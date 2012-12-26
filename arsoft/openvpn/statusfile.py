#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

""" This is a parser for openvpn status files, version 3.

How to use:

- add "status-version 3" to openvpn server configuration. Reload/restart openvpn server.
- locate openvpn status file. Usually it's under /var/run in Unix based systems.
- Run "python openvpn-status-parser.py <filename>" for demo. Sample file with random data
  is included in the repository, try it with "python openvpn-status-parser.py".

MIT License:

Copyright (C) 2012, Olli Jarva <olli.jarva@futurice.com>

Permission is hereby granted, free of charge, to any person obtaining a 
copy of this software and associated documentation files (the 
"Software"), to deal in the Software without restriction, including 
without limitation the rights to use, copy, modify, merge, publish, 
distribute, sublicense, and/or sell copies of the Software, and to 
permit persons to whom the Software is furnished to do so, subject to 
the following conditions:

The above copyright notice and this permission notice shall be included 
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY 
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 

"""

import pprint
import csv
import datetime
import logging
import sys
import os
import configfile
import management

class StatusBase(object):
    def __init__(self, version=2):
        self._connected_clients = None
        self._routing_table = None
        self._details = None
        self._statistics = None
        
    def _parse_lines(self, lines):
        self._details = {}
        self._connected_clients = {}
        self._routing_table = {}
        
        if self._version == 2:
            delimiter = ','
        elif self._version == 3:
            delimiter = '\t'
        else:
            delimiter = ','

        read_statistics = False
        topics_for = {}
        csvreader = csv.reader(lines, delimiter=delimiter)
        for row in csvreader:
            row_title = row[0]

                if row_title == "END":
                    if read_statistics:
                        if 'Updated' in self._statistics:
                            try:
                                self._details["timestamp"] = datetime.datetime.strptime(self._statistics['Updated'], '%a %b %d %H:%M:%S %Y')
                            except (IndexError, ValueError):
                                logging.error("Updated time is invalid: %s" % self._statistics['Updated'])
                    return True
                else:
                    if read_statistics == False:
                        if row_title == "TITLE":
                            try:
                                self._details["title"] = row[1]
                            except IndexError:
                                logging.error("TITLE row is invalid: %s" % row)

                        elif row_title == "TIME":
                            try:
                                self._details["timestamp"] = datetime.datetime.fromtimestamp(int(row[2]))
                            except (IndexError, ValueError):
                                logging.error("TIME row is invalid: %s" % row)

                        elif row_title == "HEADER":
                            try:
                                topics_for[row[1]] = row[2:]
                            except IndexError:
                                logging.error("HEADER row is invalid: %s" % row)

                        elif row_title == "CLIENT_LIST":
                            try:
                                self._connected_clients[row[1]] = dict(zip(topics_for["CLIENT_LIST"], row[1:]))
                                self._connected_clients[row[1]]["connected_since"] = datetime.datetime.fromtimestamp(int(row[-1]))
                            except IndexError:
                                logging.error("CLIENT_LIST row is invalid: %s" % row)

                        elif row_title == "ROUTING_TABLE":
                            try:
                                self._routing_table[row[2]] = dict(zip(topics_for["ROUTING_TABLE"], row[1:]))
                                self._routing_table[row[2]]["last_ref"] = datetime.datetime.fromtimestamp(int(row[-1]))
                            except IndexError:
                                logging.error("ROUTING_TABLE row is invalid: %s" % row)

                        elif row_title == "GLOBAL_STATS":
                            try:
                                self._details[row[1]] = row[2]
                            except IndexError:
                                logging.error("GLOBAL_STATS row is invalid: %s" % row)

                        elif row_title == "OpenVPN STATISTICS":
                            read_statistics = True
                            self._statistics = {}

                        else:
                            logging.warning("Line was not parsed. Keyword %s not recognized. %s" % (row_title, row))
                    else:
                        try:
                            self._statistics[row[0]] = row[1]
                        except IndexError:
                            logging.error("statistics row is invalid: %s" % row)

            logging.error("File was incomplete. END line was missing.")
            return False
        else:
            return False

    @property
    def details(self):
        """ Returns miscellaneous details from status file """
        if not self._details:
            self._parse_file()
        return self._details

    @property
    def last_update(self):
        """ Returns the time of the last update of the status file """
        if not self._details:
            self._parse_file()
        return self._details['timestamp']

    @property
    def connected_clients(self):
        """ Returns dictionary of connected clients with details."""
        if not self._connected_clients:
            self._parse_file()
        return self._connected_clients

    @property
    def routing_table(self):
        """ Returns dictionary of routing_table used by OpenVPN """
        if not self._routing_table:
            self._parse_file()
        return self._routing_table

    @property
    def statistics(self):
        """ Returns dictionary of statistics used by OpenVPN """
        if not self._statistics:
            self._parse_file()
        return self._statistics

class StatusFile(StatusBase):
    def __init__(self, filename=None, version=2, config_name=None, config_file=None):
        StatusBase.__init__(self, version=version)
        self.filename = filename
        self._is_socket = False

        if filename is None:
            if config_name is not None:
                cfgfile = configfile.ConfigFile(config_name=config_name)
                self.filename = cfgfile.management_socket
                if self.filename is None:
                    self.filename = cfgfile.status_file
                    self._version = cfgfile.status_version
                else:
                    self._is_socket = True
                    self._version = 3
            elif config_file is not None:
                self.filename = config_file.management_socket
                if self.filename is None:
                    self.filename = config_file.status_file
                    self._version = config_file.status_version
                else:
                    self._is_socket = True
                    self._version = 3
            else:
                self.filename = None
        else:
            self.filename = filename

        self._parse_file()

    def _parse_file(self):
        ret = False
        if self._is_socket:
            miface = management.ManagementInterface(self.filename)
            if miface.open():
                lines = miface.status()
                ret = self._parse_lines(lines)
                miface.close()
            else:
                ret = False
        else:
            try:
                file = open(self.filename)
            except IOError:
                file = None

            if file is not None:
                lines = file.readlines()
                file.close()
                ret = self._parse_lines(lines)
            else:
                ret = False
        return ret

if __name__ == '__main__':
    files = sys.argv[1:]

    for file in files:
        if os.path.isfile(file):
            parser = StatusFile(filename=file)
        else:
            parser = StatusFile(config_name=file)
        print "="*79
        print file
        print "-"*79
        print "Connected clients"
        pprint.pprint(parser.connected_clients)
        print "-"*79
        print "Routing table"
        pprint.pprint(parser.routing_table)
        print "-"*79
        print "Additional details"
        pprint.pprint(parser.details)
