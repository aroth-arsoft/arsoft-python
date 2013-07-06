#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os
import sys
import socket
import cups
import cupshelpers
from urlparse import urlparse

def _get_dict_value(dict, key, default_value=None):
    return dict[key] if key in dict else default_value

class CupsConnection(object):

    def __init__(self, server=None, port=631):
        if server is not None:
            i = server.find(':')
            if i > 0:
                port = int(server[i+1:])
                server = server[0:i]
            old_server = cups.getServer()
            old_port = cups.getPort()
            cups.setServer(server)
            cups.setPort(port)
        self._conn = cups.Connection ()
        self._server = cups.getServer()
        self._serverip = None
        self._port = cups.getPort()
        self._ppds = None
        if server is not None:
            cups.setServer(old_server)
            cups.setPort(old_port)
        self._temp_ppds = {}
        
    def __del__(self):
        for (printername, ppdfile) in self._temp_ppds.items():
            if os.path.exists(ppdfile):
                os.remove(ppdfile)

    @property
    def server(self):
        return self._server

    @property
    def serverip(self):
        if self._serverip is None:
            self._serverip = socket.gethostbyname(self._server)
        return self._serverip

    @property
    def port(self):
        return self._port

    @property
    def printers(self):
        ret = cupshelpers.getPrinters(self._conn)
        return ret

    @property
    def devices(self):
        ret = cupshelpers.getDevices(self._conn)
        return ret

    @property
    def jobs(self):
        ret = self._conn.getJobs (requested_attributes=r)
        return ret
    
    @property
    def ppds(self):
        if self._ppds is None:
            cupsppds = None
            try:
                cupsppds = self._conn.getPPDs2()
                print "Using getPPDs2()"
            except AttributeError:
                # Need pycups >= 1.9.52 for getPPDs2
                cupsppds = self._conn.getPPDs ()
                print "Using getPPDs()"
            if cupsppds:
                self._ppds = cupshelpers.ppds.PPDs(cupsppds)
        return self._ppds

    def getQueue(self, name):
        queue = self._conn.getPrinterAttributes (name)

    def retrievePPD(self, printername):
        if printername in self._temp_ppds:
            ret = self._temp_ppds[printername]
        else:
            try:
                ppd = self._conn.getPPD(printername)
            except cups.IPPError as e:
                ppd = None
            if ppd is not None and os.path.exists(ppd):
                self._temp_ppds[printername] = ppd
                ret = ppd
            else:
                ret = None
        return ret

    def _equal_printer(self, printer_obj):
        if 'device-uri' in printer_obj:
            o = urlparse(printer_obj['device-uri'])
            ret = True if o.hostname == self._server and o.port == self._port else False
        else:
            ret = False
        return ret
    
    def show_ppds(self, make_filter=None, list_models=True):
        all_ppds = self.ppds
        if all_ppds:
            ret = True
            makes = all_ppds.getMakes ()
            models_count = 0
            if make_filter:
                lower_make_filter = []
                if type(make_filter) == str:
                    lower_make_filter.append(make_filter.lower())
                else:
                    for f in make_filter:
                        lower_make_filter.append(f.lower())
            else:
                lower_make_filter = None
            for make in makes:
                if lower_make_filter and make.lower() not in lower_make_filter:
                    continue
                models = all_ppds.getModels (make)
                models_count += len (models)
                if list_models:
                    print make
                    for model in models:
                        print "  " + model
        else:
            ret = False
        return ret

    @classmethod
    def _is_printer_on_server(self, printer_obj, serverip, port):
        if 'device-uri' in printer_obj:
            o = urlparse(printer_obj['device-uri'])
            ret = True if o.hostname == serverip and o.port == port else False
        else:
            ret = False
        return ret

    def add_remote_printers(self, conn_remote):
        ret = True
        printers_to_remove = set()
        remote_server = conn_remote.server
        for (printername, printer_obj) in self.printers:
            # only add the printer from the remote connection
            # to the set of printers to remove (so all local
            # printers and printers from other remote locations
            # are kept).
            if conn_remote._equal_printer(printer_obj):
                printers_to_remove.add(printername)

        for (printername, printer_obj) in conn_remote.printers:
            if printername in printers_to_remove:
                printers_to_remove.remove(printername)
            else:
                if 'printer-uri-supported' in printer_obj:
                    printer_uri = printer_obj['printer-uri-supported']
                else:
                    printer_uri = None
                local_ppdfilename = conn_remote.retrievePPD(printername)
                if local_ppdfilename is None:
                    ret = False
                else:
                    try:
                        self._conn.addPrinter(printername, filename=local_ppdfilename, device=printer_uri)
                    except cups.IPPError as e:
                        ret = False

        for printername in printers_to_remove:
            try:
                self._conn.deletePrinter(printername)
            except cups.IPPError as e:
                ret = False
        return ret

    def remove_remote_printers_conn(self, conn_remote):
        ret = True
        printers_to_remove = set()
        for (printername, printer_obj) in self.printers:
            # only add the printer from the remote connection
            # to the set of printers to remove (so all local
            # printers and printers from other remote locations
            # are kept).
            if conn_remote._equal_printer(printer_obj):
                printers_to_remove.add(printername)

        for printername in printers_to_remove:
            try:
                self._conn.deletePrinter(printername)
            except cups.IPPError as e:
                ret = False
        return ret

    def remove_remote_printers(self, remote_server):
        ret = True
        printers_to_remove = set()
        i = remote_server.find(':')
        if i > 0:
            port = remote_server[i+1:]
            server = remote_server[0:i]
        else:
            port = 631
            server = remote_server
        serverip = socket.gethostbyname(server)
        for (printername, printer_obj) in self.printers:
            # only add the printer from the remote connection
            # to the set of printers to remove (so all local
            # printers and printers from other remote locations
            # are kept).
            if CupsConnection._is_printer_on_server(printer_obj, serverip, port):
                printers_to_remove.add(printername)

        for printername in printers_to_remove:
            try:
                self._conn.deletePrinter(printername)
            except cups.IPPError as e:
                ret = False
        return ret

    def set_default_printer(self, printername):
        try:
            self._conn.setDefault(printername)
            ret = True
        except cups.IPPError as e:
            ret = False
        return ret
