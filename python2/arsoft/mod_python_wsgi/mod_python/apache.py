import sys

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
