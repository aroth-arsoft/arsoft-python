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
    TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'
    
class BackupJobHistoryItem(object):
    def __init__(self, filename):
        self.filename = filename
        (self.basename, self.extension) = os.path.splitext(os.path.basename(self.filename))
        history_date_str = self.basename[len(BackupStateDefaults.HISTORY_FILE_PREFIX):]
        self.date = datetime.datetime.strptime(history_date_str, BackupStateDefaults.TIMESTAMP_FORMAT)
        self.timestamp = timestamp_from_datetime(self.date)
        self.enddate = None

    @staticmethod
    def create(state_dir):
        now = datetime.datetime.utcnow()
        itemname = BackupStateDefaults.HISTORY_FILE_PREFIX + now.strftime(BackupStateDefaults.TIMESTAMP_FORMAT)
        fullpath = os.path.join(state_dir, itemname)
        item = BackupJobHistoryItem(fullpath)
        return item

    def finish(self):
        now = datetime.datetime.utcnow()
        self.enddate = now

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
                if itemname.startswith(BackupStateDefaults.HISTORY_FILE_PREFIX):
                    fullpath = os.path.join(self.state_dir, itemname)
                    item = BackupJobHistoryItem(fullpath)
                    tmp_items.append(item)
            self._items = sorted(tmp_items, key=lambda item: item.timestamp)
            
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

