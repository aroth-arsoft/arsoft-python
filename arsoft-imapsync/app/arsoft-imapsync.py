#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os, sys
import argparse
from arsoft_offlineimap import OfflineImap

class ARSoftImapSync(object):

    def __init__(self):
        self._verbose = False
        self._script_name = os.path.basename(__file__)
        self._offline_imap = None
        self._root_dir = None
        self._cache_dir = None


    def main(self, argv=None):

        #=============================================================================================
        # process command line
        #=============================================================================================
        parser = argparse.ArgumentParser(description='sync mail between imap servers')
        parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='enable verbose output of this script.')
        parser.add_argument('--write-config', dest='write_config', action='store_true', help='only write the configuration for offlineimap and exit.')
        parser.add_argument('-R', '--root-directory', dest='root_dir', default='/', help='specifies the root directory for operations.')
        parser.add_argument('-C', '--config-directory', dest='config_dir', default='/etc/arsoft/imapsync', help='name of the directory containing the imap sync configuration.')
        parser.add_argument('--cache-directory', dest='cache_dir', default='/var/tmp/arsoft-imapsync', help='name of the directory containing the imap sync cache data.')
        parser.add_argument('--offlineimap', dest='offlineimap_exe', help='use specified offlineimap tool')

        args = parser.parse_args()

        ret = 0
        self._verbose = args.verbose
        self._root_dir = args.root_dir
        self._cache_dir = args.cache_dir

        if self._root_dir is not None and self._root_dir != '/':
            config_dir = os.path.normpath(self._root_dir + args.config_dir)
            cache_dir = os.path.normpath(self._root_dir + self._cache_dir)
        else:
            config_dir = os.path.normpath(args.config_dir)
            cache_dir = os.path.normpath(self._cache_dir)
        account_file = os.path.join(config_dir, 'accounts')
        private_dir = os.path.join(cache_dir, 'account-data')

        if self._verbose:
            print('Config directory: %s' % config_dir)
            print('Accounts file: %s' % account_file)
            print('Accounts data directory: %s' % private_dir)

        if not os.path.isdir(cache_dir):
            try:
                os.mkdir(cache_dir)
            except OSError:
                sys.stderr.write('Unable to create cache directory %s.\n' % (cache_dir))
                ret = 1

        if not os.path.isdir(private_dir):
            try:
                os.mkdir(private_dir)
            except OSError:
                sys.stderr.write('Unable to create private directory %s.\n' % (private_dir))
                ret = 1
        if ret != 0:
            return ret

        self._offline_imap = OfflineImap(private_dir=private_dir, offlineimap_exe=args.offlineimap_exe, verbose=self._verbose)
        if not self._offline_imap.is_installed:
            sys.stderr.write('Unable to find offlineimap executable. Please install offlineimap.\n')
            ret = 1
        else:
            if self._verbose:
                print('Offlineimap: %s' % self._offline_imap.offlineimap_exe)
                print('Logfile: %s' % self._offline_imap.logfile)
            if not self._offline_imap.readConfig(account_file):
                sys.stderr.write('Failed to read account configuration from %s\n' % account_file)
            if self._verbose:
                if self._offline_imap.account_list is not None:
                    print('Accounts:')
                    for acc in self._offline_imap.account_list:
                        print('  %s' % acc)
            if args.write_config:
                files = self._offline_imap.write_config()
                if files is None:
                    sys.stderr.write('Failed to generate configuration for accounts.\n')
                else:
                    for f in files:
                        print(f)
            else:
                results = self._offline_imap.run(per_account_log=True)
                for (account, ok, logfile) in results:
                    if not ok:
                        sys.stderr.write('Failed to sync account %s; logfile %s\n' % (account.name, logfile) )
                        ret = 1
        return ret

if __name__ == "__main__":
    app = ARSoftImapSync()
    sys.exit(app.main(sys.argv))
