#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import datetime
from arsoft.inifile import IniFile
from arsoft.timestamp import timestamp_from_datetime
from arsoft.disks.disk import Drive
from arsoft.utils import logfile_writer_proxy

class BackupStateDefaults(object):
    JOB_STATE_CONF = 'backup_job.state'
    HISTORY_FILE_PREFIX = 'backup_run_'
    HISTORY_FILE_EXTENSION = '.state'
    LOG_FILE_EXTENSION = '.log'
    TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'

class BackupJobHistoryItem(object):
    def __init__(self, parent, filename, temporary=False):
        self.parent = parent
        self.filename = filename
        (self.state_dir, basename) = os.path.split(self.filename)
        (self.basename, self.extension) = os.path.splitext(basename)
        history_date_str = self.basename[len(BackupStateDefaults.HISTORY_FILE_PREFIX):]
        self.unique_name = history_date_str
        self.date = datetime.datetime.strptime(history_date_str, BackupStateDefaults.TIMESTAMP_FORMAT)
        self.timestamp = timestamp_from_datetime(self.date)
        self.logfile = os.path.join(self.state_dir, self.basename + BackupStateDefaults.LOG_FILE_EXTENSION)
        self.temporary = temporary
        self._success = False
        self._failure_message = None
        self._startdate = None
        self._enddate = None
        self._logfile_fobj = None
        self._logfile_proxy = None
        self._require_read = True
        self._backup_dir = None
        self._backup_disk = None

    @staticmethod
    def create(parent, state_dir, temporary=False):
        now = datetime.datetime.utcnow()
        itemname = BackupStateDefaults.HISTORY_FILE_PREFIX + now.strftime(BackupStateDefaults.TIMESTAMP_FORMAT) + BackupStateDefaults.HISTORY_FILE_EXTENSION
        fullpath = os.path.join(state_dir, itemname)
        item = BackupJobHistoryItem(parent, fullpath, temporary)
        item._startdate = now
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

    @property
    def success(self):
        if self._require_read:
            self._read_state()
        return self._success

    @property
    def failure_message(self):
        if self._require_read:
            self._read_state()
        return self._failure_message

    @property
    def startdate(self):
        if self._require_read:
            self._read_state()
        return self._startdate

    @property
    def enddate(self):
        if self._require_read:
            self._read_state()
        return self._enddate

    @property
    def backup_dir(self):
        if self._require_read:
            self._read_state()
        return self._backup_dir
    @backup_dir.setter
    def backup_dir(self, value):
        self._backup_dir = value

    @property
    def fullpath(self):
        return self.backup_dir

    @property
    def backup_disk(self):
        if self._require_read:
            self._read_state()
        return self._backup_disk
    @backup_disk.setter
    def backup_disk(self, value):
        if value is None:
            self._backup_disk = value
        elif isinstance(value, Drive):
            self._backup_disk = value.match_pattern
        elif isinstance(value, str):
            self._backup_disk = value
        else:
            raise ValueError("invalid value for backup_disk %s" % value)

    def _read_state(self):
        if self.temporary:
            ret = True
        else:
            inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
            ret = inifile.open(self.filename)
            self._success = inifile.getAsBoolean(None, 'Success', False)
            self._failure_message = inifile.get(None, 'FailureMessage', None)
            self._startdate = inifile.getAsTimestamp(None, 'Start', None)
            self._enddate = inifile.getAsTimestamp(None, 'End', None)
            self._backup_dir = inifile.get(None, 'BackupDir', None)
            self._backup_disk = inifile.get(None, 'BackupDisc', None)
            self._require_read = False
        return ret

    def _write_state(self):
        if self.temporary:
            ret = True
        else:
            inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
            # read existing file
            inifile.open(self.filename)
            inifile.setAsBoolean(None, 'Success', self._success)
            inifile.set(None, 'FailureMessage', self._failure_message)
            inifile.setAsTimestamp(None, 'Start', self._startdate)
            inifile.setAsTimestamp(None, 'End', self._enddate)
            inifile.set(None, 'BackupDir', self._backup_dir)
            inifile.set(None, 'BackupDisc', self._backup_disk)
            ret = inifile.save(self.filename)
            if ret:
                self.parent._item_changed(self)
                self._require_read = False
        return ret

    def closelog(self):
        if self._logfile_fobj is not None:
            self._logfile_fobj.close()

    def openlog(self):
        if self._logfile_fobj is None:
            try:
                self._logfile_fobj = open(self.logfile, 'w')
            except IOError as e:
                self._logfile_fobj = None
            if self._logfile_fobj:
                self._logfile_proxy = logfile_writer_proxy(self._logfile_fobj)
        return self._logfile_proxy

    def writelog(self, *args):
        proxy = self.openlog()
        if proxy:
            proxy.write(*args)

    @property
    def logfile_proxy(self):
        return self._logfile_proxy

    def finish(self, success=True, failure_message=None):
        self._success = success
        self._failure_message = failure_message
        self.closelog()
        now = datetime.datetime.utcnow()
        self._enddate = now
        self._write_state()

    def __str__(self):
        return str(self.date)

class BackupJobHistory(object):
    def __init__(self, job_state, state_dir):
        self.job_state = job_state
        self.state_dir = state_dir
        self._items = None

    def load(self):
        if self._items is None:
            tmp_items = []
            if os.path.isdir(self.state_dir):
                for itemname in os.listdir(self.state_dir):
                    fullpath = os.path.join(self.state_dir, itemname)
                    #print('found %s' % fullpath)
                    if BackupJobHistoryItem.is_history_item(fullpath):
                        item = BackupJobHistoryItem(self, fullpath)
                        tmp_items.append(item)
            self._items = sorted(tmp_items, key=lambda item: item.timestamp)

    def save(self):
        for item in self._items:
            item.save()

    def create_new_item(self):
        self.load()
        item = BackupJobHistoryItem.create(self, self.state_dir)
        self._items.append(item)
        return item

    def create_temporary_item(self):
        item = BackupJobHistoryItem.create(self, '/tmp', True)
        return item
    
    @property
    def is_loaded(self):
        return True if self._items is not None else False

    def reload(self):
        self._items = None
        self.load()

    def _item_changed(self, item):
        self.job_state._item_changed(item)

    def __iter__(self):
        return iter(self._items)
    
    def __len__(self):
        return len(self._items)
    
    def __getitem__(self, index):
        return self._items[index]

    def __delitem__(self, index):
        item = self._items[index]
        os.unlink(item.filename)
        del self._items[index]

    def __str__(self):
        self.load()
        return '[' + ','.join([str(item) for item in self._items]) + ']'

class BackupJobState(object):
    def __init__(self, state_dir=None, root_dir=None):
        self.root_dir = root_dir
        self.state_dir = state_dir
        if state_dir:
            self.job_state_conf = os.path.join(state_dir, BackupStateDefaults.JOB_STATE_CONF)
        else:
            self.job_state_conf = None
        self.history = BackupJobHistory(self, state_dir)
        self.clear()
        self._dirty = False

    def clear(self):
        self.oldest_entry = None
        self.last_success = None
        self.last_failure = None

    def open(self, state_dir=None, root_dir=None):
        self.root_dir = root_dir
        if state_dir is None:
            state_dir = self.state_dir
        else:
            if self.root_dir is not None:
                state_dir = self.root_dir + state_dir
            self.job_state_conf = os.path.join(state_dir, BackupStateDefaults.JOB_STATE_CONF)
            self.history = BackupJobHistory(self, state_dir)
            self.state_dir = state_dir

        if not os.path.isfile(self.job_state_conf):
            save_state_file = True
        else:
            save_state_file = False

        ret = self._read_state_conf(self.job_state_conf)
        if save_state_file:
            ret = self._write_state_conf(self.job_state_conf)

        self.history.load()
        self._dirty = False
        return ret
    
    def _mkdir(self, dir):
        ret = True
        if os.path.exists(dir):
            if not os.path.isdir(dir):
                sys.stderr.write('%s is not a directory\n' % (dir) )
                ret = False
        else:
            try:
                os.makedirs(dir)
            except (IOError, OSError) as e:
                sys.stderr.write('Failed to create directory %s; error %s\n' % (dir, str(e)) )
                ret = False
        return ret

    def save(self, state_dir=None):
        if state_dir is None:
            state_dir = self.state_dir
        else:
            if state_dir != self.state_dir:
                self.job_state_conf = os.path.join(state_dir, BackupStateDefaults.JOB_STATE_CONF)
                self.state_dir = state_dir
                self._dirty = True

        if self._dirty:
            if not os.path.isdir(state_dir):
                ret = self._mkdir(state_dir)
            else:
                ret = True
            if ret:
                self.history = BackupJobHistory(self, state_dir)

                ret = self._write_state_conf(self.job_state_conf)
        else:
            # nothing to do
            ret = True
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
        ret = self.history.create_new_item()
        if ret:
            self._dirty = True
        return ret

    def start_temporary_session(self):
        return self.history.create_temporary_item()

    def remove_old_items(self, max_age, min_count=0, max_count=50):
        
        if not self.history.is_loaded:
            self.history.reload()

        if min_count > max_count:
            raise ValueError('min_count=%i must be greater than max_count=%i' % (min_count, max_count))
        
        #print('hist=%i min_count=%i max_count=%i' % (len(self.history), min_count, max_count))
        if len(self.history) > max_count:
            num_to_delete = len(self.history) - max_count
            #print('numbers to delete %i' % num_to_delete)
            for i in range(0, num_to_delete):
                #print('delete num %i=%s' % (i, self.history[0]))
                del self.history[0]
                self._dirty = True

        if isinstance(max_age, datetime.datetime):
            max_rentention_time = max_age
        elif isinstance(max_age, datetime.timedelta):
            now = datetime.datetime.utcnow()
            max_rentention_time = now - max_age
        elif isinstance(max_age, float) or isinstance(max_age, int):
            now = datetime.datetime.utcnow()
            max_rentention_time = now - datetime.timedelta(seconds=max_age)

        while len(self.history) > 0 and len(self.history) <= min_count:
            if self.history[0].date < max_rentention_time:
                #print('remove old item %s' % (self.history[i]))
                del self.history[0]
                self._dirty = True
            else:
                break

        return True

    def find_session(self, timestamp, backup_dir=None, backup_disk=None):
        for item in self.history:
            if item.date == timestamp:
                if backup_dir is not None:
                    if item.backup_dir != backup_dir:
                        continue

                if backup_disk is not None:
                    if item.backup_disk != backup_disk:
                        continue
                return item
        return None
    
    def _item_changed(self, item):
        if item.success:
            if self.last_success is None or item.date > self.last_success:
                self.last_success = item.date
        else:
            if self.last_failure is None or item.date > self.last_failure:
                self.last_failure = item.date
        self.save()

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

