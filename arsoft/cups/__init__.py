#!/usr/bin/python

import cups
import os
import socket
from urlparse import urlparse

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
        ret = self._conn.getPrinters ()
        return ret.items()
        
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

    def _show_printer(self, printername, printer_obj, include_raw=False):
        if 'printer-uri-supported' in printer_obj:
            printer_uri = printer_obj['printer-uri-supported']
        else:
            printer_uri = None
        if 'device-uri' in printer_obj:
            device_uri = printer_obj['device-uri']
        else:
            device_uri = None
        if 'printer-info' in printer_obj:
            description = printer_obj['printer-info']
        else:
            description = None
        if 'printer-location' in printer_obj:
            location = printer_obj['printer-location']
        else:
            location = None

        print('  Printer: ' + printername)
        print('    URI: ' + str(printer_uri))
        print('    Device URI: ' + str(device_uri))
        ppd = self.retrievePPD(printername)
        if ppd is not None:
            print('    PPD file: ' + str(ppd))
        else:
            print('    PPD file: not available')
        if include_raw:
            for (name, value) in printer_obj.items():
                print('    ' + name + ': ' + str(value))
    
    def show_printers(self, include_raw=False):
        print('Printers on ' + str(self._server) + ':' + str(self._port))
        for (printername, printer_obj) in self.printers:
            self._show_printer(printername, printer_obj, include_raw=include_raw)
        return True

    def _equal_printer(self, printer_obj):
        if 'device-uri' in printer_obj:
            o = urlparse(printer_obj['device-uri'])
            ret = True if o.hostname == self._server and o.port == self._port else False
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
