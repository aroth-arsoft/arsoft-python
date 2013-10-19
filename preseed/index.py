#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
# vim: set ts=4 sw=4 tw=0 smarttab et

from arsoft.netconfig import *
from logging import debug, info, exception, error, warning, handlers
import logging
import os
from urlparse import urlunparse
from mod_python import apache
from mod_python import util


class ProxyLogThing:
    """A proxy for default Apache logging."""

    def __init__(self):
        # No need to do anything.
        None

    def log_error(self, msg, lvl):
        apache.log_error(msg, lvl)

class ApacheLogHandler(logging.Handler):
    """A handler class which sends all logging to Apache."""

    def __init__(self, ref = None):
        """
        Initialize the handler (does nothing)
        """
        logging.Handler.__init__(self)

        if ref == None:
            self.ref = ProxyLogThing()
        else:
            self.ref = ref
        # Set up the thing
        # Set up the thing
        self.level_mapping = { logging.CRITICAL: apache.APLOG_CRIT,
                               logging.ERROR: apache.APLOG_ERR,
                               logging.WARNING: apache.APLOG_WARNING,
                               logging.INFO: apache.APLOG_INFO,
                               logging.debug: apache.APLOG_DEBUG }

    def emit(self, record):
        """Emit a record."""
        self.ref.log_error(record.msg, 1)

class http_preseed(object):
    m_netconfig = None
    m_environ = {}
    m_req = None
    m_node = None
    m_distro = None
    m_plugin = None
    m_script = None

    def __init__(self, netconfig=None):
        if netconfig != None:
            self.m_netconfig = netconfig
        else:
            self.m_netconfig = Netconfig()
        self.m_netconfig.addEnvironment(self.m_environ)
        
    def _init(self, req):
        self.m_req = req
        data = util.FieldStorage(req)
        node = data.get('node', None)
        distro = data.get('distro', None)
        plugin = data.get('plugin', None)
        self.m_script = data.get('script', None)
        if distro is not None:
            self.m_distro = self.m_netconfig.getPreseed(distro)
        if node is not None:
            self.m_node = self.m_netconfig.getNode(name=node)

    def _get_script_url(self, type):
        (scheme, hostinfo, user, password, hostname, port, path, query, fragment) = self.m_req.parsed_uri
        
        $script_url = 'http://' . $_SERVER['SERVER_NAME'] .  $_SERVER['SCRIPT_NAME'] . '?v=0';

        if type is not None:
            if len(query) > 0:
                query += "&"
            query += "script=" + type + "&arch=" + self.m_node.arch;

        url = [scheme, hostname + ':' + str(port), path, None, query, fragment ]
        
        return urlunparse(url)

 
    def get_script_cmdline(self, type):
        url = self.get_script_url(type)
        ret = "if [ -f /var/lib/preseed/log -a -d /target ]; then echo \"Preseed environment detected\"; DEST=/target/tmp/preseed_" + type + ".sh; SH=\"chroot /target /bin/sh\"; else echo \"Non-Preseed environment detected\"; DEST=/tmp/preseed_" + type + ".sh; SH=\"/bin/sh\"; fi; arch=`uname -m`; wget -q -O \$DEST \"{$url}\"; \$SH /tmp/preseed_" + type + ".sh";
        return ret
        
    def _output(self):
        req = self.m_req
        req.content_type = "text/plain"
        req.write("#\n"")
        req.write("# Preseed installer for machine " + node.dn + "\n")
        req.write("#\n\n")
        req.write("#\n")
        req.write("# Initialize Plugins\n")
        req.write("#\n\n")
        req.write("distro=" + str(distro) + "\r\n")
        req.write("node=" + str(node) + "\r\n")
        if self.m_script is None:
            req.write("d-i preseed/early_command string " + self._get_script_cmdline('early') + "\r\n")
            req.write("# This command is run just before the install finishes, but when there is\r\n")
            req.write("# still a usable /target directory.\r\n")
            req.write("d-i preseed/late_command string " + self._get_script_cmdline('late') + "\r\n")
            req.write("#\n")
            req.write("# Perform preseed\n")
            req.write("#\n\n")
        else:
            script_cmdline = self._get_script_cmdline(self.m_script)
            script_function_download = """download_file() {
URL="$1"
DEST="$2"
if [ ! -z "$URL" -a ! -z \"$DEST" ]; then\n
    wget -q -O $DEST "$URL" 2>&1\n
    RES=\$?\n
else\n
    RES=1\n
fi\n
return \$RES\n
"""

	if($output_script == 'early')
	{
		print "#\n";
		print "# Generate early script\n";
		print "# manual execute:\n";
		print "# $script_cmdline\n";

		print "# helper functions\n";
		print $script_function_download;
	
		print "#\n\n";
		print "echo \"Running early script\"\n";
		print "#\n\n";
		foreach($plugins as $plugin)
		{
			$plugin->ScriptEarly();
		}
		print "#\n\n";
		print "echo \"Finished early script\"\n";
		print "#\n\n";
	}
	else if($output_script == 'late')
	{
		print "#\n";
		print "# Generate late script\n";
		print "# manual execute:\n";
		print "# $script_cmdline\n";

		print "# helper functions\n";
		print $script_function_download;

		print "#\n\n";
		print "echo \"Running late script\"\n";
		print "#\n\n";

		foreach($plugins as $plugin)
		{
			$plugin->ScriptLate();
		}
		print "#\n\n";
		print "echo \"Finished late script\"\n";
		print "#\n\n";
	}
}          
    def process(self, req):
        self._init(req)
        self._output()
        return apache.OK


def initLog(req):
    root = logging.getLogger('')
    # allow each log channel to decide which msg to keep and which to ignore
    root.setLevel(logging.DEBUG)
    #log:changes every days, 3 files max
    try:
        flog=handlers.TimedRotatingFileHandler('/tmp/http_preseed.log', "d", 1, 3)
        flog.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s\t%(process)d\t%(threadName)s\t%(levelname)s\t%(message)s",
            datefmt="%Y-%m-%d_%H:%M:%S",
        )
        flog.setFormatter(formatter)
        root.addHandler(flog)
    except IOError, e:
        pass
    #log:changes every days, 3 files max
    try:
        slog=ApacheLogHandler()
        slog.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s\t%(process)d\t%(threadName)s\t%(levelname)s\t%(message)s",
            datefmt="%Y-%m-%d_%H:%M:%S",
        )
        slog.setFormatter(formatter)
        root.addHandler(slog)
    except IOError, e:
        pass
    
    

def handler(req):
    initLog(req)
    debug('hello')
    app = http_preseed()
    return app.process(req)
