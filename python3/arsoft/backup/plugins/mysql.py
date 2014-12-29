#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from ..plugin import *
from arsoft.filelist import *
from arsoft.utils import which

import subprocess
import sys
import tempfile
import hashlib

(python_major, python_minor, python_micro, python_releaselevel, python_serial) = sys.version_info

def mysqldump(exe, zip_exe, checksum_exe, dumpfile, checksum_file, socket=None, hostname=None, port=None, username=None, password=None, database=None, compress=True, verbose=False):
    sts = -1
    stdoutdata = None
    stderrdata = None
    with tempfile.NamedTemporaryFile() as defaults_file:
        all_args = [exe]
        all_args.append('--defaults-file=%s' % defaults_file.name)
        all_args.append('--opt')
        all_args.append('--skip-dump-date')
        if hostname:
            all_args.append('--host=%s' % hostname)
        elif socket:
            all_args.append('--socket=%s' % socket)
        if port:
            all_args.append('--port=%s' % port)
        if username:
            all_args.append('--user=%s' % username)
        if compress:
            all_args.append('--compress')
        # database(s) must be the last argument
        if database:
            if isinstance(database, list):
                all_args.append('--databases')
                for d in database:
                    all_args.append('"%s"' % d)
            else:
                all_args.append('"%s"' % database)
        else:
            all_args.append('--all-databases')

        if password:
            defaults_file.write(('[mysqldump]\npassword=%s\n' % password).encode())
            defaults_file.flush()
            defaults_file.seek(0)

        all_args.extend(['|', zip_exe ])
        all_args.extend(['|', 'tee', dumpfile ])
        all_args.extend(['|', checksum_exe ])

        if verbose:
            print("mysqldump " + ' '.join(all_args))

        f_checksum = open(checksum_file, 'w')
        p = subprocess.Popen(' '.join(all_args), stdout=f_checksum, stderr=subprocess.PIPE, stdin=None, shell=True)
        if p:
            (stdoutdata, stderrdata) = p.communicate()
            sts = p.returncode
        f_checksum.close()
    return sts, stdoutdata, stderrdata

def read_checksum_file(filename):
    ret = None
    try:
        with open(filename, 'r') as content_file:
            first_line = content_file.readline()
            if first_line and ' ' in first_line:
                (digest, digest_name) = first_line.split(' ', 1)
                ret = digest
    except IOError:
        pass
    return ret

class MysqlBackupPluginConfig(BackupPluginConfig):

    class DatabaseItem(object):
        def __init__(self, database, socket=None, hostname='localhost', port=3306, username='root', password=''):
            self.database = database
            self.socket = socket
            self.hostname = hostname
            self.port = port
            self.username = username
            self.password = password

        def __str__(self):
            if self.socket is not None:
                return '%s (%s:***@%s)' % (self.database, self.username, self.socket)
            else:
                return '%s (%s:***@%s:%i)' % (self.database, self.username, self.hostname, self.port)

    def __init__(self, parent):
        BackupPluginConfig.__init__(self, parent, 'mysql')
        self._database_list = []

    @property
    def database_list(self):
        return self._database_list

    @database_list.setter
    def database_list(self, value):
        self._database_list = value

    def _read_conf(self, inifile):
        for sect in inifile.sections:
            db_name = inifile.get(sect, 'database', None)
            db_host = inifile.get(sect, 'host', None)
            db_port = inifile.getAsInteger(sect, 'port', 3306)
            db_socket = inifile.get(sect, 'socket', None)
            db_user = inifile.get(sect, 'username', None)
            db_pass = inifile.get(sect, 'password', None)
            if db_name:
                self._database_list.append(MysqlBackupPluginConfig.DatabaseItem(db_name, socket=db_socket,
                                                                                hostname=db_host, port=db_port,
                                                                                username=db_user, password=db_pass))
        return True
    
    def _write_conf(self, inifile):
        return True

    def __str__(self):
        ret = BackupPluginConfig.__str__(self)
        ret = ret + 'databases:\n'
        if self._database_list:
            for item in self._database_list:
                ret = ret + '  %s:\n' % item.database
                if item.socket is not None:
                    ret = ret + '    socket: %s:%i\n' % (item.socket)
                else:
                    ret = ret + '    server: %s:%i\n' % (item.hostname, item.port)
                ret = ret + '    username: %s\n' % item.username
                ret = ret + '    password: %s\n' % item.password
        return ret

class MysqlBackupPlugin(BackupPlugin):
    def __init__(self, backup_app):
        self.config = MysqlBackupPluginConfig(backup_app)
        BackupPlugin.__init__(self, backup_app, 'mysql')
        self.mysqldump_exe = which('mysqldump', only_first=True)
        self.zip_exe = which('bzip2', only_first=True)
        self.checksum_exe = which('md5sum', only_first=True)

    def perform_backup(self, **kwargs):
        ret = True
        backup_dir = self.config.intermediate_backup_directory
        if not self._mkdir(backup_dir):
            ret = False
        if not self.mysqldump_exe:
            sys.stderr.write('mysqldump not found.\n')
            ret = False
        if ret:
            mysql_backup_filelist = FileListItem(base_directory=self.config.base_directory)
            for database_item in self.config.database_list:
                if self.backup_app._verbose:
                    print('backup %s' % str(database_item))
                db_dumpfile = os.path.join(backup_dir, database_item.database + '.mysql.bz2')
                db_checksumfile = db_dumpfile + '.md5'

                db_dumpfile_tmp = db_dumpfile + '.tmp'
                db_checksumfile_tmp = db_dumpfile_tmp + '.md5'

                sts, stdoutdata, stderrdata = mysqldump(self.mysqldump_exe, self.zip_exe, self.checksum_exe,
                                db_dumpfile_tmp, db_checksumfile_tmp,
                                database=database_item.database,
                                socket=database_item.socket,
                                hostname=database_item.hostname, port=database_item.port,
                                username=database_item.username, password=database_item.password,
                                verbose=self.backup_app._verbose)
                if sts != 0:
                    sys.stderr.write('Dump of database %s failed. %s\n' % (str(database_item), stderrdata))
                    ret = False
                else:
                    checksum = read_checksum_file(db_checksumfile)
                    checksum_tmp = read_checksum_file(db_checksumfile_tmp)

                    if checksum == checksum_tmp:
                        os.remove(db_dumpfile_tmp)
                        os.remove(db_checksumfile_tmp)
                    else:
                        os.rename(db_dumpfile_tmp, db_dumpfile)
                        os.rename(db_checksumfile_tmp, db_checksumfile)

                    mysql_backup_filelist.append(db_dumpfile)
                    mysql_backup_filelist.append(db_checksumfile)

            #print(mysql_backup_filelist)
            self.backup_app.append_to_filelist(mysql_backup_filelist)
            #print(self.intermediate_filelist)
        return ret
 
