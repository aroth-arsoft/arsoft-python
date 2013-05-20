#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import sys
import os.path
from daemon import runner, pidlockfile
import signal
from arsoft.utils import get_main_script_filename, to_gid, to_uid

# version of this script
__version__  = '1.0'

class arsoft_daemon_runner(runner.DaemonRunner):
    def __init__(self, app):
        """ Set up the parameters of a new runner.

            The `app` argument must have the following attributes:

            * `stdin_path`, `stdout_path`, `stderr_path`: Filesystem
              paths to open and replace the existing `sys.stdin`,
              `sys.stdout`, `sys.stderr`.

            * `pidfile_path`: Absolute filesystem path to a file that
              will be used as the PID file for the daemon. If
              ``None``, no PID file will be used.

            * `pidfile_timeout`: Used as the default acquisition
              timeout value supplied to the runner's PID lock file.

            * `run`: Callable that will be invoked when the daemon is
              started.
            
            """
        super(arsoft_daemon_runner, self).__init__(app)
        self.progname = os.path.basename(get_main_script_filename())
        self.daemon_context.signal_map = {
            signal.SIGTERM: self.signal_terminate,
            signal.SIGHUP: self.signal_reload
            }
        if hasattr(app, 'daemon_user'):
            self.daemon_context.uid = to_uid(app.daemon_user)
        if hasattr(app, 'daemon_group'):
            self.daemon_context.gid = to_gid(app.daemon_group)

        #This ensures that the logger file handle does not get closed during daemonization
        self.daemon_context.files_preserve=app.files_preserve
        

    def signal_terminate(self, signal_number, stack_frame):
        self.app.terminate()

    def signal_reload(self, signal_number, stack_frame):
        self.app.reload()

    def _usage_exit(self, argv):
        """ Emit a usage message, then exit.
            """
        usage_exit_code = 2
        action_usage = "|".join(self.action_funcs.keys())
        message = "usage: %(progname)s %(action_usage)s" % (self.progname, action_usage)
        runner.emit_message(message)
        sys.exit(usage_exit_code)

    def parse_args(self, argv=None):
        """ Parse command-line arguments.
            """
        # ignore all arguments because this should be done by the user
        return

    def _terminate_daemon_process(self, wait=True):
        """ Terminate the daemon process specified in the current PID file.
            """

        pid = self.pidfile.read_pid()
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as exc:
            raise DaemonRunnerStopFailureError(
                "Failed to terminate %(pid)d: %(exc)s" % vars())
        while wait:
            try:
                os.kill(pid, 0)
            except OSError as ex:
                if ex.errno == errno.ESRCH:
                    break
            time.sleep(0.25)

    def _start(self):
        """ Open the daemon context and run the application.
            """
        """ Open the daemon context and run the application.
            """
        print('_start')
        if runner.is_pidfile_stale(self.pidfile):
            self.pidfile.break_lock()

        print('before fork')
        try:
            self.daemon_context.open()
        except pidlockfile.AlreadyLocked:
            pidfile_path = self.pidfile.path
            print('failed fork')
            runner.emit_message('%s is already running' % (self.progname))
            return
        print('after fork')
        pid = os.getpid()
        message = self.start_message % vars()
        runner.emit_message(message)

        self.app.run()
        self.app.terminate()

    def _stop(self):
        """ Exit the daemon process specified in the current PID file.
            """
        if not self.pidfile.is_locked():
            pidfile_path = self.pidfile.path
            runner.emit_message('%s is not running' % self.progname)
            return

        if runner.is_pidfile_stale(self.pidfile):
            self.pidfile.break_lock()
        else:
            self._terminate_daemon_process(wait=True)

    def _status(self):
        (running, pid) = pidfile_status(self.pidfile)
        if running:
            runner.emit_message('%s is running (PID %i)' % (self.progname, pid))
        else:
            runner.emit_message('%s is not running' % (self.progname))

    action_funcs = {
        'start': _start,
        'stop': _stop,
        'restart': runner.DaemonRunner._restart,
        'status': _status
        }

def pidfile_status(pidfile):
    """ Determine the status of the process specified in the a PID file.

        Return tuple of (running as bool, process id)

        """
    result = (False, -1)

    pidfile_pid = pidfile.read_pid()
    if pidfile_pid is not None:
        try:
            os.kill(pidfile_pid, signal.SIG_DFL)
            result = (True, pidfile_pid)
        except OSError, exc:
            if exc.errno == errno.ESRCH:
                # The specified PID does not exist
                result = (False, pidfile_pid)
    else:
        result = (False, -1)

    return result 
