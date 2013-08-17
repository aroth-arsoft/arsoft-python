#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from ..plugin import *
from ..FileList import *

from arsoft.git.repo import *
from arsoft.git.bundle import GitBundle
from arsoft.git.error import *

class GitBackupPluginConfig(BackupPluginConfig):
    def __init__(self, parent):
        BackupPluginConfig.__init__(self, parent, 'git')
        self._repository_list = None
        self._repositories_config = None

    @property
    def repository_list(self):
        return self._repository_list

    @repository_list.setter
    def repository_list(self, value):
        if value is not None:
            if isinstance(value, FileList):
                self._repository_list = value
            else:
                self._repository_list = FileList.from_list(value)
        else:
            self._repository_list = None

    def _read_conf(self, inifile):
        self.repository_list = inifile.getAsArray(None, 'Repositories', [])
        return True
    
    def _write_conf(self, inifile):
        #filelist_path = os.path.join(config_dir, BackupConfigDefaults.REPOSITORY_LIST)
        #if self._repository_list:
            #self._repository_list.save(filelist_path)
        if self._repository_list:
            inifile.set(None, 'Repositories', self._repository_list.items)
        else:
            inifile.set(None, 'Repositories', [])
        return True

class GitBackupPlugin(BackupPlugin):
    def __init__(self, backup_app):
        self.config = GitBackupPluginConfig(backup_app)
        BackupPlugin.__init__(self, backup_app, 'git')

    def _git_backup_to_bundle(self, repository, bundle_file):
        ret = False
        if GitBundle.is_bundle(bundle_file):
            bundle = GitBundle(bundle_file, repository=repository, verbose=self.backup_app._verbose)
            try:
                ret = bundle.update()
                if ret:
                    if self.backup_app._verbose:
                        print('backup %s to %s - Updated' % (repository.root_directory, bundle.filename))
                else:
                    sys.stderr.write('backup %s to %s - Failed\n' % (repository.root_directory, bundle.filename))
            except (GitRepositoryError, GitBundleError) as e:
                sys.stderr.write('Failed to update bundle from repository %s; error %s\n' % (repository.root_directory, str(e)))
        else:
            try:
                bundle = repository.create_bundle(bundle_file, all=True)
                if self._verbose:
                    print('backup %s to %s - Created' % (repository.root_directory, bundle.filename))
                ret = True
            except (GitRepositoryError, GitBundleError) as e:
                sys.stderr.write('Failed to create bundle from repository %s; error %s\n' % (repository.root_directory, str(e)))
        return ret

    def perform_backup(self, **kwargs):
        ret = True
        backup_dir = self.config.intermediate_backup_directory
        if not self._mkdir(backup_dir):
            ret = False
        if ret:
            repo_backup_filelist = FileListItem(base_directory=self.config.base_directory)
            for repo_path in self.config.repository_list:
                repo = GitRepository(repo_path, verbose=self.backup_app._verbose)
                if repo:
                    if repo.valid:
                        bundle_file = os.path.join(backup_dir, repo.name + '.git_bundle')
                        if self.backup_app._verbose:
                            print('backup %s to %s' % (repo_path, bundle_file))
                        if not self._git_backup_to_bundle(repo, bundle_file):
                            ret = False
                        else:
                            repo_backup_filelist.append(bundle_file)
                    else:
                        sys.stderr.write('Repository %s is invalid\n' % repo_path)
                        ret = False
                else:
                    sys.stderr.write('Failed to load repository %s\n' % repo_path)
                    ret = False
            #print(repo_backup_filelist)
            self.backup_app.append_intermediate_filelist(repo_backup_filelist)
            #print(self.intermediate_filelist)
        return ret
 
