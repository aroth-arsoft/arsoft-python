#!/usr/bin/python

import re
import io

class Nsswitch(object):
    default_filename = '/etc/nsswitch.conf'
    
    s_service_re = re.compile(
        r'(?P<service>[\w]+)\s*:\s*'         # service name
                                              # any number of space/tab,
                                              # followed by a : separator
                                              # followed by any number of space/tab
        r'(?P<value>.*)$'                     # everything up to eol
        )
    
    def __init__(self, filename=None):
        if filename is None:
            self.m_filename = self.default_filename
        else:
            self.m_filename = filename
        self.m_items = []

    def open(self, filename=None):
        if filename is None:
            filename = self.m_filename
        else:
            self.m_filename = filename

        ret = False
        lineno = 0
        try:
            f = open(filename, 'r')
            for line in f:
                result = self.s_service_re.match(line)
                if result is not None:
                    service = result.group('service')
                    values = result.group('value').split(' ')
                    item = (service, values)
                    
                    self.m_items.append( item )
                else:
                    self.m_items.append ( line.rstrip('\n') )
                lineno = lineno + 1
            f.close()
            ret = True
        except Exception as e:
            print (e)
            ret = False
            pass

        #print(self.m_items)
        return ret
        
    def save(self, filename=None):
        if filename is None:
            filename = self.m_filename
        else:
            self.m_filename = filename

        try:
            f = open(filename, 'w')
            for item in self.m_items:
                if isinstance(item, str):
                    # simply write the line/item
                    f.write(item + '\n')
                else:
                    (service, values) = item
                    line = service + ': ' + ' '.join(values) + '\n'
                    f.write(line)
            f.close()
            ret = True
        except Exception as e:
            print (e)
            ret = False
            pass
        return ret
        
    def filename(self):
        return self.m_filename

    def getService(self, name):
        ret = None
        for item in self.m_items:
            # skip any unrecognized lines (e.g. comments)
            if not isinstance(item, str):
                (service, values) = item
                if service == name:
                    ret = values
                    break
        return ret

    def setService(self, name, values):
        found = False
        i = 0
        while i < len(self.m_items):
            # skip any unrecognized lines (e.g. comments)
            if not isinstance(self.m_items[i], str):
                (service, ignore_values) = self.m_items[i]
                if service == name:
                    self.m_items[i] = (name, values)
                    found = True
                    break
            i = i + 1
        if not found:
            self.m_items.append( (name, values) )
        return True

    @property
    def services(self):
        """ Returns a list of all configured services """
        ret = []
        for item in self.m_items:
            if not isinstance(item, str):
                (service, ignore_values) = item
                ret.append(service)
        return ret

