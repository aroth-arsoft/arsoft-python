#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import sys
import yaml
from arsoft.utils import which
from .repo import *

def find_git_commit_notifier_executable():
    return which('git-commit-notifier', only_first=True)

GIT_COMMIT_NOTIFIER_EXECUTABLE = find_git_commit_notifier_executable()

class GitCommitNotifierConfig(object):

    def __init__(self, repository=None, configfile=None):
        object.__setattr__(self, '_data', {})
        object.__setattr__(self, '_last_error', None)

        if configfile is None:
            if repository is not None:
                object.__setattr__(self, '_configfile', os.path.join(repository.magic_directory, 'git-commit-notifier.yml'))
            else:
                object.__setattr__(self, '_configfile', None)
        else:
            object.__setattr__(self, '_configfile', configfile)

        do_reset = True
        if self._configfile:
            do_reset = True if not self.open() else False
        if do_reset:
            self.reset()

    def clear(self):
        self._data = []
        self._last_error = None

    def open(self, filename=None):
        if filename is None:
            filename = self._configfile

        try:
            f = open(filename, 'r')
            object.__setattr__(self, '_data', yaml.load(f))
            f.close()
            ret = True
        except IOError as e:
            object.__setattr__(self, '_last_error', str(e))
            ret = False

        return ret

    def save(self, filename=None):
        if filename is None:
            filename = self._configfile

        try:
            f = open(filename, 'w')
            f.write(yaml.dump(self._data))
            f.close()
            ret = True
        except IOError as e:
            object.__setattr__(self, '_last_error', str(e))
            ret = False
        return ret

    def reset(self):
        data = {}
        data['ignore_merge'] = False
        data['emailprefix'] = None
        data['lines_per_diff'] = 250
        data['too_many_files'] = 50
        data['show_summary'] = True
        data['mailinglist'] = ''
        data['from'] = ''
        data['delivery_method'] = 'sendmail'
        data['sendmail_options'] = { 'location': '/usr/sbin/sendmail', 'arguments': '-i -t' }
        data['message_integration'] = ''
        data['unique_commits_per_branch'] = False
        data['show_master_branch_name'] = False
        data['ignore_whitespace'] = True
        data['reply_to_author'] = False
        data['prefer_git_config_mailinglist'] = False
        data['send_mail_to_committer'] = False
        data['message_map'] = {}
        object.__setattr__(self, '_data', data)

    _CUSTOM_PROPS = ['email_recipients', 'email_sender', 'email_prefix', 'last_error']

    @property
    def last_error(self):
        return self._last_error

    @property
    def email_prefix(self):
        return self._data['emailprefix']

    @email_prefix.setter
    def email_prefix(self, value):
        self._data['emailprefix'] = value

    @property
    def email_sender(self):
        return self._data['from']

    @email_sender.setter
    def email_sender(self, value):
        self._data['from'] = value

    @property
    def email_recipients(self):
        return self._data['mailinglist'].split(',')

    @email_recipients.setter
    def email_recipients(self, value):
        if isinstance(value, list):
            self._data['mailinglist'] = ','.join(value)
        else:
            self._data['mailinglist'] = value

    @property
    def message_map(self):
        return self._data['message_map']
    
    def enable_trac(self, trac_url, repo_name=None, keywords=['refs','ref','close','closes','implements','fixes','fixed']):
        for (regex, url) in self._data['message_map'].items():
            if trac_url in url:
                del self._data['message_map'][regex]
                break

        regex = '\\b(' + '|'.join(keywords) + ')\\s*\\#(\\d+)'
        ticket_url = trac_url + '/ticket/\\2'
        changeset_url = trac_url + '/changeset'

        self._data['message_map'][regex] = ticket_url
        if repo_name is None:
            self._data['trac'] = { 'path': changeset_url }
        else:
            self._data['trac'] = { 'path': changeset_url, 'repository':repo_name  }
        self._data['link_files'] = 'trac'

    def enable_gitweb(self, gitweb_url, project=None):
        self._data['gitweb'] = { 'path': gitweb_url, 'project':project  }
        self._data['link_files'] = 'gitweb'

    def __str__(self):
        return str(self._data)

    def __getattr__(self, name):
        if name in self._CUSTOM_PROPS:
            return object.__getattribute__(self, name)
        else:
            return self._data[name]

    def __setattr__(self, name, value):
        if name in self._CUSTOM_PROPS:
            return object.__setattr__(self, name, value)
        else:
            self._data[name] = value

if __name__ == '__main__':

    repo = GitRepository(sys.argv[1])
    notify_config = GitCommitNotifierConfig(repo)

    print(notify_config)
    print('email_sender: %s' % (str(notify_config.email_sender)))
    print('email_recipients: %s' % (str(notify_config.email_recipients)))
    print('show_master_branch_name: %s' % (str(notify_config.show_master_branch_name)))
    print('message_map: %s' % (str(notify_config.message_map)))
    
    notify_config.email_recipients = 'me@you'
    print('email_recipients: %s' % (str(notify_config.email_recipients)))

    notify_config.enable_trac('http://local')
    print('message_map: %s' % (str(notify_config.message_map)))
    print('trac: %s' % (str(notify_config.trac)))
