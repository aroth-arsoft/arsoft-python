#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.filelist import *
from arsoft.rsync import Rsync
from arsoft.sshutils import *
from arsoft.utils import rmtree
from .BackupConfig import *
from .plugin import *
from .state import *
from .diskmgr import *
import sys, stat

    
class BackupList(object):

    class BackupItem(object):
        def __init__(self, fullpath, timestamp, session=None):
            self.fullpath = fullpath
            self.timestamp = timestamp
            self.session = session
    
    def __init__(self, app):
        self.app = app
        self.config = app.config
        self._items = []
        self._last_full = None

    def load(self):
        ret = True
        local_backup_dir = None
        ssh_remote_backup_dir = None
        if Rsync.is_rsync_url(self.config.backup_directory):
            url = Rsync.parse_url(self.config.backup_directory)
            if url is not None:
                if not self.config.use_ssh_for_rsync:
                    local_backup_dir = url.path
                else:
                    ssh_remote_backup_dir = url
        else:
            local_backup_dir = None
        if local_backup_dir is not None:
            if os.path.isdir(local_backup_dir):
                found_backup_dirs = []
                for item in os.listdir(local_backup_dir):
                    fullpath = os.path.join(local_backup_dir, item)
                    if os.path.isdir(fullpath):
                        (backup_ok, timestamp) = self.config.is_backup_item(item)
                        if backup_ok:
                            session = self.app.job_state.find_session(timestamp, fullpath)
                            bak = BackupList.BackupItem(fullpath, timestamp, session)
                            found_backup_dirs.append( bak )
                self._items = sorted(found_backup_dirs, key=lambda bak: bak.timestamp)
            else:
                ret = False
        elif ssh_remote_backup_dir is not None:
            remote_items = ssh_listdir(server=ssh_remote_backup_dir.hostname, directory=ssh_remote_backup_dir.path,
                        username=ssh_remote_backup_dir.username, password=ssh_remote_backup_dir.password, 
                        keyfile=self.config.ssh_identity_file)
            if remote_items:
                found_backup_dirs = []
                for item, item_stat in remote_items.iteritems():
                    if stat.S_ISDIR(item_stat.st_mode):
                        fullpath = Rsync.join_url(ssh_remote_backup_dir, item)
                        (backup_ok, timestamp) = self.config.is_backup_item(item)
                        if backup_ok:
                            session = self.app.job_state.find_session(timestamp, fullpath)
                            bak = BackupList.BackupItem(fullpath, timestamp, session)
                            found_backup_dirs.append( bak )
                self._items = sorted(found_backup_dirs, key=lambda bak: bak.timestamp)
            else:
                if remote_items is None:
                    ret = False 

        # pick the latest/last backup from the list
        self._last_full = self._items[-1] if self._items else None
        return ret
    
    def remove_old_backups(self, max_age, min_count=0, max_count=50):

        if min_count > max_count:
            raise ValueError('min_count=%i must be greater than max_count=%i' % (min_count, max_count))

        #print('hist=%i min_count=%i max_count=%i' % (len(self._items), min_count, max_count))
        if len(self._items) > max_count:
            num_to_delete = len(self._items) - max_count
            #print('numbers to delete %i' % num_to_delete)
            for i in range(0, num_to_delete):
                #print('delete num %i=%s' % (i, self._items[0]))
                self.__delitem__(0)

        if isinstance(max_age, datetime.datetime):
            max_rentention_time = max_age
        elif isinstance(max_age, datetime.timedelta):
            now = datetime.datetime.utcnow()
            max_rentention_time = now - max_age
        elif isinstance(max_age, float) or isinstance(max_age, int):
            now = datetime.datetime.utcnow()
            max_rentention_time = now - datetime.timedelta(seconds=max_age)

        while len(self._items) > 0 and len(self._items) <= min_count:
            if self._items[0].timestamp < max_rentention_time:
                #print('remove old item %s' % (self._items[i]))
                self.__delitem__(0)
            else:
                break
        return True

    def __iter__(self):
        return iter(self._items)
    
    def __len__(self):
        return len(self._items)
    
    def __getitem__(self, index):
        return self._items[index]

    def __delitem__(self, index):
        #print('delitem %i' % index)
        item = self._items[index]
        if Rsync.is_rsync_url(item.fullpath):
            url = Rsync.parse_url(item.fullpath)
            ssh_rmdir(server=url.hostname, directory=url.path, recursive=True,
                        username=url.username, password=url.password,
                        keyfile=self.config.ssh_identity_file)
        else:
            rmtree(item.fullpath)
        del self._items[index]

    @property
    def last_full_backup(self):
        return self._last_full

    def __str__(self):
        self.load()
        return '[' + ','.join([str(item) for item in self._items]) + ']'

class BackupApp(object):
    
    class LoadedPlugin(object):
        def __init__(self, plugin_name, plugin_module, plugin_impl):
            self.name = plugin_name
            self.module = plugin_module
            self.impl = plugin_impl
    
    def __init__(self, name=None):
        self.name = name
        self.filelist_include = FileList()
        self.filelist_exclude = FileList()
        self.config = BackupConfig()
        self.job_state = BackupJobState()
        self.previous_backups = BackupList(self)
        self.plugins = []
        self._diskmgr = None
        self.disk_loaded = False

    def cleanup(self):
        self.job_state.save()

        if self._diskmgr:
            self._diskmgr.cleanup()

    def reinitialize(self, configdir=None, statedir=None):
        self.config.open(configdir)
        self.job_state.open(statedir)

        # in any case continue with the config we got
        self._diskmgr = DiskManager()

        plugins_to_load = self.config.active_plugins
        for plugin in plugins_to_load:
            if not self._load_plugin(plugin):
                sys.stderr.write('Failed to load plugin %s\n' % plugin)
        return True

    def _load_plugin(self, plugin_name):
        plugin_module_name = "arsoft.backup.plugins." + plugin_name
        try:
            mod = __import__(plugin_module_name)
        except Exception as e:
            print(e)
            mod = None

        subclasses=[]
        if mod:
            #walk the dictionaries to get to the last one
            d=mod.__dict__
            for m in plugin_module_name.split('.')[1:]:
                d=d[m].__dict__
            for (key, entry) in d.iteritems():
                if key.startswith('_') or key == BackupPlugin.__name__:
                    continue

                try:
                    if issubclass(entry, BackupPlugin):
                        subclasses.append(entry)
                except TypeError:
                    #this happens when a non-type is passed in to issubclass. We
                    #don't care as it can't be a subclass of Job if it isn't a
                    #type
                    continue
        
        ret = False
        for subclass in subclasses:
            inst = subclass(self)
            plugin = BackupApp.LoadedPlugin(plugin_name, mod, inst)
            self.plugins.append(plugin)
            ret = True
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

    def _prepare_backup_dir(self):
        ret = True
        backup_dir = self.config.backup_directory
        if backup_dir is None or len(backup_dir) == 0:
            sys.stderr.write('No backup directory configured in %s\n' % (self.config.main_conf) )
            ret = False
        else:
            if not self.config.use_filesystem_snapshots:
                if self.config.use_timestamp_for_backup_dir:
                    now = datetime.datetime.utcnow()
                    nowstr = now.strftime(self.config.timestamp_format_for_backup_dir)
                    backup_dir = os.path.join(backup_dir, nowstr)

            if Rsync.is_rsync_url(backup_dir):
                # assume the given URL is good
                pass
            else:
                if not self._mkdir(backup_dir):
                    ret = False
            if ret:
                self.session.backup_dir = backup_dir
                if self.config.intermediate_backup_directory:
                    if not self._mkdir(self.config.intermediate_backup_directory):
                        ret = False
        return ret

    def load_previous(self):
        return self.previous_backups.load()

    def prepare_destination(self):
        # load all available external discs
        if not self._diskmgr.is_disk_ready():
            if not self._diskmgr.load():
                sys.stderr.write('Failed to load external discs\n')
                ret = 1
            else:
                self.plugin_notify_disk_ready()
                disk_loaded = True
                disk_ready = True
        else:
            disk_ready = True

        if disk_ready:
            ret = self._prepare_backup_dir()
        else:
            ret = False
        return ret
    
    def manage_retention(self):
        self.previous_backups.remove_old_backups(max_age=self.config.retention_time, 
                                        min_count=self.config.retention_count,
                                        max_count=self.config.retention_count)
        self.job_state.remove_old_items(max_age=self.config.retention_time, 
                                        min_count=self.config.retention_count,
                                        max_count=self.config.retention_count)

    def shutdown_destination(self):
        ret = True
        if self.disk_loaded:
            self.plugin_notify_disk_eject()

            if not self._diskmgr.eject():
                ret = False
        return ret
    
    def start_session(self):
        self.session = self.job_state.start_new_session()
        self.session.writelog('Start')
        self.plugin_notify_start_session()

    def finish_session(self, success=True, failure_message=None):
        self.plugin_notify_finish_session(success=success, failure_message=failure_message)
        if success:
            self.session.writelog('Finish successfully')
        else:
            self.session.writelog('Finish with error %s' % failure_message)
        self.session.finish(success, failure_message)

    def _call_plugins(self, cmd, **kwargs):
        for plugin in self.plugins:
            if hasattr(plugin.impl, cmd):
                func = getattr(plugin.impl, cmd)
                if func:
                    func(**kwargs)

    def append_to_filelist(self, filelist_item, exclude=False):
        if exclude:
            self.filelist_exclude.append(filelist_item)
        else:
            self.filelist_include.append(filelist_item)

    def plugin_notify_start_session(self):
        self._call_plugins('start_session')

    def plugin_notify_finish_session(self, **kwargs):
        self._call_plugins('finish_session', **kwargs)

    def plugin_notify_disk_ready(self):
        self._call_plugins('disk_ready')

    def plugin_notify_disk_eject(self):
        self._call_plugins('disk_eject')

    def plugin_notify_start_rsync(self):
        self._call_plugins('start_rsync')

    def plugin_notify_rsync_complete(self):
        self._call_plugins('rsync_complete')

    def plugin_notify_start_backup(self):
        self._call_plugins('start_backup')
    def plugin_notify_perform_backup(self):
        self._call_plugins('perform_backup')
    def plugin_notify_backup_complete(self):
        self._call_plugins('backup_complete')
