#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from ..plugin import *
from arsoft.filelist import *

from arsoft.git.repo import *
from arsoft.git.bundle import GitBundle
from arsoft.git.error import *

class GitBackupPluginConfig(BackupPluginConfig):
    def __init__(self, parent):
        BackupPluginConfig.__init__(self, parent, 'git')
        self._repository_list = None

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

    def __str__(self):
        ret = BackupPluginConfig.__str__(self)
        if self._repository_list:
            ret = ret + 'repositories: ' + ','.join(self._repository_list.items) + '\n'
        else:
            ret = ret + 'repositories: []\n'
        return ret

class GitBackupPlugin(BackupPlugin):
    def __init__(self, backup_app):
        self.config = GitBackupPluginConfig(backup_app)
        BackupPlugin.__init__(self, backup_app, 'git')

    def _git_backup_to_bundle(self, repository, bundle_file):
        ret = False
        if self.backup_app._verbose:
            print('git backup %s to %s' % (repository.root_directory, bundle_file))

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
                if self.backup_app._verbose:
                    print('backup %s to %s - Created' % (repository.root_directory, bundle.filename))
                ret = True
            except (GitRepositoryError, GitBundleError) as e:
                sys.stderr.write('Failed to create bundle from repository %s; error %s\n' % (repository.root_directory, str(e)))
        return ret

    @staticmethod
    def is_remote_repository(repo_url):
        idx = repo_url.find('://')
        ret = True if idx > 0 else False
        return ret

    def update_remote_repo(self, local_path, remote_url):
        ret = True
        if os.path.isdir(local_path):
            repo = GitRepository(local_path, bare=True, verbose=self.backup_app._verbose)
            # only update the origin remote (which should be always the case)
            (sts, stdoutdata, stderrdata) = repo.fetch(remote='origin', quiet=True, recursive=True, outputStdErr=True, outputStdOut=True)
            if sts != 0:
                sys.stderr.write('Failed to pull latest from %s to %s\n' % (remote_url, local_path))
                ret = False
        else:
            if self.backup_app._verbose:
                print('git clone %s to %s' % (remote_url, local_path))
            repo = GitRepository(local_path, bare=True, verbose=self.backup_app._verbose)
            (sts, stdoutdata, stderrdata) = repo.clone(remote_url, local_path, recursive=True)
            if sts != 0:
                sys.stderr.write('Failed to clone %s to %s\n' % (remote_url, local_path))
                ret = False
        return ret

    def perform_backup(self, **kwargs):
        ret = True
        backup_dir = self.config.intermediate_backup_directory
        if not self._mkdir(backup_dir):
            ret = False
        if ret:
            repo_backup_filelist = FileListItem(base_directory=self.config.base_directory)
            for repo_path in self.config.repository_list:
                if GitBackupPlugin.is_remote_repository(repo_path):
                    local_repo_name = GitRepository.suggested_name(repo_path)
                    local_repo_path = os.path.join(backup_dir, local_repo_name + '.git')
                    if self.update_remote_repo(local_repo_path, repo_path):
                        repo_path = local_repo_path
                    else:
                        repo_path = None
                repo = GitRepository(repo_path, verbose=self.backup_app._verbose) if repo_path else None
                if repo:
                    if repo.valid:
                        if repo.empty:
                            sys.stderr.write('Repository %s is empty. Skip\n' % repo_path)
                            ret = False
                        else:
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
            self.backup_app.append_to_filelist(repo_backup_filelist)
            #print(self.intermediate_filelist)
        return ret
 
