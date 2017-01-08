#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.filelist import *
from arsoft.rsync import Rsync
from arsoft.sshutils import *
from arsoft.utils import rmtree, isRoot
from arsoft.socket_utils import gethostname_tuple
from arsoft.sshutils import *
from .BackupConfig import *
from .plugin import *
from .state import *
from .diskmgr import *
import sys, stat
import shlex
import traceback
    
class BackupList(object):

    class BackupItem(object):
        def __init__(self, fullpath, timestamp, session=None):
            self.fullpath = fullpath
            self.timestamp = timestamp
            self.session = session
        def __str__(self):
            return 'BackupItem(%s,%s,%s)' % (self.fullpath, self.timestamp, self.session)
    
    def __init__(self, app):
        self.app = app
        self.config = app.config
        self._items = []
        self._last_full = None

    def load(self, backup_dir, skip_failed=False, current_session=None):
        ret = True
        local_backup_dir = None
        ssh_remote_backup_dir = None
        if Rsync.is_rsync_url(backup_dir):
            url = Rsync.parse_url(backup_dir)
            if url is not None:
                if not self.config.use_ssh_for_rsync:
                    local_backup_dir = url.path
                else:
                    ssh_remote_backup_dir = url
        else:
            local_backup_dir = backup_dir
        if local_backup_dir is not None:
            if os.path.isdir(local_backup_dir):
                found_backup_dirs = []
                for item in os.listdir(local_backup_dir):
                    fullpath = os.path.join(local_backup_dir, item)
                    if os.path.isdir(fullpath):
                        (backup_ok, timestamp) = self.config.is_backup_item(item)
                        if backup_ok:
                            session = self.app.job_state.find_session(timestamp, fullpath)
                            if session is not None and session == current_session:
                                continue
                            bak = BackupList.BackupItem(fullpath, timestamp, session)

                            found_backup_dirs.append( bak )
                self._items = sorted(found_backup_dirs, key=lambda bak: bak.timestamp)
            else:
                ret = False
        elif ssh_remote_backup_dir is not None:
            #remote_items = ssh_listdir(server=ssh_remote_backup_dir.hostname, directory=ssh_remote_backup_dir.path,
                        #username=ssh_remote_backup_dir.username, password=ssh_remote_backup_dir.password,
                        #keyfile=self.config.ssh_identity_file, verbose=self.app.verbose)
            remote_items = Rsync.listdir(backup_dir,
                                         use_ssh=True, ssh_key=self.config.ssh_identity_file, verbose=self.app.verbose)
            if remote_items:
                found_backup_dirs = []
                for item, item_stat in remote_items.iteritems():
                    if stat.S_ISDIR(item_stat.st_mode):
                        fullpath = Rsync.join_url(ssh_remote_backup_dir, item)
                        (backup_ok, timestamp) = self.config.is_backup_item(item)
                        if backup_ok:
                            session = self.app.job_state.find_session(timestamp, fullpath)
                            if session is not None and session == current_session:
                                continue
                            bak = BackupList.BackupItem(fullpath, timestamp, session)
                            found_backup_dirs.append( bak )
                self._items = sorted(found_backup_dirs, key=lambda bak: bak.timestamp)
            else:
                if remote_items is None:
                    ret = False 

        # pick the latest/last backup from the list
        self._last_full = None
        if self._items:
            idx = len(self._items) - 1
            while idx >= 0:
                if self._items[idx].session is not None and not self._items[idx].session.temporary:
                    self._last_full = self._items[idx]
                    break
                idx = idx - 1
        return ret
    
    def remove_old_backups(self, max_age, min_count=0, max_count=50):

        if min_count > max_count:
            raise ValueError('min_count=%i must be greater than max_count=%i' % (min_count, max_count))

        #print('hist=%i min_count=%i max_count=%i' % (len(self._items), min_count, max_count))
        if len(self._items) > max_count:
            num_to_delete = len(self._items) - max_count
            #print('numbers to delete %i' % num_to_delete)
            for i in range(0, num_to_delete):
                self.app.session.writelog('Remove backup %s because more than %i backups found' % (self._items[0].fullpath, max_count) )
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
                self.app.session.writelog('Remove backup %s because backup exceeds retention time of %s' % (self._items[0].fullpath, max_rentention_time) )
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
        error_msg = None
        item = self._items[index]
        if Rsync.is_rsync_url(item.fullpath):
            url = Rsync.parse_url(item.fullpath)
            result = Rsync.rmdir(item.fullpath, recursive=True,
                                 use_ssh=True, ssh_key=self.config.ssh_identity_file,
                                 verbose=self.app.verbose)
        else:
            result = False
            try:
                rmtree(item.fullpath)
                result = True
            except IOError as e:
                error_msg = str(e)

        if not result:
            self.app.session.writelog('Failed to remove backup %s (Error %s)\n' % (item.fullpath, error_msg if not None else 'unknown'))
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

        @property
        def config(self):
            if self.impl:
                return self.impl.config
            else:
                return None

    class PluginLoadException(Exception):
        def __init__(self, plugin_name, exc_info):
            self.name = plugin_name
            self.exc_type, self.exc_value, self.exc_traceback = exc_info

        @property
        def exc_info(self):
            return (self.exc_type, self.exc_value, self.exc_traceback)

        def __str__(self):
            return 'PluginLoadException(%s, %s(%s) )' % (self.name, self.exc_type, self.exc_value)

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
        self.disk_mounted = False
        self._disk_obj = None
        self._real_backup_dir = None
        self._verbose = False
        self._rsync_verbose = False
        self.root_dir = None
        self.fqdn = None
        self.hostname = None

    @property
    def verbose(self):
        return self._verbose

    @property
    def config_dir(self):
        return self.config.config_dir

    @property
    def backup_dir(self):
        return self._real_backup_dir

    def cleanup(self):
        self.job_state.save()

        if self._diskmgr:
            self._diskmgr.cleanup()

    def reinitialize(self, config_dir=None, state_dir=None, root_dir=None, plugins=None):
        self.root_dir = root_dir
        self.config.open(config_dir, root_dir=root_dir)
        self.job_state.open(state_dir, root_dir=root_dir, verbose=self._verbose)

        (fqdn, hostname, domain) = gethostname_tuple()
        self.fqdn = fqdn
        self.hostname = hostname

        has_localhost_server = False
        for item in self.config.remote_servers:
            if self.is_localhost(item.hostname):
                if item.scheme != 'local':
                    sys.stderr.write('Remote server %s is configured to use scheme %s instead of local.\n' % (item.name, item.scheme))
                has_localhost_server = True

        if not has_localhost_server:
            self.config.remote_servers.append(BackupConfig.RemoteServerInstance(name='localhost', scheme='local', hostname=self.fqdn))

        # in any case continue with the config we got
        self._diskmgr = DiskManager(tag=None if not self.config.disk_tag else self.config.disk_tag, root_dir=root_dir)

        if plugins is None:
            plugins_to_load = self.config.active_plugins
        else:
            plugins_to_load = plugins

        if self._verbose:
            print('plugins to load: %s' % plugins_to_load)

        for plugin in plugins_to_load:
            try:
                self._load_plugin(plugin)
            except BackupApp.PluginLoadException as e:
                sys.stderr.write('Failed to load plugin %s: error %s\n' % (plugin, str(e)))
                (ex_type, ex_value, ex_traceback) = e.exc_info
                traceback.print_exception(ex_type, ex_value, ex_traceback)
        return True

    def _load_plugin(self, plugin_name):
        plugin_module_name = "arsoft.backup.plugins." + plugin_name
        try:
            mod = __import__(plugin_module_name)
        except Exception as e:
            (ex_type, ex_value, ex_traceback) = sys.exc_info()
            raise BackupApp.PluginLoadException(plugin_module_name, (ex_type, ex_value, ex_traceback) )

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
        
    @staticmethod
    def _mkdir(dir, perms=0700):
        ret = True
        if os.path.exists(dir):
            if not os.path.isdir(dir):
                sys.stderr.write('%s is not a directory\n' % (dir) )
                ret = False
        else:
            try:
                os.makedirs(dir)
                os.chmod(dir, perms)
            except (IOError, OSError) as e:
                sys.stderr.write('Failed to create directory %s; error %s\n' % (dir, str(e)) )
                ret = False
        return ret

    def sync_directories(self, source_dir, target_dir, recursive=True, relative=False, exclude=None, delete=True, deleteExcluded=True, perserveACL=True, preserveXAttrs=True):
        return Rsync.sync_directories(source_dir, target_dir,
                                      recursive=recursive, relative=relative,
                                      exclude=exclude, delete=delete, deleteExcluded=deleteExcluded,
                                      perserveACL=perserveACL, preserveXAttrs=preserveXAttrs,
                                      stdout=None, stderr=None, stderr_to_stdout=False, verbose=self._rsync_verbose)

    def is_localhost(self, hostname):
        if hostname == 'localhost' or hostname == 'loopback':
            return True
        elif hostname == '127.0.0.1' or hostname == '::1':
            return True
        elif hostname == self.hostname or hostname == self.fqdn:
            return True
        else:
            return False

    def _prepare_backup_dir(self):
        ret = True
        backup_dir = self._real_backup_dir
        if backup_dir is None or len(backup_dir) == 0:
            sys.stderr.write('No backup directory configured in %s\n' % (self.config.main_conf) )
            ret = False
        else:
            if not self.config.use_filesystem_snapshots:
                if self.config.use_timestamp_for_backup_dir:
                    now = datetime.datetime.utcnow()
                    nowstr = now.strftime(self.config.timestamp_format_for_backup_dir)
                    backup_dir = os.path.join(backup_dir, nowstr)

            backup_disk = None
            if Rsync.is_rsync_url(backup_dir):
                # assume the given URL is good and there's no backup disk for
                # remote backups
                self.session.backup_dir = backup_dir
                self.session.backup_disk = None
            else:
                if not BackupApp._mkdir(backup_dir):
                    self.session.writelog('Failed to create backup directory %s' % backup_dir)
                    ret = False
                else:
                    backup_disk = self._diskmgr.get_disk_for_directory(backup_dir)
            if ret:
                self.session.backup_dir = backup_dir
                self.session.backup_disk = backup_disk
                if self.config.intermediate_backup_directory:
                    if not BackupApp._mkdir(self.config.intermediate_backup_directory):
                        self.session.writelog('Failed to create intermediate backup directory %s' % self.config.intermediate_backup_directory)
                        ret = False
        return ret

    def load_previous(self):
        return self.previous_backups.load(self._real_backup_dir, current_session=self.session)

    def prepare_destination(self, create_backup_dir=False):
        if Rsync.is_rsync_url(self.config.backup_directory):
            # backup using rsync, so no disk required
            self._real_backup_dir = self.config.backup_directory
            if create_backup_dir:
                ret = self._prepare_backup_dir()
            ret = True
        else:
            # load all available external discs
            disk_ready = self._diskmgr.is_disk_ready()
            if not disk_ready:
                if not self._diskmgr.load():
                    self.session.writelog('Failed to load external discs')
                    sys.stderr.write('Failed to load external discs\n')
                    ret = 1
                else:
                    self.session.writelog('Waiting for disk for %f seconds' % self.config.disk_timeout)
                    self._disk_obj = self._diskmgr.wait_for_disk(timeout=self.config.disk_timeout)
                    if self._disk_obj:
                        self.disk_loaded = True
                        disk_ready = True
            else:
                # just get the present disk
                self._disk_obj = self._diskmgr.get_disk()

            if disk_ready:
                ret = True
                # use configure backup directory as fallback (or for disk-less backups)
                self._real_backup_dir = self.config.backup_directory
                if self._disk_obj is None:
                    # no disk required for this backup
                    pass
                else:
                    # get the mount path of the backup disk and use it as
                    # real backup directory
                    mountpath = self._diskmgr.get_disk_mountpath(self._disk_obj)
                    if mountpath:
                        self._real_backup_dir = mountpath
                        self.session.writelog('Disk already available and mount to %s' % mountpath)
                    else:
                        (result, mountpath) = self._diskmgr.disk_mount(self._disk_obj)
                        if result:
                            self.disk_mounted = True
                            self._real_backup_dir = mountpath
                            self.session.writelog('Disk mount to %s' % str(mountpath))
                            self.plugin_notify_disk_mount()
                        else:
                            self.session.writelog('Failed to mount disk')
                            ret = False
                if ret:
                    self.plugin_notify_disk_ready()
                    if create_backup_dir:
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
            self._disk_obj = self._diskmgr.update_disk(self._disk_obj)
            self.plugin_notify_disk_eject()
            if self._disk_obj:
                self.session.writelog('Ejecting backup disk %s' % str(self._disk_obj))
                if not self._diskmgr.eject(self._disk_obj):
                    self.session.writelog('Failed to eject backup disk %s' % str(self._disk_obj))
                    ret = False
                self._disk_obj = None
            else:
                self.session.writelog('Ejecting backup disk but no disk object available.')
        elif self.disk_mounted:
            self._disk_obj = self._diskmgr.update_disk(self._disk_obj)
            self.plugin_notify_disk_unmount()
            if self._disk_obj:
                self.session.writelog('Unmount backup disk %s' % str(self._disk_obj))
                if not self._diskmgr.disk_unmount(self._disk_obj):
                    self.session.writelog('Failed to unmount backup disk %s' % str(self._disk_obj))
                    ret = False
                self._disk_obj = None
            else:
                self.session.writelog('Mounted backup disk but no disk object available.')
        else:
            self.session.writelog('No backup disk loaded.')

        return ret
    
    def start_session(self, temporary=False):
        if temporary:
            self.session = self.job_state.start_temporary_session()
        else:
            self.session = self.job_state.start_new_session()
        utcnow = datetime.datetime.utcnow()
        localnow = datetime.datetime.now()
        utcOffset_minutes = int(round((localnow - utcnow).total_seconds())) / 60
        self.session.writelog('Start at %s local time (%d minutes UTC diff)' % (str(localnow), utcOffset_minutes))
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

    def create_link(self, source, link, hardlink=False, symlink=False, overwrite=True, relative_to=None, use_relative_path=True):
        if not hardlink and not symlink:
            symlink = True
        if hardlink:
            if not isRoot():
                hardlink = False
                symlink = True
        if relative_to is not None:
            actual_source = os.path.relpath(source, start=relative_to)
        elif use_relative_path and symlink:
            actual_source = os.path.relpath(source, start=os.path.dirname(link))
        else:
            actual_source = source
        remove_old_link = False
        old_link_exists = False
        try:
            link_st = os.stat(link, follow_symlinks=False)
            old_link_exists = True
            if stat.S_ISLNK(link_st.st_mode):
                target = os.readlink(link)
                if not os.path.samefile(source, target):
                    remove_old_link = True if overwrite else False
            else:
                if not os.path.samefile(source, link):
                    remove_old_link = True if overwrite else False
        except IOError:
            # ignore if it does not exist
            pass
        if old_link_exists:
            if remove_old_link:
                # remove old link
                os.unlink(link)
            else:
                raise IOError('%s already exists' % link)
        if symlink:
            os.symlink(actual_source, link)
        else:
            os.link(actual_source, link)
        return True

    def plugin_notify_start_session(self):
        self._call_plugins('start_session')

    def plugin_notify_finish_session(self, **kwargs):
        self._call_plugins('finish_session', **kwargs)

    def plugin_notify_disk_ready(self):
        self._call_plugins('disk_ready')

    def plugin_notify_disk_eject(self):
        self._call_plugins('disk_eject')

    def plugin_notify_disk_mount(self):
        self._call_plugins('disk_mount')
    def plugin_notify_disk_unmount(self):
        self._call_plugins('disk_unmount')

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

    def plugin_notify_start_manage_retention(self):
        self._call_plugins('start_manage_retention')
    def plugin_notify_manage_retention_complete(self):
        self._call_plugins('manage_retention_complete')

    class RemoteServerConnection(BackupConfig.RemoteServerInstance):
        def __init__(self, backup_app, server_item):
            BackupConfig.RemoteServerInstance.__init__(self,
                                                       name=server_item.name,
                                                       scheme=server_item.scheme,
                                                       hostname=server_item.hostname,
                                                       port=server_item.port,
                                                       username=server_item.username,
                                                       password=server_item.password,
                                                       keyfile=server_item.keyfile,
                                                       sudo_password=server_item.sudo_password)
            self._backup_app = backup_app
            self._cxn = None
            self._session_key = None
            self._sudo = None

        def __del__(self):
            self.close()

        @property
        def connection(self):
            if self._cxn is None:
                self.connect()
            return self._cxn

        @property
        def has_sudo(self):
            return True if self._sudo else False

        def connect(self):
            if self.scheme == 'ssh':
                self._cxn = SSHConnection(hostname=self.hostname, port=self.port, username=self.username, keyfile=self.keyfile, verbose=self._backup_app.verbose)
                if self.keyfile is None and self.password:
                    self._session_key = SSHSessionKey(self._cxn)

                if self.sudo_password:
                    self._sudo = SSHSudoSession(self._cxn, sudo_password=self.sudo_password)
            elif self.scheme == 'local':
                self._cxn = LocalConnection(verbose=self._backup_app.verbose)
                if self.sudo_password:
                    self._sudo = LocalSudoSession(self._cxn, sudo_password=self.sudo_password)
            return True if self._cxn else False

        def close(self):
            self._session_key = None
            self._sudo = None
            if self._cxn:
                self._cxn.close()
                self._cxn = None

    def find_remote_server_entry(self, name=None, hostname=None):
        if hostname is not None:
            hostname_for_comparison = hostname.lower()
        for item in self.config.remote_servers:
            if name is not None and item.name == name:
                return BackupApp.RemoteServerConnection(self,item)
            if hostname is not None and item.hostname.lower() == hostname_for_comparison:
                return BackupApp.RemoteServerConnection(self,item)
        return None

