#!/usr/bin/python
# -*- coding: utf-8 -*-

## This is for the custom nagios module
from pynag.Plugins import OK, WARNING, CRITICAL, UNKNOWN, \
    check_threshold as pynag_check_threshold, \
    check_range as pynag_check_range, \
    simple as pynagPlugin

class NagiosPlugin(pynagPlugin):
    
    def __init__(self, shortname = None, version = None, blurb = None, extra = None, url = None, license = None, plugin = None, timeout = 15, must_threshold = True):
        pynagPlugin.__init__(self, shortname, version, blurb, extra, url, license, plugin, timeout, must_threshold)
        
        self._named_values = {}

    def add_value(self, label, description=None, guitext=None, units=None, warning=False, critical=False):
        pynagPlugin.add_perfdata(self, label, value=None)

        self.add_arg(label[0], label, description, required=None)
        
        self._named_values[label] = { 'description':description, 'guitext':guitext, 'units':units, 'warning': warning, 'critical': critical }
        return None

    def set_value(self, label, value):
        ret = None

        # first update the value in the perfdata
        num_data = len(self.data['perfdata'])
        i = 0
        while i < num_data:
            if self.data['perfdata'][i]['label'] == label:
                self.data['perfdata'][i]['value'] = value
                ret = pynag_check_threshold(value, warning=self.data['perfdata'][i]['warn'], critical=self.data['perfdata'][i]['crit'])
                break
            i = i + 1
        return ret
    def activate(self):
        pynagPlugin.activate(self)

        # first update the value in the perfdata
        num_data = len(self.data['perfdata'])
        i = 0
        while i < num_data:
            label_name = self.data['perfdata'][i]['label']
            label_value = self[label_name]
            if label_value is not None:
                for label, named_value_data in self._named_values.items():
                    if label_name == label:
                        if named_value_data['warning']:
                            self.data['perfdata'][i]['warn'] = label_value
                        if named_value_data['critical']:
                            self.data['perfdata'][i]['crit'] = label_value
                        break
            i = i + 1

    def _check_threshold(self, value_item):
        #print('_check_threshold ' + str(value_item))
        code = pynag_check_threshold(value_item['value'], warning=value_item['warn'], critical=value_item['crit'])
        if code == OK:
            msg = None
        elif code == WARNING or code == CRITICAL:
            named_value_item = self._named_values[value_item['label']]
            gui_value_name = named_value_item['guitext'] if named_value_item['guitext'] is not None else named_value_item['label']
            gui_units = ' ' + named_value_item['units'] if named_value_item['units'] is not None else ''
            gui_range = value_item['warn'] if code == WARNING else value_item['crit']
            msg = '%s (%s%s) outside specified range %s%s' \
                % (gui_value_name, str(value_item['value']), gui_units, gui_range, gui_units)
        else:
            msg = None
        return (code, msg)
        
    def check_values(self):
        # first update the value in the perfdata
        num_data = len(self.data['perfdata'])
        i = 0
        exit_code = OK
        exit_message = ''
        while i < num_data:
            (ret, msg) = self._check_threshold(self.data['perfdata'][i])
            if ret != OK:
                #print(str(self.data['perfdata'][i]) + ' not ok')
                if ret > exit_code:
                    exit_code = ret
                if exit_message:
                    exit_message = exit_message + ',' + msg
                else:
                    exit_message = msg
            i = i + 1
        return (exit_code, exit_message)
    