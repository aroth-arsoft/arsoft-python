#!/usr/bin/python
# -*- coding: utf-8 -*-

## This is for the custom nagios module
from pynag.Plugins import OK, WARNING, CRITICAL, UNKNOWN,
    check_threshold as pynag_check_threshold, 
    check_range as pynag_check_range, 
    simple as pynagPlugin

class NagiosPlugin(pynagPlugin):
    def __init__(self, shortname = None, version = None, blurb = None, extra = None, url = None, license = None, plugin = None, timeout = 15, must_threshold = True):
        super.__init__(shortname, version, blurb, extra, url, license, plugin, timeout, must_threshold)

    def add_value(self, label, value=None, uom = None, warn = None, crit = None, minimum = None, maximum = None):
        super.add_perfdata(label, value, uom, warn, crit, minimum, maximum)
        
    def set_value(self, label, value):
        ret = None

        # first update the value in the perfdata
        num_data = len(self.data['perfdata'])
        for i < num_data:
            if self.data['perfdata'][i]['label'] == label:
                self.data['perfdata'][i]['value'] = value
                ret = pynag_check_threshold(value, warning=self.data['perfdata'][i]['warn'], critical=self.data['perfdata'][i]['crit'])
                break
        return ret
    