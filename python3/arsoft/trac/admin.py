#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.utils import runcmdAndGetData
import sys, os

class TracAdmin(object):
    def __init__(self, tracenv, trac_admin_bin='trac-admin', verbose=False):
        self._tracenv = tracenv
        self._trac_admin_bin = trac_admin_bin
        self._last_error = None
        self._verbose = verbose
        self._trac_config = None
        self._plugin_info = None
        self._repository_manager = None
        self._db_repository_provider = None
        self._env = None

    def reinitialize(self):
        self._last_error = None
        self._trac_config = None
        self._plugin_info = None
        self._repository_manager = None
        self._db_repository_provider = None
        self._env = None

    @property
    def last_error(self):
        return self._last_error

    @property
    def verbose(self):
        return self._verbose

    @property
    def valid(self):
        self._init_env()
        return True if self._env else False

    def _run_trac_admin(self, args):
        self._last_error = None
        cmd_args = [self._tracenv]
        cmd_args.extend(args)
        (sts, stdoutdata, stderrdata) = runcmdAndGetData(self._trac_admin_bin, cmd_args, verbose=self._verbose)
        self._last_error = stderrdata
        if sts == 0:
            return True
        else:
            return False

    def initenv(self, project_name, database, repository_path=None, repository_type='svn'):
        # 'mysql://' + dbuser + ':' + dbpassword + '@' + self._mysql_server + '/' + dbname
        args = ['initenv', project_name, database]
        if repository_path is not None:
            args.append(repository_type)
            args.append(repository_path)
        return self._run_trac_admin(args)

    def upgrade(self, backup=True):
        if not self._check_config_access(read_only=False):
            return False
        args = ['upgrade']
        if backup == False:
            args.append('--no-backup')
        return self._run_trac_admin(args)

    def hotcopy(self, dest_dir, include_database=True):
        if not self._check_config_access(read_only=True):
            return False
        args = ['hotcopy']
        args.append(dest_dir)
        if not include_database:
            args.append('--no-database')
        #if os.path.exists(dest_dir):
        #    raise FileExistsError(dest_dir)
        return self._run_trac_admin(args)

    def _init_env(self):
        if self._env is None:
            from trac.core import TracError
            try:
                from trac.env import Environment
                self._env = Environment(self._tracenv)
            except TracError as e:
                self._env = None
                self._last_error = str(e)
            except IOError as e:
                self._env = None
                self._last_error = str(e)

    def _check_config_access(self, read_only=True):
        ret = True
        if self._tracenv:
            trac_ini = os.path.join(self._tracenv, 'conf', 'trac.ini')
            if read_only:
                if not os.access(trac_ini, os.R_OK):
                    self._last_error = str(PermissionError('Unable to read %s.' % trac_ini))
                    ret = False
            else:
                if not os.access(trac_ini, os.W_OK):
                    self._last_error = str(PermissionError('Unable to write %s.' % trac_ini))
                    ret = False
        return ret

    def _retrieve_plugin_info(self):
        if self._plugin_info is None:
            self._init_env()
            try:
                from trac.loader import get_plugin_info, get_plugins_dir
                self._plugin_info = get_plugin_info(self._env)
            except:
                self._plugin_info = []
                
    def _retrieve_repository_manager(self):
        if self._repository_manager is None:
            self._init_env()
            try:
                from trac.versioncontrol import RepositoryManager
                self._repository_manager = RepositoryManager(self._env)
            except:
                self._repository_manager = []

    def _retrieve_db_repository_provider(self):
        if self._db_repository_provider is None:
            self._init_env()
            try:
                from trac.versioncontrol import DbRepositoryProvider
                self._db_repository_provider = DbRepositoryProvider(self._env)
            except:
                self._db_repository_provider = []

    @property
    def plugins(self):
        self._retrieve_plugin_info()
        ret = []
        for p in self._plugin_info:
            ret.append(p['name'])
        return ret
    
    def get_plugin_info(self, plugin):
        self._retrieve_plugin_info()
        for p in self._plugin_info:
            if p['name'] == plugin:
                return p
        return None
        
    def get_plugin_components(self, plugin):
        self._retrieve_plugin_info()
        for p in self._plugin_info:
            if p['name'] == plugin:
                ret = []
                for (name, m) in list(p['modules'].items()):
                    for (compname, compdetails) in list(m['components'].items()):
                        ret.append(compdetails['full_name'])
                return ret
        return None
        
    @property
    def configured_components(self):
        self._init_env()
        ret = []
        if self._env:
            for (k, v) in self._env.config.options('components'):
                ret.append( (k,v) )
        return ret
        
    def set_configured_components(self, components):
        self._init_env()
        if self._env:
            for (k, v) in self._env.config.options('components'):
                self._env.config.remove('components', k)
            for (k, v) in components:
                self._env.config.set('components', k, v)

    @property
    def database(self):
        self._init_env()
        if self._env:
            return self._env.config.get('trac', 'database', None)
        else:
            return None

    def set_database(self, database):
        self._init_env()
        if self._env:
            return self._env.config.set('trac', 'database', database)
        else:
            return None

    @property
    def database_type(self):
        db = self.database
        if db:
            return db.split(':')[0]
        else:
            return None

    @property
    def database_file(self):
        db = self.database
        if db:
            elem = db.split(':')
            if elem[0] == 'sqlite':
                return os.path.join(self._tracenv, elem[1])
            else:
                return None
        else:
            return None

    @property
    def repositories(self):
        ret = []
        self._retrieve_db_repository_provider()
        if self._db_repository_provider:
            ret = self._db_repository_provider.get_repositories()
        return ret
    
    @property
    def supported_repository_types(self):
        self._retrieve_repository_manager()
        ret = []
        if self._repository_manager:
            ret = self._repository_manager.get_supported_types()
        return ret

    def get_repository(self, reponame):
        self._retrieve_repository_manager()
        if self._repository_manager:
            return self._repository_manager.get_repository(reponame)
        else:
            return None

    def sync_repository(self, reponame, rev_callback=None, clean=False):
        ret = False
        self._retrieve_repository_manager()
        if self._repository_manager:
            from trac.core import TracError
            try:
                repo = self._repository_manager.get_repository(reponame)
                if repo:
                    repo.sync(rev_callback=rev_callback, clean=clean)
                    ret = True
                else:
                    ret = False
            except TracError as e:
                self._last_error = str(e)
        return ret

    def add_repository(self, reponame, path, repotype):
        ret = False
        self._retrieve_db_repository_provider()
        if self._db_repository_provider:
            from trac.core import TracError
            try:
                self._db_repository_provider.add_repository(reponame, path, repotype)
                ret = True
            except TracError as e:
                self._last_error = str(e)
        return ret

    def remove_repository(self, reponame):
        ret = False
        self._retrieve_db_repository_provider()
        if self._db_repository_provider:
            from trac.core import TracError
            try:
                self._db_repository_provider.remove_repository(reponame)
                ret = True
            except TracError as e:
                self._last_error = str(e)
        return ret

    def modify_repository(self, reponame, changes):
        ret = False
        self._retrieve_db_repository_provider()
        if self._db_repository_provider:
            from trac.core import TracError
            try:
                self._db_repository_provider.modify_repository(reponame, changes)
                ret = True
            except TracError as e:
                self._last_error = str(e)
        return ret
    
    def add_repository_alias(self, reponame, target):
        ret = False
        self._retrieve_db_repository_provider()
        if self._db_repository_provider:
            from trac.core import TracError
            try:
                self._db_repository_provider.add_alias(reponame, target)
                ret = True
            except TracError as e:
                self._last_error = str(e)
        return ret

    def set_logging(self, logfile='trac.log', level='DEBUG', logtype='file'):
        self._init_env()
        self._env.config.set('logging', 'log_file', logfile)
        self._env.config.set('logging', 'log_level', level)
        self._env.config.set('logging', 'log_type', logtype)

    def enable_component(self, component):
        self._init_env()
        self._env.enable_component(component)
        self._env.config.set('components', component, 'enabled')
        
    def disable_component(self, component):
        self._init_env()
        self._env.config.set('components', component, 'disabled')

    def enable_plugin(self, plugin):
        plugin_components = self.get_plugin_components(plugin)
        if plugin_components is not None:
            for comp in plugin_components:
                if self._verbose:
                    print('enable ' + comp)
                self._env.enable_component(comp)
                self._env.config.set('components', comp, 'enabled')
            ret = True
        else:
            ret = False
        return ret

    def save_config(self):
        """Try to save the config, and display either a success notice or a
        failure warning.
        """
        self._last_error = None
        try:
            if self._env:
                self._env.config.save()
            ret = True
        except Exception as e:
            self._last_error = 'Error writing to trac.ini: ' + exception_to_unicode(e)
            ret = False
        return ret
    
    @property
    def config_filename(self):
        return os.path.join(self._tracenv, 'conf/trac.ini')

if __name__ == '__main__':
    t = TracAdmin(tracenv=sys.argv[1])
    print(t.plugins)
    print(t.get_plugin_info('AdvancedTicketWorkflowPlugin'))
    print(t.get_plugin_components('AdvancedTicketWorkflowPlugin'))
    for repo in t.repositories:
        repo_dir = repo.params['dir']
        repo_type = repo.params['type'] if 'type' in repo.params else 'svn'
        repo_name = '(default)' if not repo.name else repo.name
        print(repo_type + ': ' + repo_name + ' ' + repo_dir)
 
