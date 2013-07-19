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

class Statistics(object):
    def __init__(self):
        self.updated = None
        self.device_read = 0
        self.device_write = 0
        self.connection_read = 0
        self.connection_write = 0
        self.auth_read = 0
        self.auth_write = 0
        self.pre_compress = 0
        self.post_compress = 0
        self.pre_decompress = 0
        self.post_decompress = 0

    def __str__(self):
        elems = []
        elems.append('updated=%s' % (self.updated))
        elems.append('device_read=%s' % (self.device_read))
        elems.append('device_write=%s' % (self.device_write))
        elems.append('connection_read=%s' % (self.connection_read))
        elems.append('connection_write=%s' % (self.connection_write))
        elems.append('auth_read=%s' % (self.auth_read))
        elems.append('auth_write=%s' % (self.auth_write))
        elems.append('pre_compress=%s' % (self.pre_compress))
        elems.append('post_compress=%s' % (self.post_compress))
        elems.append('compress_ratio=%s' % (self.compress_ratio))
        elems.append('pre_decompress=%s' % (self.pre_decompress))
        elems.append('post_decompress=%s' % (self.post_decompress))
        elems.append('decompress_ratio=%s' % (self.decompress_ratio))
        return '{' + ';'.join(elems) + '}'
    
    class _StatisticsIterator(object):
        def __init__(self, stats):
            self._stats = stats
            self._properties = []
            for prop in dir(stats):
                if prop[0] == '_':
                    continue
                self._properties.append(prop)
            self._it = iter(self._properties)

        def next(self):
            return next(self._it)

    def __iter__(self):
        return self._StatisticsIterator(self)

    @property
    def compress_ratio(self):
        if self.post_compress and self.pre_compress:
            return float(self.post_compress) / float(self.pre_compress)
        else:
            return 0.0

    @property
    def decompress_ratio(self):
        if self.post_decompress and self.pre_decompress:
            return float(self.post_decompress) / float(self.pre_decompress)
        else:
            return 0.0

    def __setitem__(self, key, value):
        if key == 'Updated':
            try:
                self.updated = datetime.datetime.strptime(value, '%a %b %d %H:%M:%S %Y')
            except (IndexError, ValueError):
                logging.error("Updated time is invalid: %s" % value)
        elif key == 'TUN/TAP read bytes':
            try:
                self.device_read = int(value)
            except ValueError:
                logging.error("%s is invalid: %s" % (key, value))
        elif key == 'TUN/TAP write bytes':
            try:
                self.device_write = int(value)
            except ValueError:
                logging.error("%s is invalid: %s" % (key, value))
        elif key == 'TCP/UDP read bytes':
            try:
                self.connection_read = int(value)
            except ValueError:
                logging.error("%s is invalid: %s" % (key, value))
        elif key == 'TCP/UDP write bytes':
            try:
                self.connection_write = int(value)
            except ValueError:
                logging.error("%s is invalid: %s" % (key, value))
        elif key == 'Auth read bytes':
            try:
                self.auth_read = int(value)
            except ValueError:
                logging.error("%s is invalid: %s" % (key, value))
        elif key == 'Auth write bytes':
            try:
                self.auth_write = int(value)
            except ValueError:
                logging.error("%s is invalid: %s" % (key, value))
        elif key == 'pre-compress bytes':
            try:
                self.pre_compress = int(value)
            except ValueError:
                logging.error("%s is invalid: %s" % (key, value))
        elif key == 'post-compress bytes':
            try:
                self.post_compress = int(value)
            except ValueError:
                logging.error("%s is invalid: %s" % (key, value))
        elif key == 'pre-decompress bytes':
            try:
                self.pre_decompress = int(value)
            except ValueError:
                logging.error("%s is invalid: %s" % (key, value))
        elif key == 'post-decompress bytes':
            try:
                self.post_decompress = int(value)
            except ValueError:
                logging.error("%s is invalid: %s" % (key, value))

class State(object):
    
    STATE_TO_LONG_STATE = {
        'DOWN': 'Connection is down',
        'CONNECTING': 'Initialize connection',
        'WAIT': 'Waiting for initial response from server',
        'AUTH': 'Authenticating with server',
        'GET_CONFIG': 'Downloading configuration options from server',
        'ASSIGN_IP': 'Assigning IP address to virtual network interface',
        'ADD_ROUTES': 'Adding routes to system',
        'CONNECTED': 'Initialization Sequence Completed',
        'RECONNECTING': 'Connection restart has occurred',
        'EXITING': 'Shutting down connection'
        }

    def __init__(self, timestamp=None, name=None, description=None, localip=None, remoteip=None, state_line_elements=None):
        self.timestamp = timestamp
        self.name = name
        self.description = description
        self.localip = localip
        self.remoteip = remoteip
        if state_line_elements is not None:
            self._parse(state_line_elements)

    def _parse(self, state_line_elements):
        if len(state_line_elements) >= 5:
            self.timestamp = datetime.datetime.fromtimestamp(float(state_line_elements[0]))
            self.name = state_line_elements[1]
            self.description = state_line_elements[2]
            self.localip = state_line_elements[3]
            self.remoteip = state_line_elements[4]
            ret = True
        else:
            ret = False
        return ret

    @property
    def is_connecting(self):
        return self.name == 'CONNECTING'

    @property
    def is_waiting(self):
        return self.name == 'WAIT'

    @property
    def is_authenticating(self):
        return self.name == 'AUTH'

    @property
    def is_downloading_config(self):
        return self.name == 'GET_CONFIG'

    @property
    def is_assigning_ip(self):
        return self.name == 'ASSIGN_IP'

    @property
    def is_adding_routes(self):
        return self.name == 'ADD_ROUTES'

    @property
    def is_connected(self):
        return self.name == 'CONNECTED'

    @property
    def is_reconnecting(self):
        return self.name == 'RECONNECTING'

    @property
    def is_exiting(self):
        return self.name == 'EXITING'

    @property
    def is_down(self):
        return self.name == 'DOWN'

    @property
    def long_state(self):
        if self.name in self.STATE_TO_LONG_STATE:
            ret = self.STATE_TO_LONG_STATE[self.name]
        else:
            ret = self.name
        if self.description is not None and len(self.description) != 0:
            ret = ret + ' (%s)' % (self.description)
        return ret

    def __str__(self):
        return '%s,%s,%s,%s,%s' % (self.timestamp,self.name,self.description,self.localip, self.remoteip)
    
class ConnectedClient(object):
    def __init__(self, headers, row):
        self.name = row[1]
        self._info = dict(zip(headers, row[1:]))
        
        self.connected_since = self._get_info('Connected Since (time_t)', type=datetime.datetime, default_value=0)
        self.virtual_address = self._get_info('Virtual Address', type=str)
        self.real_address = self._get_info('Real Address', type=str)
        self.common_name = self._get_info('Common Name', type=str)
        self.bytes_sent = self._get_info('Bytes Sent', type=int)
        self.bytes_received = self._get_info('Bytes Received', type=int)
        
    def _get_info(self, key, type, default_value=None):
        if key in self._info:
            value = self._info[key]
        else:
            value = default_value
        if type == int:
            return int(value)
        elif type == datetime.datetime:
            return datetime.datetime.fromtimestamp(float(value))
        else:
            return value

    def __str__(self):
        return "%s [%s] %s<>%s (%s; %i/%i)" % (self.name, self.common_name, self.virtual_address, self.real_address, self.connected_since, self.bytes_sent, self.bytes_received)

class RoutingTableEntry(object):
    def __init__(self, headers, row):
        self.name = row[1]
        self._info = dict(zip(headers, row[1:]))
        
        self.last_ref = self._get_info('Last Ref (time_t)', type=datetime.datetime, default_value=0)
        self.virtual_address = self._get_info('Virtual Address', type=str)
        self.real_address = self._get_info('Real Address', type=str)
        self.common_name = self._get_info('Common Name', type=str)
        
    def _get_info(self, key, type, default_value=None):
        if key in self._info:
            value = self._info[key]
        else:
            value = default_value
        if type == int:
            return int(value)
        elif type == datetime.datetime:
            return datetime.datetime.fromtimestamp(float(value))
        else:
            return value

    def __str__(self):
        return "%s [%s] %s<>%s (%s)" % (self.name, self.common_name, self.virtual_address, self.real_address, self.last_ref)

class StatusBase(object):
    def __init__(self, version=2):
        self._connected_clients = None
        self._routing_table = None
        self._details = None
        self._statistics = None
        self._reading_done = False
        self._running = False
        self._state = State(name='DOWN')

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

        self._reading_done = True
        read_statistics = False
        topics_for = {}
        csvreader = csv.reader(lines, delimiter=delimiter)
        for row in csvreader:
            row_title = row[0]
            if row_title == "END":
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
                            client = ConnectedClient(headers=topics_for["CLIENT_LIST"], row=row)
                            self._connected_clients[client.name] = client
                        except IndexError:
                            logging.error("CLIENT_LIST row is invalid: %s" % row)

                    elif row_title == "ROUTING_TABLE":
                        try:
                            entry = RoutingTableEntry(headers=topics_for["ROUTING_TABLE"], row=row)
                            self._routing_table[row[2]] = entry
                        except IndexError:
                            logging.error("ROUTING_TABLE row is invalid: %s" % row)

                    elif row_title == "GLOBAL_STATS":
                        try:
                            self._details[row[1]] = row[2]
                        except IndexError:
                            logging.error("GLOBAL_STATS row is invalid: %s" % row)

                    elif row_title == "OpenVPN STATISTICS":
                        read_statistics = True
                        self._statistics = Statistics()

                    else:
                        logging.warning("Line was not parsed. Keyword %s not recognized. %s" % (row_title, row))
                else:
                    try:
                        self._statistics[row[0]] = row[1]
                    except IndexError:
                        logging.error("statistics row is invalid: %s" % row)

        logging.error("File was incomplete. END line was missing.")
        return False

    def _parse_state(self, lines):
        self._state = {}
        csvreader = csv.reader(lines, delimiter=',')
        for row in csvreader:
            row_title = row[0]
            if row_title == "END":
                return True
            else:
                self._state = State(state_line_elements=row)
        logging.error("File was incomplete. END line was missing.")
        return False

    @property
    def details(self):
        """ Returns miscellaneous details from status file """
        if not self._reading_done:
            self._parse_file()
        return self._details

    @property
    def running(self):
        if not self._reading_done:
            self._parse_file()
        return self._running

    @property
    def state(self):
        """ Returns state of the OpenVPN connection """
        return self._state

    @property
    def last_update(self):
        """ Returns the time of the last update of the status file """
        if not self._reading_done:
            self._parse_file()
        if self._details is not None and 'timestamp' in self._details:
            return self._details['timestamp']
        elif self._statistics is not None:
            return self._statistics.updated
        else:
            return None

    @property
    def connected_clients(self):
        """ Returns dictionary of connected clients with details."""
        if not self._reading_done:
            self._parse_file()
        return self._connected_clients

    @property
    def routing_table(self):
        """ Returns dictionary of routing_table used by OpenVPN """
        if not self._reading_done:
            self._parse_file()
        return self._routing_table

    @property
    def statistics(self):
        """ Returns dictionary of statistics used by OpenVPN """
        if not self._reading_done:
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
                    self._version = 2
            elif config_file is not None:
                self.filename = config_file.management_socket
                if self.filename is None:
                    self.filename = config_file.status_file
                    self._version = config_file.status_version
                else:
                    self._is_socket = True
                    self._version = 2
            else:
                self.filename = None
        else:
            self.filename = filename

        self._parse_file()

    def _parse_file(self):
        ret = False
        self._running = False
        if self._is_socket:
            miface = management.ManagementInterface(self.filename)
            if miface.open():
                self._running = True
                lines = miface.state()
                ret = self._parse_state(lines)
                if ret:
                    lines = miface.status(version=self._version)
                    ret = self._parse_lines(lines)
                miface.close()
            else:
                ret = False
        elif self.filename is not None:
            try:
                file = open(self.filename)
            except IOError:
                file = None

            if file is not None:
                lines = file.readlines()
                file.close()
                ret = self._parse_lines(lines)
                self._running = True
            else:
                ret = False
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
        print("="*79)
        print(file)
        print("="*79)
        print("Last updated")
        pprint.pprint(parser.last_update)
        print("Connected clients")
        pprint.pprint(parser.connected_clients)
        print("-"*79)
        print("Routing table")
        pprint.pprint(parser.routing_table)
        print("-"*79)
        print("Additional details")
        pprint.pprint(parser.details)
        print("-"*79)
        print("Statistics")
        pprint.pprint(parser.statistics)
