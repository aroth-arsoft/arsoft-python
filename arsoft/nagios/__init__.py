#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import sys
import os
import re
import collections
import types
from platform import node
import argparse


# Map the return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

class pynagPlugin:
    """
    Nagios plugin helper library based on Nagios::Plugin

    Sample usage

    from pynag.Plugins import WARNING, CRITICAL, OK, UNKNOWN, simple as Plugin

    # Create plugin object
    np = Plugin()
    # Add arguments
    np.add_arg("d", "disk")
    # Do activate plugin
    np.activate()
    ... check stuff, np['disk'] to address variable assigned above...
    # Add a status message and severity
    np.add_message( WARNING, "Disk nearing capacity" )
    # Get parsed code and messages
    (code, message) = np.check_messages()
    # Return information and exit
    nagios_exit(code, message)
    """

    def __init__(self, shortname = None, version = None, blurb = None, url = None, license = None, plugin = None, timeout = 15, must_threshold = True, has_host_argument=True, optional_threshold=False):

        ## Variables we'll get later
        self.opts = None
        self.has_host_argument = has_host_argument
        self.must_threshold = must_threshold
        self.optional_threshold = optional_threshold
        self.data = {}
        self.data['perfdata'] = []
        self.data['messages'] = { OK:[], WARNING:[], CRITICAL:[], UNKNOWN:[] }
        self.data['threshhold'] = None

        ## Error mappings, for easy access
        self.errors = { "OK":0, "WARNING":1, "CRITICAL":2, "UNKNOWN":3, }
        self.status_text = { 0:"OK", 1:"WARNING", 2:"CRITICAL", 3:"UNKNOWN", }

        ## Shortname creation
        if not shortname:
            self.data['shortname'] = os.path.basename("%s" % sys.argv[0])
        else:
            self.data['shortname'] = shortname

        ## Set the option parser stuff here
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-v", "--verbose", dest="verbose", help="Verbosity Level", metavar="VERBOSE", default=0)
        if self.has_host_argument:
            self.parser.add_argument("-H", "--host", dest="host", help="Target Host", metavar="HOST")
            self.parser.add_argument("-t", "--timeout", dest="timeout", default=timeout, type=int, help="Connection Timeout", metavar="TIMEOUT")

        if self.must_threshold or self.optional_threshold:
            self.parser.add_argument("-c", "--critical", dest="critical", help="Critical Threshhold", required=self.must_threshold, metavar="CRITICAL")
            self.parser.add_argument("-w", "--warning", dest="warning", help="Warn Threshhold", required=self.must_threshold, metavar="WARNING")

    def add_arg(self, spec_abbr, spec, help_text, required=1, action="store"):
        """
        Add an argument to be handled by the option parser.  By default, the arg is not required.
        
        required = optional parameter
        action = [store, append, store_true]
        """
        self.parser.add_argument("-%s" % spec_abbr, "--%s" % spec, dest="%s" % spec, help=help_text, metavar="%s" % spec.upper(), required=required, action=action)

    def activate(self):
        """
        Parse out all command line options and get ready to process the plugin.  This should be run after argument preps
        """
        args = self.parser.parse_args()

        ## Set verbosity level
        if int(args.verbose) in (0, 1, 2, 3):
            self.data['verbosity'] = args.verbose
        else:
            self.data['verbosity'] = 0

        ## Ensure the hostname is set
        if self.has_host_argument:
            self.data['host'] = args.host
            self.data['timeout'] = args.timeout

        if self.must_threshold or self.optional_threshold:
            ## Set Critical
            self.data['critical'] = args.critical

            ## Set Warn
            self.data['warning'] = args.warning
            
        for (name, value) in vars(args).iteritems():
            self.data[name] = value

    def add_perfdata(self, label , value , uom = None, warn = None, crit = None, minimum = None, maximum = None, exclude=False):
        """
        Append perfdata string to the end of the message
        """

        # Append perfdata (assume multiple)
        self.data['perfdata'].append({ 'label' : label, 'value' : value, 'uom' : uom, 
            'warn' : warn, 'crit' : crit, 'min' : minimum, 'max' : maximum, 'exclude': 1 if exclude else 0 })

    def check_range(self, value):
        """
        Check if a value is within a given range.  This should replace change_threshold eventually. Exits with appropriate exit code given the range.

        Taken from:  http://nagiosplug.sourceforge.net/developer-guidelines.html
        Range definition
    
        Generate an alert if x...
        10        < 0 or > 10, (outside the range of {0 .. 10})
        10:        < 10, (outside {10 .. #})
        ~:10    > 10, (outside the range of {-# .. 10})
        10:20    < 10 or > 20, (outside the range of {10 .. 20})
        @10:20    # 10 and # 20, (inside the range of {10 .. 20})
        """
        critical = self.data['critical']
        warning = self.data['warning']
        self.hr_range = ""

        if critical and self._range_checker(value, critical):
            self.add_message(CRITICAL,"%s is within critical range: %s" % (value, critical))
        elif warning and self._range_checker(value, warning):
            self.add_message(WARNING,"%s is within warning range: %s" % (value, warning))
        else:
            self.add_message(OK,"%s is outside warning=%s and critical=%s" % (value, warning, critical))

        # Get all messages appended and exit code
        (code, message) = self.check_messages()

        # Exit with appropriate exit status and message
        self.nagios_exit(code, message)

    def _range_checker(self, value, range_threshold):
        """ deprecated. Use pynag.Plugins.check_range() """
        return check_range(value=value, range_threshold=range_threshold)

    def send_nsca(self, code, message, ncsahost, hostname=node(), service=None):
        """
        Send data via send_nsca for passive service checks
        """
    
        # Execute send_nsca
        from popen2 import Popen3
        command = "send_nsca -H %s" % ncsahost
        p = Popen3(command,  capturestderr=True)

        # Service check
        if service:
            print >>p.tochild, "%s    %s    %s    %s %s" % (hostname, service, code, message, self.perfdata_string())
        # Host check, omit service_description
        else:
            print >>p.tochild, "%s    %s    %s %s" % (hostname, code, message, self.perfdata_string())

        # Send eof
        # TODO, support multiple statuses ?
        p.tochild.close()

        # Save output incase we have an error
        nsca_output = ''
        for line in p.fromchild.readlines():
            nsca_output += line

        # Wait for send_nsca to exit
        returncode = p.wait()
        returncode = os.WEXITSTATUS( returncode) 

        # Problem with running nsca
        if returncode != 0:
            if returncode == 127:
                raise Exception("Could not find send_nsca in path")
            else:
                raise Exception("returncode: %i\n%s" % (returncode, nsca_output))

        return 0

    def nagios_exit(self, code_text, message):
        """
        Exit with exit_code, message, and optionally perfdata
        """

        # Change text based codes to int
        code = self.code_string2int(code_text)

        ## This should be one line (or more in nagios 3)
        print "%s: %s %s" % (self.status_text[code], message, self.perfdata_string())
        sys.exit(code)

    def perfdata_string(self):

        ## Append perfdata to the message, if perfdata exists
        if self.data['perfdata']:
            append = '|'
        else:
            append = ''

        for pd in self.data['perfdata']:
            if pd['exclude'] != 0:
                continue
            if isinstance(pd['value'], collections.Iterable) and not isinstance(pd['value'], types.StringTypes):
                pd_value = ','.join(pd['value'])
            else:
                pd_value = pd['value']

            append += " '%s'=%s%s;%s;%s;%s;%s" % (
                pd['label'],
                pd_value,
                pd['uom'] or '',
                pd['warn'] or '',
                pd['crit'] or '',
                pd['min'] or '',
                pd['max'] or '')

        return append

    def add_message( self, code, message ):
        """
        Add a message with code to the object. May be called
        multiple times.  The messages added are checked by check_messages,
        following.

        Only CRITICAL, WARNING, OK and UNKNOWN are accepted as valid codes.
        """
        # Change text based codes to int
        code = self.code_string2int(code)

        self.data['messages'][code].append( message )

    def check_messages( self, joinstr = " ", joinallstr = None ):
        """
        Check the current set of messages and return an appropriate nagios
        return code and/or a result message. In scalar context, returns
        only a return code; in list context returns both a return code and
        an output message, suitable for passing directly to nagios_exit()

        joinstr = string
            A string used to join the relevant array to generate the
            message string returned in list context i.e. if the 'critical'
            array is non-empty, check_messages would return:
                joinstr.join(critical)

        joinallstr = string
            By default, only one set of messages are joined and returned in
            the result message i.e. if the result is CRITICAL, only the
            'critical' messages are included in the result; if WARNING,
            only the 'warning' messages are included; if OK, the 'ok'
            messages are included (if supplied) i.e. the default is to
            return an 'errors-only' type message.

            If joinallstr is supplied, however, it will be used as a string
            to join the resultant critical, warning, and ok messages
            together i.e.  all messages are joined and returned.
        """
        # Check for messages in unknown, critical, warning, ok to determine
        # code
        keys = self.data['messages'].keys()
        keys.sort(reverse=True)
        code = UNKNOWN
        for code in keys:
            if len(self.data['messages'][code]):
                break

        # Create the relevant message for the most severe code
        if joinallstr is None:
            message = joinstr.join(self.data['messages'][code])
        # Join all strings whether OK, WARN...
        else:
            message = ""
            for c in keys:
                if len(self.data['messages'][c]):
                    message += joinallstr.join(self.data['messages'][c]) + joinallstr

        return code, message.rstrip(joinallstr)

    def code_string2int( self, code_text ):
        """
        Changes CRITICAL, WARNING, OK and UNKNOWN code_text to integer
        representation for use within add_message() and nagios_exit()
        """

        # If code_text is a string, convert to the int
        if str(type(code_text)) == "<type 'str'>":
            code = self.errors[code_text]
        else:
            code = code_text

        return code

    def __setitem__(self, key, item):
        self.data[key] = item

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        else:
            return None

def check_threshold(value, warning=None, critical=None):
    """ Checks value against warning/critical and returns Nagios exit code.

    Format of range_threshold is according to:
    http://nagiosplug.sourceforge.net/developer-guidelines.html#THRESHOLDFORMAT

    Returns (in order of appearance):
        UNKNOWN int(3)  -- On errors or bad input
        CRITICAL int(2) -- if value is within critical threshold
        WARNING int(1)  -- If value is within warning threshold
        OK int(0)       -- If value is outside both tresholds
    Arguments:
        value -- value to check
        warning -- warning range
        critical -- critical range

    # Example Usage:
    >>> check_threshold(88, warning="90:", critical="95:")
    0
    >>> check_threshold(92, warning="90:", critical="95:")
    1
    >>> check_threshold(96, warning="90:", critical="95:")
    2
    """
    if critical and not check_range(value, critical):
        return CRITICAL
    elif warning and not check_range(value, warning):
        return WARNING
    else:
        return OK


def check_range(value, range_threshold=None):
    """ Returns True if value is within range_threshold.

    Format of range_threshold is according to:
    http://nagiosplug.sourceforge.net/developer-guidelines.html#THRESHOLDFORMAT

    Arguments:
        value -- Numerical value to check (i.e. 70 )
        range -- Range to compare against (i.e. 0:90 )
    Returns:
        True  -- If value is inside the range
        False -- If value is outside the range (alert if this happens)

    Summary from plugin developer guidelines:
    ---------------------------------------------------------
    x       Generate an alert if x...
    ---------------------------------------------------------
    10      < 0 or > 10, (outside the range of {0 .. 10})
    10:     < 10, (outside {10 .. ∞})
    ~:10    > 10, (outside the range of {-∞ .. 10})
    10:20   < 10 or > 20, (outside the range of {10 .. 20})
    @10:20  ≥ 10 and ≤ 20, (inside the range of {10 .. 20})
    10      < 0 or > 10, (outside the range of {0 .. 10})
    ---------------------------------------------------------


    # Example runs for doctest, False should mean alert
    >>> check_range(78, "90") # Example disk is 78% full, threshold is 90
    True
    >>> check_range(5, 10) # Everything between 0 and 10 is True
    True
    >>> check_range(0, 10) # Everything between 0 and 10 is True
    True
    >>> check_range(10, 10) # Everything between 0 and 10 is True
    True
    >>> check_range(11, 10) # Everything between 0 and 10 is True
    False
    >>> check_range(-1, 10) # Everything between 0 and 10 is True
    False
    >>> check_range(-1, "~:10") # Everything Below 10
    True
    >>> check_range(11, "10:") # Everything above 10 is True
    True
    >>> check_range(1, "10:") # Everything above 10 is True
    False
    >>> check_range(0, "5:10") # Everything between 5 and 10 is True
    False
    >>> check_range(0, "@5:10") # Everything outside 5:10 is True
    True
    """

    # if no range_threshold is provided, assume everything is ok
    if not range_threshold:
        range_threshold='~:'
    range_threshold = str(range_threshold)
    # If range starts with @, then we do the opposite
    if range_threshold[0] == '@':
        return not check_range(value, range_threshold[1:])

    value = float(value)
    if range_threshold.find(':') > -1:
        (start,end) = (range_threshold.split(':', 1))
    # we get here if ":" was not provided in range_threshold
    else:
        start = ''
        end = range_threshold
    # assume infinity if start is not provided
    if start == '~':
        start = None
    # assume start=0 if start is not provided
    if start == '':
        start = 0
    # assume infinity if end is not provided
    if end == '':
        end = None
    # start is defined and value is lower than start
    if start is not None and float(value) < float(start):
        return False
    if end is not None and float(value) > float(end):
        return False
    return True

class NagiosPlugin(pynagPlugin):
    
    def __init__(self, shortname = None, version = None, blurb = None, url = None, license = None, plugin = None, timeout = 15, must_threshold = True,
                 has_host_argument=True, optional_threshold=False):
        pynagPlugin.__init__(self, shortname, version, blurb, url, license, plugin, timeout, 
                             must_threshold=must_threshold, has_host_argument=has_host_argument, optional_threshold=optional_threshold)
        
        self._named_values = {}

    def add_value(self, label, description=None, guitext=None, value=None, units=None, uom=None, warning=False, critical=False, has_argument=True):
        pynagPlugin.add_perfdata(self, label, value=value, uom=uom)

        if has_argument:
            self.add_arg(label[0], label, description, required=None)
        
        self._named_values[label] = { 'description':description, 'guitext':guitext, 'units':units, 'uom':uom, 'warning': warning, 'critical': critical }
        return None

    def add_arg(self, spec_abbr, spec, help_text, required=1, action="store", default=None):
        """
        Add an argument to be handled by the option parser.  By default, the arg is not required.
        
        required = optional parameter
        action = [store, append, store_true]
        """
        self.parser.add_argument("-%s" % spec_abbr, "--%s" % spec, dest="%s" % spec, help=help_text, metavar="%s" % spec.upper(), action=action, default=default)

    def add_flag(self, spec_abbr, spec, help_text, action="store_true", default=False):
        self.parser.add_argument("-%s" % spec_abbr, "--%s" % spec, dest="%s" % spec, help=help_text, action=action, default=default)

    def set_value_range(self, label, warning, critical):
        # first update the value in the perfdata
        num_data = len(self.data['perfdata'])
        i = 0
        while i < num_data:
            if self.data['perfdata'][i]['label'] == label:
                self.data['perfdata'][i]['warn'] = warning
                self.data['perfdata'][i]['crit'] = critical
                #print(str(self.data['perfdata'][i]))
                break
            i = i + 1

    def set_value(self, label, value):
        ret = None

        # first update the value in the perfdata
        num_data = len(self.data['perfdata'])
        i = 0
        while i < num_data:
            if self.data['perfdata'][i]['label'] == label:
                self.data['perfdata'][i]['value'] = value
                ret = check_threshold(value, warning=self.data['perfdata'][i]['warn'], critical=self.data['perfdata'][i]['crit'])
                break
            i = i + 1
        return ret

    def exclude_value(self, label, exclude=True):
        ret = False

        # first update the value in the perfdata
        num_data = len(self.data['perfdata'])
        i = 0
        while i < num_data:
            if self.data['perfdata'][i]['label'] == label:
                self.data['perfdata'][i]['exclude'] = 1 if exclude else 0
                ret = True
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
        code = check_threshold(value_item['value'], warning=value_item['warn'], critical=value_item['crit'])
        if code == OK:
            msg = None
        elif code == WARNING or code == CRITICAL:
            named_value_item = self._named_values[value_item['label']]
            gui_value_name = named_value_item['guitext'] if named_value_item['guitext'] is not None else value_item['label']
            if named_value_item['units'] is not None:
                gui_units = named_value_item['units']
            elif named_value_item['uom'] is not None:
                gui_units = named_value_item['uom']
            else:
                gui_units = ''
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
            if self.data['perfdata'][i]['exclude'] == 0:
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
    