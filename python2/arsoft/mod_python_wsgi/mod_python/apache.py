#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import sys
import imp
import time
import os

# Apache return codes

OK = 0
DECLINED = 1

REMOTE_NOLOOKUP = 1

# HTTP Status code aliases

HTTP_CONTINUE = 100
HTTP_SWITCHING_PROTOCOLS = 101
HTTP_PROCESSING = 102
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_NON_AUTHORITATIVE = 203
HTTP_NO_CONTENT = 204
HTTP_RESET_CONTENT = 205
HTTP_PARTIAL_CONTENT = 206
HTTP_MULTI_STATUS = 207
HTTP_MULTIPLE_CHOICES = 300
HTTP_MOVED_PERMANENTLY = 301
HTTP_MOVED_TEMPORARILY = 302
HTTP_SEE_OTHER = 303
HTTP_NOT_MODIFIED = 304
HTTP_USE_PROXY = 305
HTTP_TEMPORARY_REDIRECT = 307
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_PAYMENT_REQUIRED = 402
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_NOT_ACCEPTABLE = 406
HTTP_PROXY_AUTHENTICATION_REQUIRED = 407
HTTP_REQUEST_TIME_OUT = 408
HTTP_CONFLICT = 409
HTTP_GONE = 410
HTTP_LENGTH_REQUIRED = 411
HTTP_PRECONDITION_FAILED = 412
HTTP_REQUEST_ENTITY_TOO_LARGE = 413
HTTP_REQUEST_URI_TOO_LARGE = 414
HTTP_UNSUPPORTED_MEDIA_TYPE = 415
HTTP_RANGE_NOT_SATISFIABLE = 416
HTTP_EXPECTATION_FAILED = 417
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_LOCKED = 423
HTTP_FAILED_DEPENDENCY = 424
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_NOT_IMPLEMENTED = 501
HTTP_BAD_GATEWAY = 502
HTTP_SERVICE_UNAVAILABLE = 503
HTTP_GATEWAY_TIME_OUT = 504
HTTP_VERSION_NOT_SUPPORTED = 505
HTTP_VARIANT_ALSO_VARIES = 506
HTTP_INSUFFICIENT_STORAGE = 507
HTTP_NOT_EXTENDED = 510

class SERVER_RETURN(Exception):
    def __init__(self, status_code):
        #print('SERVER_RETURN %i' % status_code)
        Exception.__init__(self)
        self.status_code = status_code

# The APLOG constants in Apache are derived from syslog.h
# constants, so we do same here.

try:
    import syslog
    APLOG_EMERG = syslog.LOG_EMERG     # system is unusable
    APLOG_ALERT = syslog.LOG_ALERT     # action must be taken immediately
    APLOG_CRIT = syslog.LOG_CRIT       # critical conditions
    APLOG_ERR = syslog.LOG_ERR         # error conditions
    APLOG_WARNING = syslog.LOG_WARNING # warning conditions
    APLOG_NOTICE = syslog.LOG_NOTICE   # normal but significant condition
    APLOG_INFO = syslog.LOG_INFO       # informational
    APLOG_DEBUG = syslog.LOG_DEBUG     # debug-level messages
except ImportError:
    APLOG_EMERG = 0
    APLOG_ALERT = 1
    APLOG_CRIT = 2
    APLOG_ERR = 3
    APLOG_WARNING = 4
    APLOG_NOTICE = 5
    APLOG_INFO = 6
    APLOG_DEBUG = 7

def log_error(msg, level=0):
    sys.stderr.write(msg + '\n')


def import_module(module_name, autoreload=1, log=0, path=None):
    """
    Get the module to handle the request. If
    autoreload is on, then the module will be reloaded
    if it has changed since the last import.
    """

    # nlehuen: this is a big lock, we'll have to refine it later to get better performance.
    # For now, we'll concentrate on thread-safety.
    imp.acquire_lock()
    try:
        # (Re)import
        if module_name in sys.modules:

            # The module has been imported already
            module = sys.modules[module_name]
            oldmtime, mtime  = 0, 0

            if autoreload:

                # but is it in the path?
                try:
                    file = module.__dict__["__file__"]
                except KeyError:
                    file = None

                # the "and not" part of this condition is to prevent execution
                # of arbitrary already imported modules, such as os. The
                # reason we use startswith as opposed to exact match is that
                # modules inside packages are actually in subdirectories.

                if not file or (path and not list(filter(file.startswith, path))):
                    # there is a script by this name already imported, but it's in
                    # a different directory, therefore it's a different script
                    mtime, oldmtime = 0, -1 # trigger import
                else:
                    try:
                        last_check = module.__dict__["__mtime_check__"]
                    except KeyError:
                        last_check = 0

                    if (time.time() - last_check) > 1:
                        oldmtime = module.__dict__.get("__mtime__", 0)
                        mtime = module_mtime(module)
            else:
                pass
        else:
            mtime, oldmtime = 0, -1

        if mtime != oldmtime:

            # Import the module
            if log:
                if path:
                    s = "mod_python: (Re)importing module '%s' with path set to '%s'" % (module_name, path)
                else:
                    s = "mod_python: (Re)importing module '%s'" % module_name
                _apache.log_error(s, APLOG_NOTICE)

            parent = None
            parts = module_name.split('.')
            for i in range(len(parts)):
                f, p, d = imp.find_module(parts[i], path)
                try:
                    mname = ".".join(parts[:i+1])
                    module = imp.load_module(mname, f, p, d)
                    if parent:
                        setattr(parent,parts[i],module)
                    parent = module
                finally:
                    if f: f.close()
                if hasattr(module, "__path__"):
                    path = module.__path__

            if mtime == 0:
                mtime = module_mtime(module)

            module.__mtime__ = mtime

        return module
    finally:
        imp.release_lock()

def module_mtime(module):
    """Get modification time of module"""
    mtime = 0
    if "__file__" in module.__dict__:

        filepath = module.__file__

        try:
            # this try/except block is a workaround for a Python bug in
            # 2.0, 2.1 and 2.1.1. See
            # http://sourceforge.net/tracker/?group_id=5470&atid=105470&func=detail&aid=422004

            if os.path.exists(filepath):
                mtime = os.path.getmtime(filepath)

            if os.path.exists(filepath[:-1]) :
                mtime = max(mtime, os.path.getmtime(filepath[:-1]))

            module.__dict__["__mtime_check__"] = time.time()
        except OSError: pass

    return mtime

def resolve_object(module, obj_str, arg=None, silent=0):
    """
    This function traverses the objects separated by .
    (period) to find the last one we're looking for:

       From left to right, find objects, if it is
       an unbound method of a class, instantiate the
       class passing the request as single argument

    'arg' is sometimes req, sometimes filter,
    sometimes connection
    """

    obj = module

    for obj_str in obj_str.split('.'):

        parent = obj

        # don't throw attribute errors when silent
        if silent and not hasattr(obj, obj_str):
            return None

        # this adds a little clarity if we have an attriute error
        if obj == module and not hasattr(module, obj_str):
            if hasattr(module, "__file__"):
                s = "module '%s' contains no '%s'" % (module.__file__, obj_str)
                raise AttributeError(s)

        obj = getattr(obj, obj_str)

        if hasattr(obj, "im_self") and not obj.__self__:
            # this is an unbound method, its class
            # needs to be instantiated
            instance = parent(arg)
            obj = getattr(instance, obj_str)

    return obj
