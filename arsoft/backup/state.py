#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import datetime
from arsoft.inifile import IniFile
from arsoft.timestamp import timestamp_from_datetime

class BackupStateDefaults(object):
    JOB_STATE_CONF = 'backup_job.state'
    HISTORY_FILE_PREFIX = 'backup_run_'
    HISTORY_FILE_EXTENSION = '.state'
    LOG_FILE_EXTENSION = '.log'
    TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'

class BackupJobHistoryItem(object):
    def __init__(self, filename):
        self.filename = filename
        (self.state_dir, basename) = os.path.split(self.filename)
        (self.basename, self.extension) = os.path.splitext(basename)
        history_date_str = self.basename[len(BackupStateDefaults.HISTORY_FILE_PREFIX):]
        self.date = datetime.datetime.strptime(history_date_str, BackupStateDefaults.TIMESTAMP_FORMAT)
        self.timestamp = timestamp_from_datetime(self.date)
        self.logfile = os.path.join(self.state_dir, self.basename + BackupStateDefaults.LOG_FILE_EXTENSION)
        self.success = False
        self.failure_message = None
        self.startdate = None
        self.enddate = None
        self.logfile_fobj = None

    @staticmethod
    def create(state_dir):
        now = datetime.datetime.utcnow()
        itemname = BackupStateDefaults.HISTORY_FILE_PREFIX + now.strftime(BackupStateDefaults.TIMESTAMP_FORMAT) + BackupStateDefaults.HISTORY_FILE_EXTENSION
        fullpath = os.path.join(state_dir, itemname)
        item = BackupJobHistoryItem(fullpath)
        item._write_state()
        return item

    @staticmethod
    def is_history_item(filename):
        (basename, extension) = os.path.splitext(os.path.basename(filename))
        if basename.startswith(BackupStateDefaults.HISTORY_FILE_PREFIX) and extension.lower() == BackupStateDefaults.HISTORY_FILE_EXTENSION:
            ret = True
        else:
            ret = False
        return ret

    def _read_state(self):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        ret = inifile.open(self.filename)
        self.success = inifile.getAsBoolean(None, 'Success', False)
        self.failure_message = inifile.get(None, 'FailureMessage', None)
        self.startdate = inifile.getAsTimestamp(None, 'Start', None)
        self.enddate = inifile.getAsTimestamp(None, 'End', None)
        return ret

    def _write_state(self):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        # read existing file
        inifile.open(self.filename)
        inifile.setAsBoolean(None, 'Success', self.success)
        inifile.set(None, 'FailureMessage', self.failure_message)
        inifile.setAsTimestamp(None, 'Start', self.startdate)
        inifile.setAsTimestamp(None, 'End', self.enddate)
        ret = inifile.save(self.filename)
        return ret

    def closelog(self):
        if self.logfile_fobj is not None:
            self.logfile_fobj.close()

    def openlog(self):
        if self.logfile_fobj is None:
            if os.path.isfile(self.logfile):
                self.logfile_fobj = open(self.logfile, 'w')
            else:
                self.logfile_fobj = None
        return self.logfile_fobj

    def finish(self):
        self.closelog()
        now = datetime.datetime.utcnow()
        self.enddate = now
        self._write_state()

    def __str__(self):
        return str(self.date)

class BackupJobHistory(object):
    def __init__(self, state_dir):
        self.state_dir = state_dir
        self._items = None

    def load(self):
        if self._items is None:
            tmp_items = []
            for itemname in os.listdir(self.state_dir):
                fullpath = os.path.join(self.state_dir, itemname)
                print('found %s' % fullpath)
                if BackupJobHistoryItem.is_history_item(fullpath):
                    item = BackupJobHistoryItem(fullpath)
                    tmp_items.append(item)
            self._items = sorted(tmp_items, key=lambda item: item.timestamp)

    def save(self):
        for item in self._items:
            item.save()

    def create_new_item(self):
        self.load()
        item = BackupJobHistoryItem.create(self.state_dir)
        self._items.append(item)
        return item

    def reload(self):
        self._items = None
        self.load()

    def __str__(self):
        self.load()
        return '[' + ','.join([str(item) for item in self._items]) + ']'

class BackupJobState(object):
    def __init__(self, state_dir=None):
        self.state_dir = state_dir
        if state_dir:
            self.job_state_conf = os.path.join(state_dir, BackupStateDefaults.JOB_STATE_CONF)
        else:
            self.job_state_conf = None
        self.history = BackupJobHistory(state_dir)
        self.clear()

    def clear(self):
        self.last_success = None
        self.last_failure = None

    def open(self, state_dir=None):
        if state_dir is None:
            state_dir = self.state_dir
        else:
            self.job_state_conf = os.path.join(state_dir, BackupStateDefaults.JOB_STATE_CONF)
            self.history = BackupJobHistory(state_dir)
            self.state_dir = state_dir

        if not os.path.isfile(self.job_state_conf):
            save_state_file = True
        else:
            save_state_file = False

        ret = self._read_state_conf(self.job_state_conf)
        if save_state_file:
            ret = self._write_state_conf(self.job_state_conf)

        self.history.load()

        return ret

    def save(self, state_dir=None):
        if state_dir is None:
            state_dir = self.state_dir
        else:
            self.job_state_conf = os.path.join(state_dir, BackupStateDefaults.JOB_STATE_CONF)
            self.state_dir = state_dir
            self.history = BackupJobHistory(state_dir)

        ret = self._write_state_conf(self.job_state_conf)
        return ret

    def _read_state_conf(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        ret = inifile.open(filename)
        self.last_success = inifile.getAsTimestamp(None, 'LastSuccess', None)
        self.last_failure = inifile.getAsTimestamp(None, 'LastFailure', None)
        return ret
        
    def _write_state_conf(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        # read existing file
        inifile.open(filename)
        # and modify it according to current config
        inifile.setAsTimestamp(None, 'LastSuccess', self.last_success)
        inifile.setAsTimestamp(None, 'LastFailure', self.last_failure)

        ret = inifile.save(filename)
        return ret
    
    def start_new_session(self):
        return self.history.create_new_item()

    def __str__(self):
        ret = ''
        ret = ret + 'last_success: ' + str(self.last_success) + '\n'
        ret = ret + 'last_failure: ' + str(self.last_failure) + '\n'
        ret = ret + 'history: ' + str(self.history) + '\n'
        return ret

if __name__ == "__main__":
    import sys
    s = BackupJobState(sys.argv[1])
    s.open()
    print(s)
    
    s.start_new_session()
    
    s.last_failure = datetime.datetime.now()
    s.save()
    print(s)

