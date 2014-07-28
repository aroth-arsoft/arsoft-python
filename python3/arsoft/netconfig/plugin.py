#!/usr/bin/python

from optparse import OptionParser
from .main import *

class NetconfigPlugin(object):
    _netconfig = None
    _verbose = False
    _environment = {}
    
    def __init__(self, netconfig=None):
        if netconfig != None:
            self._netconfig = netconfig
        else:
            self._netconfig = Netconfig()
        self._netconfig.addEnvironment(self._environment)

    def run(self):
        action_choices = ['startup', 'shutdown', 'update']
        usage = 'usage: %prog [' + string.join(action_choices,'|') + '] [options]'
        parser = OptionParser(usage)
        parser.add_option('-a', "--action", choices=action_choices, 
                        action="store", dest="action",
                        help="action to perform")
        parser.add_option("-v", "--verbose",
                        action="store_true", dest="verbose", default=False,
                        help="print status messages to stdout")

        (options, args) = parser.parse_args()
        if options.action == None:
            for a in args:
                if a in action_choices:
                    options.action = a
        self._verbose = options.verbose
        if options.action == None:
            parser.error('No action selected')
        
        self.log('action=' + options.action)
        if options.action == 'startup':
            self.startup()
        elif options.action == 'shutdown':
            self.shutdown()
        elif options.action == 'update':
            self.update()
            
    def log(self, *args):
        if self._verbose == False:
            return
        str = ''
        for a in args:
            str += a
        print(str)

    def startup(self):
        return 0
    def shutdown(self):
        return 0
    def update(self):
        return 0
