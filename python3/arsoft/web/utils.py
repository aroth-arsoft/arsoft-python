#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
import sys
import types
import re
import os.path
import collections

def _get_system_language_code():
    # Language code for this installation. All choices can be found here:
    # http://www.i18nguy.com/unicode/language-identifiers.html
    import locale
    (lang_code, charset) = locale.getdefaultlocale()
    if lang_code == None:
        ret = 'en-US'
    else:
        # convert en_US to en-US
        ret = lang_code.replace('_', '-')
    return ret

def _get_system_timezone():
    import time
    ret = time.tzname[0]
    return ret

def _get_default_admin():
    import socket
    fqdn = socket.getfqdn()
    return ('root', 'root@' + fqdn)

def _is_running_in_devserver(appdir):
    import __main__
    main_script = os.path.abspath(__main__.__file__)
    if main_script == os.path.join(appdir, 'manage.py'):
        return True
    elif '--in-development' in sys.argv:
        return True
    else:
        return False


HIDDEN_SETTINGS = re.compile('API|TOKEN|KEY|SECRET|PASS|PROFANITIES_LIST|SIGNATURE')

CLEANSED_SUBSTITUTE = '********************'

def cleanse_setting(key, value):
    """Cleanse an individual setting key/value of sensitive content.

    If the value is a dictionary, recursively cleanse the keys in
    that dictionary.
    """
    try:
        if HIDDEN_SETTINGS.search(key):
            cleansed = CLEANSED_SUBSTITUTE
        else:
            if isinstance(value, dict):
                cleansed = dict((k, cleanse_setting(k, v)) for k, v in value.items())
            else:
                cleansed = value
    except TypeError:
        # If the key isn't regex-able, just return as-is.
        cleansed = value

    if isinstance(cleansed, collections.Callable):
        # For fixing #21345 and #23070
        cleansed = CallableSettingWrapper(cleansed)
    return cleansed

def get_safe_settings():
    from django.conf import settings
    "Returns a dictionary of the settings module, with sensitive settings blurred out."
    settings_dict = {}
    for k in dir(settings):
        if k.isupper():
            settings_dict[k] = cleanse_setting(k, getattr(settings, k))
    return settings_dict

def is_debug_info_disabled():
    from django.conf import settings
    if hasattr(settings, 'DISABLE_DEBUG_INFO_PAGE'):
        return bool(getattr(settings, 'DISABLE_DEBUG_INFO_PAGE'))
    else:
        return False

def initialize_settings(settings_module, setttings_file, options={}):
    settings_obj = sys.modules[settings_module]
    settings_obj_type = type(settings_obj)
    appname = settings_module
    settings_module_elems = settings_module.split('.')
    setttings_dir = os.path.dirname(setttings_file)
    if settings_module_elems[-1] == 'settings':
        appname_elems = settings_module_elems[:-1]
        appname = '.'.join(appname_elems)
        settings_dir_end = '/'.join(appname_elems)
        app_etc_dir = os.path.join('/etc', settings_dir_end)
        if setttings_dir.endswith(settings_dir_end):
            appdir = setttings_dir[:-len(settings_dir_end)]
        else:
            appdir = setttings_dir
        app_data_dir = os.path.join('/var/lib', settings_dir_end)
    else:
        appdir = setttings_dir
        app_etc_dir = setttings_dir
        app_data_dir = setttings_dir
    in_devserver = _is_running_in_devserver(appdir)

    if 'BASE_PATH' in os.environ:
        settings_obj.BASE_PATH = os.environ['BASE_PATH']
        if len(settings_obj.BASE_PATH) > 2 and settings_obj.BASE_PATH[-1] == '/':
            settings_obj.BASE_PATH = settings_obj.BASE_PATH[:-1]
    else:
        settings_obj.BASE_PATH = ''

    #print('initialize_settings for ' + appname + ' appdir ' + appdir + ' debug=' + str(in_devserver) + ' basepath=' + str(settings_obj.BASE_PATH))

    if 'debug' in options:
        settings_obj.DEBUG = options['debug']
    else:
        settings_obj.DEBUG = in_devserver

    # If DISABLE_DEBUG_INFO_PAGE is set the 
    settings_obj.DISABLE_DEBUG_INFO_PAGE = False

    settings_obj.ADMINS = _get_default_admin()
    settings_obj.MANAGERS = settings_obj.ADMINS

    # If you set this to False, Django will make some optimizations so as not
    # to load the internationalization machinery.
    settings_obj.USE_I18N = True

    # If you set this to False, Django will not format dates, numbers and
    # calendars according to the current locale.
    settings_obj.USE_L10N = True

    # use the language code from the system
    settings_obj.LANGUAGE_CODE = _get_system_language_code()

    # If you set this to False, Django will not use timezone-aware datetimes.
    settings_obj.USE_TZ = True
    
    # Local time zone for this installation. Choices can be found here:
    # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
    # although not all choices may be available on all operating systems.
    # In a Windows environment this must be set to your system time zone.
    settings_obj.TIME_ZONE = _get_system_timezone()

    # Absolute path to the directory static files should be collected to.
    # Don't put anything in this directory yourself; store your static files
    # in apps' "static/" subdirectories and in STATICFILES_DIRS.
    # Example: "/home/media/media.lawrence.com/static/"
    settings_obj.STATIC_ROOT = ''

    # URL prefix for static files.
    # Example: "http://media.lawrence.com/static/"
    settings_obj.STATIC_URL = settings_obj.BASE_PATH + '/static/'

    # Absolute filesystem path to the directory that will hold user-uploaded files.
    # Example: "/home/media/media.lawrence.com/media/"
    settings_obj.MEDIA_ROOT = app_data_dir

    # URL that handles the media served from MEDIA_ROOT. Make sure to use a
    # trailing slash.
    # Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
    settings_obj.MEDIA_URL = settings_obj.BASE_PATH + '/media/'

    settings_obj.ROOT_URLCONF = appname + '.urls'

    # Python dotted path to the WSGI application used by Django's runserver.
    settings_obj.WSGI_APPLICATION = appname + '.wsgi.application'

    settings_obj.SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

    settings_obj.MIDDLEWARE = [
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ]

    settings_obj.AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']

    settings_obj.LOGIN_URL = settings_obj.BASE_PATH + '/accounts/login/'

    # use sendmail as email backend by default
    settings_obj.EMAIL_BACKEND = 'arsoft.web.backends.SendmailBackend'

    settings_obj.SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')
    
    # Additional locations of static files and the  List of finder classes 
    # that know how to find static files in various locations.
    if in_devserver:
        app_static_dir = os.path.join(appdir, 'static')
        if os.path.exists(app_static_dir):
            settings_obj.STATICFILES_DIRS = [ app_static_dir ]
        else:
            settings_obj.STATICFILES_DIRS = []
    else:
        settings_obj.STATICFILES_DIRS = [ os.path.join(app_etc_dir, 'static') ]
    settings_obj.STATICFILES_FINDERS = [ 'django.contrib.staticfiles.finders.FileSystemFinder', 'django.contrib.staticfiles.finders.AppDirectoriesFinder' ]

    # set up the template directories and loaders
    template_dirs = []
    if in_devserver:
        app_template_dir = os.path.join(appdir, 'templates')
        if os.path.exists(app_template_dir):
            template_dirs = [ app_template_dir ]
        else:
            template_dirs = []
    else:
        template_dirs = [ os.path.join(app_etc_dir, 'templates') ]

    settings_obj.TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': template_dirs,
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                    # list if you haven't customized them:
                    'django.contrib.auth.context_processors.auth',
                    'django.template.context_processors.debug',
                    'django.template.context_processors.i18n',
                    'django.template.context_processors.media',
                    'django.template.context_processors.static',
                    'django.template.context_processors.tz',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]

    # set config directory
    if in_devserver:
        settings_obj.CONFIG_DIR = os.path.join(appdir, 'config')
    else:
        settings_obj.CONFIG_DIR = os.path.join(app_etc_dir, 'config')

    # set application data directory
    if in_devserver:
        settings_obj.APP_DATA_DIR = os.path.join(appdir, 'data')
    else:
        settings_obj.APP_DATA_DIR = app_data_dir

    # and finally set up the list of installed applications
    settings_obj.INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'arsoft.web',
            appname
            ]
    if in_devserver:
        settings_obj.LOG_DIR = os.path.join(appdir, 'data')
        if not os.path.isdir(settings_obj.LOG_DIR):
            # create LOG_DIR if it does not exists
            os.makedirs(settings_obj.LOG_DIR)
    else:
        settings_obj.LOG_DIR = '/var/log/django'
    # A sample logging configuration. The only tangible logging
    # performed by this configuration is to send an email to
    # the site admins on every HTTP 500 error when DEBUG=False.
    # See http://docs.djangoproject.com/en/dev/topics/logging for
    # more details on how to customize your logging configuration.
    settings_obj.LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
                },
                'simple': {
                    'format': '%(levelname)s %(message)s'
                },
            },
            'filters': {
                'require_debug_false': {
                    '()': 'django.utils.log.RequireDebugFalse'
                }
            },
            'handlers': {
                'null': {
                    'level': 'DEBUG',
                    'class': 'logging.NullHandler',
                },
                'console':{
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple'
                },
                'mail_admins': {
                    'level': 'ERROR',
                    'filters': ['require_debug_false'],
                    'class': 'django.utils.log.AdminEmailHandler',
                    # But the emails are plain text by default - HTML is nicer
                    'include_html': True,
                },
                # Log to a text file that can be rotated by logrotate
                'logfile': {
                    'class': 'logging.handlers.WatchedFileHandler',
                    'filename': os.path.join(settings_obj.LOG_DIR, appname + '.log')
                },
            },
            'loggers': {
                'django.request': {
                    'handlers': ['mail_admins', 'logfile'] if not settings_obj.DEBUG else ['logfile'],
                    'level': 'ERROR' if not settings_obj.DEBUG else 'DEBUG',
                    'propagate': True,
                },
                # Might as well log any errors anywhere else in Django
                'django': {
                    'handlers': ['logfile'],
                    'level': 'ERROR' if not settings_obj.DEBUG else 'DEBUG',
                    'propagate': True,
                },
                appname: {
                    'handlers': ['console', 'logfile'],
                    'level': 'ERROR' if not settings_obj.DEBUG else 'DEBUG',
                    'propagate': True,
                },
            }
        }

    custom_settings_file = os.path.join(settings_obj.CONFIG_DIR, 'settings.py')
    #print(custom_settings_file)
    if os.path.exists(custom_settings_file):
        exec(compile(open(custom_settings_file).read(), custom_settings_file, 'exec'))

    #print(settings_obj.INSTALLED_APPS)

def django_request_info_view(request):
    import datetime
    from django.http import HttpResponse
    from django.template import Template, Context
    from django.core.urlresolvers import get_script_prefix
    from django import get_version

    disable = is_debug_info_disabled()
    if disable:
        return HttpResponseForbidden('Debug info pages disabled.', content_type='text/plain')

    script_prefix = get_script_prefix()

    env = []
    for key in sorted(os.environ.keys()):
        env.append( (key, os.environ[key]) )
    request_base_fields = []
    for attr in ['scheme', 'method', 'path', 'path_info', 'user', 'session', 'urlconf', 'resolver_match']:
        request_base_fields.append( (attr, getattr(request, attr) if hasattr(request, attr) else None) )
    t = Template(DEBUG_REQUEST_VIEW_TEMPLATE, name='Debug request template')
    c = Context({
        'request_path': request.path_info,
        'environment': env,
        'request': request,
        'request_base_fields': request_base_fields,
        'settings': get_safe_settings(),
        'script_prefix': script_prefix,
        'sys_executable': sys.executable,
        'sys_version_info': '%d.%d.%d' % sys.version_info[0:3],
        'server_time': datetime.datetime.now(),
        'django_version_info': get_version(),
        'sys_path': sys.path,
    })
    return HttpResponse(t.render(c), content_type='text/html')

def django_env_info_view(request):
    import datetime
    from django.http import HttpResponse, HttpResponseForbidden
    from django.template import Template, Context
    from django.core.urlresolvers import get_script_prefix
    from django import get_version

    script_prefix = get_script_prefix()

    env = []
    for key in sorted(os.environ.keys()):
        env.append( (key, os.environ[key]) )
    t = Template(DEBUG_ENV_VIEW_TEMPLATE, name='Debug environment template')
    c = Context({
        'request_path': request.path_info,
        'environment': env,
        'request': request,
        'settings': get_safe_settings(),
        'script_prefix': script_prefix,
        'sys_executable': sys.executable,
        'sys_version_info': '%d.%d.%d' % sys.version_info[0:3],
        'server_time': datetime.datetime.now(),
        'django_version_info': get_version(),
        'sys_path': sys.path,
    })
    return HttpResponse(t.render(c), content_type='text/html')

def django_settings_view(request):
    import datetime
    from django.conf import settings
    from django.http import HttpResponse, HttpResponseForbidden
    from django.template import Template, Context
    from django.utils.encoding import force_bytes, smart_text
    from django.core.urlresolvers import get_script_prefix
    from django import get_version

    disable = is_debug_info_disabled()
    if disable:
        return HttpResponseForbidden('Debug info pages disabled.', content_type='text/plain')

    script_prefix = get_script_prefix()

    urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
    if isinstance(urlconf, types.ModuleType):
        urlconf = urlconf.__name__

    t = Template(DEBUG_SETTINGS_VIEW_TEMPLATE, name='Debug settings template')
    c = Context({
        'urlconf': urlconf,
        'root_urlconf': settings.ROOT_URLCONF,
        'request_path': request.path_info,
        'reason': 'N/A',
        'request': request,
        'settings': get_safe_settings(),
        'script_prefix': script_prefix,
        'sys_executable': sys.executable,
        'sys_version_info': '%d.%d.%d' % sys.version_info[0:3],
        'server_time': datetime.datetime.now(),
        'django_version_info': get_version(),
        'sys_path': sys.path,
    })
    return HttpResponse(t.render(c), content_type='text/html')

class _url_pattern_wrapper(object):
    def __init__(self, url, parent, level):
        self.url = url
        self.parent = parent
        self.level = level

    def __getattr__(self, attr, default_value=None):
        if attr not in ['full_url', 'full_name', 'url', 'level', 'parent', 'typename', 'full_qualified_name']:
            return getattr(self.url, attr, default_value)
        else:
            return object.__getattribute__(self, attr)

    @property
    def typename(self):
        return str(type(self.url))

    @property
    def full_qualified_name(self):
        namespace = getattr(self.url, 'namespace', None)
        if namespace is None and self.parent is not None:
            namespace = getattr(self.parent, 'namespace', None)
        if namespace is not None:
            ret = namespace + ':' + self.url.name
        else:
            ret = self.url.name
        return ret

    @property
    def reverse_url(self):
        from django.core.urlresolvers import reverse, NoReverseMatch
        url = None
        try:
            url = reverse(self.full_qualified_name)
        except NoReverseMatch:
            pass
        return url

    @property
    def full_url(self):
        from django.core.urlresolvers import LocaleRegexProvider
        if isinstance(self.url, LocaleRegexProvider):
            ret = [ self.url.regex.pattern ]
        else:
            ret = [ self.url.name ]
        if self.parent is not None:
            ret.insert(0, self.parent.full_url)
        return ','.join(ret)

    @property
    def full_name(self):
        from django.core.urlresolvers import RegexURLResolver, RegexURLPattern
        if isinstance(self.url, RegexURLResolver):
            if isinstance(self.url.urlconf_name, list) and len(self.url.urlconf_name):
                # Don't bother to output the whole list, it can be huge
                urlconf_repr = '<%s list>' % self.url.urlconf_name[0].__class__.__name__
            else:
                urlconf_repr = repr(self.url.urlconf_name)
            ret = [ urlconf_repr ]
        elif isinstance(self.url, RegexURLPattern):
            ret = [ self.url.name ]
        else:
            ret = [ str(self.url) ]
        if self.parent is not None:
            ret.insert(0, self.parent.full_name)
        return '/'.join(ret)


def _flatten_url_list(obj, parent_obj=None, level=0):
    from django.core.urlresolvers import RegexURLResolver, RegexURLPattern
    ret = []
    wrapped_obj = _url_pattern_wrapper(obj, parent_obj, level)
    if isinstance(obj, RegexURLResolver):
        for p in obj.url_patterns:
            if hasattr(p, 'url_patterns'):
                r = _flatten_url_list(p, wrapped_obj, level=level+1)
                ret.extend(r)
            else:
                ret.append(_url_pattern_wrapper(p, wrapped_obj, level))
    elif isinstance(obj, list):
        for p in obj:
            if hasattr(p, 'url_patterns'):
                r = _flatten_url_list(p, wrapped_obj, level=level+1)
                ret.extend(r)
            else:
                ret.append(_url_pattern_wrapper(p, wrapped_obj, level))
    else:
        ret.append(wrapped_obj)
    return ret

def _flatten_url_dict(obj, parent_obj=None, level=0):
    from django.core.urlresolvers import RegexURLResolver, RegexURLPattern
    ret = {}
    wrapped_obj = _url_pattern_wrapper(obj, parent_obj, level)
    if isinstance(obj, RegexURLResolver):
        for p in obj.url_patterns:
            if hasattr(p, 'url_patterns'):
                r = _flatten_url_dict(p, wrapped_obj, level=level+1)
                ret.update(r)
            else:
                pobj = _url_pattern_wrapper(p, wrapped_obj, level)
                if pobj.full_qualified_name is not None:
                    ret[pobj.full_qualified_name] = pobj
    elif isinstance(obj, list):
        for p in obj:
            if hasattr(p, 'url_patterns'):
                r = _flatten_url_dict(p, wrapped_obj, level=level+1)
                ret.update(r)
            else:
                pobj = _url_pattern_wrapper(p, wrapped_obj, level)
                if pobj.full_qualified_name is not None:
                    ret[pobj.full_qualified_name] = pobj
    else:
        if wrapped_obj.full_qualified_name is not None:
            ret[wrapped_obj.full_qualified_name] = wrapped_obj
    return ret

def _sort_dict_by_key(d):
    def _sort_key(a):
        return a[0]
    ret = []
    for k,v in d.items():
        ret.append( (k, v) )
    return sorted(ret, key=_sort_key)

def django_urls_view(request):
    import datetime
    from django.conf import settings
    from django.http import HttpResponse, HttpResponseForbidden
    from django.template import Template, Context
    from django.utils.encoding import force_bytes, smart_text
    from django.core.urlresolvers import get_script_prefix, get_resolver
    from django import get_version

    disable = is_debug_info_disabled()
    if disable:
        return HttpResponseForbidden('Debug info pages disabled.', content_type='text/plain')

    script_prefix = get_script_prefix()

    urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
    if isinstance(urlconf, types.ModuleType):
        urlconf = urlconf.__name__
    resolver = get_resolver(None)

    t = Template(DEBUG_URLS_VIEW_TEMPLATE, name='Debug URL handlers template')
    c = Context({
        'urlconf': urlconf,
        'root_urlconf': settings.ROOT_URLCONF,
        'request_path': request.path_info,
        'urlpatterns': _flatten_url_list(resolver),
        'urlnames': _sort_dict_by_key(_flatten_url_dict(resolver)),
        'reason': 'N/A',
        'request': request,
        'settings': get_safe_settings(),
        'script_prefix': script_prefix,
        'sys_executable': sys.executable,
        'sys_version_info': '%d.%d.%d' % sys.version_info[0:3],
        'server_time': datetime.datetime.now(),
        'django_version_info': get_version(),
        'sys_path': sys.path,
    })
    return HttpResponse(t.render(c), content_type='text/html')

def django_debug_info(request):
    import datetime
    from django.conf import settings
    from django.http import HttpResponse, HttpResponseForbidden
    from django.template import Template, Context
    from django.utils.encoding import force_bytes, smart_text
    from django.core.urlresolvers import get_script_prefix, get_resolver
    from django import get_version

    disable = is_debug_info_disabled()
    if disable:
        return HttpResponseForbidden('Debug info pages disabled.', content_type='text/plain')

    script_prefix = get_script_prefix()

    urlpatterns = django_debug_urls()

    t = Template(DEBUG_INFO_VIEW_TEMPLATE, name='Debug Info template')
    c = Context({
        'request_path': request.path_info,
        'urlpatterns': urlpatterns,
        'reason': 'N/A',
        'request': request,
        'settings': get_safe_settings(),
        'script_prefix': script_prefix,
        'sys_executable': sys.executable,
        'sys_version_info': '%d.%d.%d' % sys.version_info[0:3],
        'server_time': datetime.datetime.now(),
        'django_version_info': get_version(),
        'sys_path': sys.path,
    })
    return HttpResponse(t.render(c), content_type='text/html')

def django_debug_urls(options={}):
    from django.conf.urls import url

    # add debug handler here
    urlpatterns = [
        url(r'^$', django_debug_info, name='debug_django_info'),
        url(r'^request$', django_request_info_view, name='debug_django_request'),
        url(r'^env$', django_env_info_view, name='debug_django_env'),
        url(r'^settings$', django_settings_view, name='debug_django_settings'),
        url(r'^urls$', django_urls_view, name='debug_django_urls'),
        ]
    return urlpatterns

DEBUG_INFO_VIEW_TEMPLATE = """
{% load base_url %}
{% load static_url %}
{% load media_url %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <title>Request information</title>
  <meta name="robots" content="NONE,NOARCHIVE">
  <style type="text/css">
    html * { padding:0; margin:0; }
    body * { padding:10px 20px; }
    body * * { padding:0; }
    body { font:small sans-serif; background:#eee; }
    body>div { border-bottom:1px solid #ddd; }
    h1 { font-weight:normal; margin-bottom:.4em; }
    h1 span { font-size:60%; color:#666; font-weight:normal; }
    h2 { margin-bottom:.8em; }
    h2 span { font-size:80%; color:#666; font-weight:normal; }
    h3 { margin:1em 0 .5em 0; }
    h4 { margin:0 0 .5em 0; font-weight: normal; }
    table { border:none; border-collapse: collapse; width:100%; }
    tr.settings { border-bottom: 1px solid #ccc; }
    tr.req { border-bottom: 1px solid #ccc; }
    td, th { vertical-align:top; padding:2px 3px; }
    th { width:12em; text-align:right; color:#666; padding-right:.5em; }
    th.settings { text-align:left; }
    th.req { text-align:left; }
    div { padding-bottom: 10px; }
    #info { background:#f6f6f6; }
    #info ol { margin: 0.5em 4em; }
    #info ol li { font-family: monospace; }
    #summary { background: #ffc; }
    #explanation { background:#eee; border-bottom: 0px none; }
  </style>
</head>
<body>
  <div id="summary">
    <h1>Available debug helpers</h1>
    <table class="meta">
      <tr>
        <th>Request Method:</th>
        <td>{{ request.META.REQUEST_METHOD }}</td>
      </tr>
      <tr>
        <th>Request URL:</th>
        <td>{{ request.build_absolute_uri|escape }}</td>
      </tr>
    <tr>
      <th>Script prefix:</th>
      <td><pre>{{ script_prefix|escape }}</pre></td>
    </tr>
    <tr>
      <th>Base URL:</th>
      <td><pre>{% base_url %}</pre></td>
    </tr>
    <tr>
      <th>Static URL:</th>
      <td><pre>{% static_url %}</pre></td>
    </tr>
    <tr>
      <th>Media URL:</th>
      <td><pre>{% media_url %}</pre></td>
    </tr>
      <tr>
        <th>Django Version:</th>
        <td>{{ django_version_info }}</td>
      </tr>
      <tr>
        <th>Python Version:</th>
        <td>{{ sys_version_info }}</td>
      </tr>
    <tr>
      <th>Python Executable:</th>
      <td>{{ sys_executable|escape }}</td>
    </tr>
    <tr>
      <th>Python Version:</th>
      <td>{{ sys_version_info }}</td>
    </tr>
    <tr>
      <th>Python Path:</th>
      <td><pre>{{ sys_path|pprint }}</pre></td>
    </tr>
    <tr>
      <th>Server time:</th>
      <td>{{server_time|date:"r"}}</td>
    </tr>
      <tr>
        <th>Installed Applications:</th>
        <td><ul>
          {% for item in settings.INSTALLED_APPS %}
            <li><code>{{ item }}</code></li>
          {% endfor %}
        </ul></td>
      </tr>
      <tr>
        <th>Installed Middleware:</th>
        <td><ul>
          {% for item in settings.MIDDLEWARE_CLASSES %}
            <li><code>{{ item }}</code></li>
          {% endfor %}
        </ul></td>
      </tr>
      <tr>
        <th>settings module:</th>
        <td><code>{{ settings.SETTINGS_MODULE }}</code></td>
      </tr>
    </table>
  </div>
  
  <div id="info">
      <ol>
        {% for pattern in urlpatterns %}
          <li>
            <a href="{% url pattern.name %}">{{ pattern.name }}</a> ({{ pattern.regex.pattern }})
          </li>
        {% endfor %}
      </ol>
  </div>

  <div id="explanation">
    <p>
      This page contains information to investigate issues with this web application.
    </p>
  </div>
</body>
</html>
"""

DEBUG_REQUEST_VIEW_TEMPLATE = """
{% load base_url %}
{% load static_url %}
{% load media_url %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <title>Request information</title>
  <meta name="robots" content="NONE,NOARCHIVE">
  <style type="text/css">
    html * { padding:0; margin:0; }
    body * { padding:10px 20px; }
    body * * { padding:0; }
    body { font:small sans-serif; background:#eee; }
    body>div { border-bottom:1px solid #ddd; }
    h1 { font-weight:normal; margin-bottom:.4em; }
    h1 span { font-size:60%; color:#666; font-weight:normal; }
    h2 { margin-bottom:.8em; }
    h2 span { font-size:80%; color:#666; font-weight:normal; }
    h3 { margin:1em 0 .5em 0; }
    h4 { margin:0 0 .5em 0; font-weight: normal; }
    table { border:none; border-collapse: collapse; width:100%; }
    tr.settings { border-bottom: 1px solid #ccc; }
    tr.req { border-bottom: 1px solid #ccc; }
    td, th { vertical-align:top; padding:2px 3px; }
    th { width:12em; text-align:right; color:#666; padding-right:.5em; }
    th.settings { text-align:left; }
    th.req { text-align:left; }
    div { padding-bottom: 10px; }
    #info { background:#f6f6f6; }
    #info ol { margin: 0.5em 4em; }
    #info ol li { font-family: monospace; }
    #summary { background: #ffc; }
    #explanation { background:#eee; border-bottom: 0px none; }
  </style>
</head>
<body>
  <div id="summary">
    <h1>Request information</h1>
    <table class="meta">
      <tr>
        <th>Request Method:</th>
        <td>{{ request.META.REQUEST_METHOD }}</td>
      </tr>
      <tr>
        <th>Request URL:</th>
        <td>{{ request.build_absolute_uri|escape }}</td>
      </tr>
    <tr>
      <th>Script prefix:</th>
      <td><pre>{{ script_prefix|escape }}</pre></td>
    </tr>
    <tr>
      <th>Base URL:</th>
      <td><pre>{% base_url %}</pre></td>
    </tr>
    <tr>
      <th>Static URL:</th>
      <td><pre>{% static_url %}</pre></td>
    </tr>
    <tr>
      <th>Media URL:</th>
      <td><pre>{% media_url %}</pre></td>
    </tr>
      <tr>
        <th>Django Version:</th>
        <td>{{ django_version_info }}</td>
      </tr>
      <tr>
        <th>Python Version:</th>
        <td>{{ sys_version_info }}</td>
      </tr>
    <tr>
      <th>Python Executable:</th>
      <td>{{ sys_executable|escape }}</td>
    </tr>
    <tr>
      <th>Python Version:</th>
      <td>{{ sys_version_info }}</td>
    </tr>
    <tr>
      <th>Python Path:</th>
      <td><pre>{{ sys_path|pprint }}</pre></td>
    </tr>
    <tr>
      <th>Server time:</th>
      <td>{{server_time|date:"r"}}</td>
    </tr>
      <tr>
        <th>Installed Applications:</th>
        <td><ul>
          {% for item in settings.INSTALLED_APPS %}
            <li><code>{{ item }}</code></li>
          {% endfor %}
        </ul></td>
      </tr>
      <tr>
        <th>Installed Middleware:</th>
        <td><ul>
          {% for item in settings.MIDDLEWARE_CLASSES %}
            <li><code>{{ item }}</code></li>
          {% endfor %}
        </ul></td>
      </tr>
      <tr>
        <th>settings module:</th>
        <td><code>{{ settings.SETTINGS_MODULE }}</code></td>
      </tr>
    </table>
  </div>

<div id="requestinfo">
  <h2>Request information</h2>

{% if request %}
  <h3 id="basic-info">base</h3>
    <table class="req">
      <thead>
        <tr class="req">
          <th class="req">Variable</th>
          <th class="req">Value</th>
        </tr>
      </thead>
      <tbody>
        {% for var in request_base_fields %}
          <tr class="req">
            <td>{{ var.0 }}</td>
            <td class="code"><pre>{{ var.1|pprint }}</pre></td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  


  <h3 id="get-info">GET</h3>
  {% if request.GET %}
    <table class="req">
      <thead>
        <tr class="req">
          <th class="req">Variable</th>
          <th class="req">Value</th>
        </tr>
      </thead>
      <tbody>
        {% for var in request.GET.items %}
          <tr class="req">
            <td>{{ var.0 }}</td>
            <td class="code"><pre>{{ var.1|pprint }}</pre></td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p>No GET data</p>
  {% endif %}

  <h3 id="post-info">POST</h3>
  {% if filtered_POST %}
    <table class="req">
      <thead>
        <tr class="req">
          <th class="req">Variable</th>
          <th class="req">Value</th>
        </tr>
      </thead>
      <tbody>
        {% for var in filtered_POST.items %}
          <tr class="req">
            <td>{{ var.0 }}</td>
            <td class="code"><pre>{{ var.1|pprint }}</pre></td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p>No POST data</p>
  {% endif %}
  <h3 id="files-info">FILES</h3>
  {% if request.FILES %}
    <table class="req">
        <thead>
            <tr class="req">
                <th class="req">Variable</th>
                <th class="req">Value</th>
            </tr>
        </thead>
        <tbody>
            {% for var in request.FILES.items %}
                <tr class="req">
                    <td>{{ var.0 }}</td>
                    <td class="code"><pre>{{ var.1|pprint }}</pre></td>
                </tr>
            {% endfor %}
        </tbody>
    </table>
  {% else %}
    <p>No FILES data</p>
  {% endif %}


  <h3 id="cookie-info">COOKIES</h3>
  {% if request.COOKIES %}
    <table class="req">
      <thead>
        <tr class="req">
          <th class="req">Variable</th>
          <th class="req">Value</th>
        </tr>
      </thead>
      <tbody>
        {% for var in request.COOKIES.items %}
          <tr class="req">
            <td>{{ var.0 }}</td>
            <td class="code"><pre>{{ var.1|pprint }}</pre></td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p>No cookie data</p>
  {% endif %}

  <h3 id="meta-info">META</h3>
  <table class="req">
    <thead>
      <tr class="req">
        <th class="req">Variable</th>
        <th class="req">Value</th>
      </tr>
    </thead>
    <tbody>
      {% for var in request.META.items|dictsort:"0" %}
        <tr class="req">
          <td>{{ var.0 }}</td>
          <td class="code"><pre>{{ var.1|pprint }}</pre></td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
{% else %}
  <p>Request data not supplied</p>
{% endif %}

  <div id="settings">
  <h3 id="settings">Settings</h3>
  <table class="settings">
    <thead>
      <tr>
        <th class="settings">Setting</th>
        <th class="settings">Value</th>
      </tr>
    </thead>
    <tbody>
      {% for var in settings.items|dictsort:"0" %}
        <tr class="settings">
          <td>{{ var.0 }}</td>
          <td class="code"><pre>{{ var.1|pprint }}</pre></td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
  </div>

  <div id="explanation">
    <p>
      This page contains information to investigate issues with this web application.
    </p>
  </div>
</body>
</html>
"""

DEBUG_ENV_VIEW_TEMPLATE = """
{% load base_url %}
{% load static_url %}
{% load media_url %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <title>Environment info</title>
  <meta name="robots" content="NONE,NOARCHIVE">
  <style type="text/css">
    html * { padding:0; margin:0; }
    body * { padding:10px 20px; }
    body * * { padding:0; }
    body { font:small sans-serif; background:#eee; }
    body>div { border-bottom:1px solid #ddd; }
    h1 { font-weight:normal; margin-bottom:.4em; }
    h1 span { font-size:60%; color:#666; font-weight:normal; }
    table { border:none; border-collapse: collapse; width:100%; }
    td, th { vertical-align:top; padding:2px 3px; }
    tr.env { border-bottom: 1px solid #ccc; }
    th { width:12em; text-align:right; color:#666; padding-right:.5em; }
    #info { background:#f6f6f6; }
    #info ol { margin: 0.5em 4em; }
    #info ol li { font-family: monospace; }
    #summary { background: #ffc; }
    #explanation { background:#eee; border-bottom: 0px none; }
  </style>
</head>
<body>
  <div id="summary">
    <h1>Environment info</h1>
    <table class="meta">
      <tr>
        <th>Request Method:</th>
        <td>{{ request.META.REQUEST_METHOD }}</td>
      </tr>
      <tr>
        <th>Request URL:</th>
        <td>{{ request.build_absolute_uri|escape }}</td>
      </tr>
    <tr>
      <th>Script prefix:</th>
      <td><pre>{{ script_prefix|escape }}</pre></td>
    </tr>
    <tr>
      <th>Base URL:</th>
      <td><pre>{% base_url %}</pre></td>
    </tr>
    <tr>
      <th>Static URL:</th>
      <td><pre>{% static_url %}</pre></td>
    </tr>
    <tr>
      <th>Media URL:</th>
      <td><pre>{% media_url %}</pre></td>
    </tr>
      <tr>
        <th>Django Version:</th>
        <td>{{ django_version_info }}</td>
      </tr>
      <tr>
        <th>Python Version:</th>
        <td>{{ sys_version_info }}</td>
      </tr>
    <tr>
      <th>Python Executable:</th>
      <td>{{ sys_executable|escape }}</td>
    </tr>
    <tr>
      <th>Python Version:</th>
      <td>{{ sys_version_info }}</td>
    </tr>
    <tr>
      <th>Python Path:</th>
      <td><pre>{{ sys_path|pprint }}</pre></td>
    </tr>
    <tr>
      <th>Server time:</th>
      <td>{{server_time|date:"r"}}</td>
    </tr>
      <tr>
        <th>Installed Applications:</th>
        <td><ul>
          {% for item in settings.INSTALLED_APPS %}
            <li><code>{{ item }}</code></li>
          {% endfor %}
        </ul></td>
      </tr>
      <tr>
        <th>Installed Middleware:</th>
        <td><ul>
          {% for item in settings.MIDDLEWARE_CLASSES %}
            <li><code>{{ item }}</code></li>
          {% endfor %}
        </ul></td>
      </tr>
      <tr>
        <th>settings module:</th>
        <td><code>{{ settings.SETTINGS_MODULE }}</code></td>
      </tr>
    </table>
  </div>
  <div id="info">
    {% if environment %}
       <table>
        {% for item in environment %}
          <tr class="env">
            <td>{{item.0|escape}}</td><td>{{item.1|escape}}</td>
          </tr>
        {% endfor %}
      </table>
    {% else %}
      <p>{{ reason }}</p>
    {% endif %}
  </div>

  <div id="explanation">
    <p>
      This page contains information to investigate issues with this web application.
    </p>
  </div>
</body>
</html>
"""

DEBUG_SETTINGS_VIEW_TEMPLATE = """
{% load base_url %}
{% load static_url %}
{% load media_url %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <title>Settings</title>
  <meta name="robots" content="NONE,NOARCHIVE">
  <style type="text/css">
    html * { padding:0; margin:0; }
    body * { padding:10px 20px; }
    body * * { padding:0; }
    body { font:small sans-serif; background:#eee; }
    body>div { border-bottom:1px solid #ddd; }
    h1 { font-weight:normal; margin-bottom:.4em; }
    h1 span { font-size:60%; color:#666; font-weight:normal; }
    table { border:none; border-collapse: collapse; width:100%; }
    tr.settings { border-bottom: 1px solid #ccc; }
    td, th { vertical-align:top; padding:2px 3px; }
    th { width:12em; text-align:right; color:#666; padding-right:.5em; }
    th.settings { text-align:left; }
    #info { background:#f6f6f6; }
    #info ol { margin: 0.5em 4em; }
    #info ol li { font-family: monospace; }
    #summary { background: #ffc; }
    #explanation { background:#eee; border-bottom: 0px none; }
  </style>
</head>
<body>
  <div id="summary">
    <h1>Settings</h1>
    <table class="meta">
      <tr>
        <th>Request Method:</th>
        <td>{{ request.META.REQUEST_METHOD }}</td>
      </tr>
      <tr>
        <th>Request URL:</th>
        <td>{{ request.build_absolute_uri|escape }}</td>
      </tr>
    <tr>
      <th>Script prefix:</th>
      <td><pre>{{ script_prefix|escape }}</pre></td>
    </tr>
    <tr>
      <th>Base URL:</th>
      <td><pre>{% base_url %}</pre></td>
    </tr>
    <tr>
      <th>Static URL:</th>
      <td><pre>{% static_url %}</pre></td>
    </tr>
    <tr>
      <th>Media URL:</th>
      <td><pre>{% media_url %}</pre></td>
    </tr>
      <tr>
        <th>Django Version:</th>
        <td>{{ django_version_info }}</td>
      </tr>
      <tr>
        <th>Python Version:</th>
        <td>{{ sys_version_info }}</td>
      </tr>
    <tr>
      <th>Python Executable:</th>
      <td>{{ sys_executable|escape }}</td>
    </tr>
    <tr>
      <th>Python Version:</th>
      <td>{{ sys_version_info }}</td>
    </tr>
    <tr>
      <th>Python Path:</th>
      <td><pre>{{ sys_path|pprint }}</pre></td>
    </tr>
    <tr>
      <th>Server time:</th>
      <td>{{server_time|date:"r"}}</td>
    </tr>
      <tr>
        <th>Installed Applications:</th>
        <td><ul>
          {% for item in settings.INSTALLED_APPS %}
            <li><code>{{ item }}</code></li>
          {% endfor %}
        </ul></td>
      </tr>
      <tr>
        <th>Installed Middleware:</th>
        <td><ul>
          {% for item in settings.MIDDLEWARE_CLASSES %}
            <li><code>{{ item }}</code></li>
          {% endfor %}
        </ul></td>
      </tr>
      <tr>
        <th>settings module:</th>
        <td><code>{{ settings.SETTINGS_MODULE }}</code></td>
      </tr>
    </table>
  </div>
  
  <div id="info">
  <table class="settings">
    <thead>
      <tr>
        <th class="settings">Setting</th>
        <th class="settings">Value</th>
      </tr>
    </thead>
    <tbody>
      {% for var in settings.items|dictsort:"0" %}
        <tr class="settings">
          <td>{{ var.0 }}</td>
          <td class="code"><pre>{{ var.1|pprint }}</pre></td>
        </tr>
      {% endfor %}
    </tbody>
  </table>  
  </div>

  <div id="explanation">
    <p>
      This page contains information to investigate issues with this web application.
    </p>
  </div>
</body>
</html>
"""

DEBUG_URLS_VIEW_TEMPLATE = """
{% load type %}
{% load base_url %}
{% load static_url %}
{% load media_url %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <title>URL handler info</title>
  <meta name="robots" content="NONE,NOARCHIVE">
  <style type="text/css">
    html * { padding:0; margin:0; }
    body * { padding:10px 20px; }
    body * * { padding:0; }
    body { font:small sans-serif; background:#eee; }
    body>div { border-bottom:1px solid #ddd; }
    h1 { font-weight:normal; margin-bottom:.4em; }
    h1 span { font-size:60%; color:#666; font-weight:normal; }
    table { border:none; border-collapse: collapse; width:100%; }
    td, th { vertical-align:top; padding:2px 3px; }
    th { width:12em; text-align:right; color:#666; padding-right:.5em; }
    #info { background:#f6f6f6; }
    #info ol { margin: 0.5em 4em; }
    #info ol li { font-family: monospace; }
    #summary { background: #ffc; }
    #explanation { background:#eee; border-bottom: 0px none; }
  </style>
</head>
<body>
  <div id="summary">
    <h1>URL handler info</h1>
    <table class="meta">
      <tr>
        <th>Request Method:</th>
        <td>{{ request.META.REQUEST_METHOD }}</td>
      </tr>
      <tr>
        <th>Request URL:</th>
        <td>{{ request.build_absolute_uri|escape }}</td>
      </tr>
    <tr>
      <th>Script prefix:</th>
      <td><pre>{{ script_prefix|escape }}</pre></td>
    </tr>
    <tr>
      <th>Base URL:</th>
      <td><pre>{% base_url %}</pre></td>
    </tr>
    <tr>
      <th>Static URL:</th>
      <td><pre>{% static_url %}</pre></td>
    </tr>
    <tr>
      <th>Media URL:</th>
      <td><pre>{% media_url %}</pre></td>
    </tr>
    <tr>
      <th>URLconf:</th>
      <td><pre>{{ urlconf }}</pre></td>
    </tr>
      <tr>
        <th>Django Version:</th>
        <td>{{ django_version_info }}</td>
      </tr>
      <tr>
        <th>Python Version:</th>
        <td>{{ sys_version_info }}</td>
      </tr>
    <tr>
      <th>Python Executable:</th>
      <td>{{ sys_executable|escape }}</td>
    </tr>
    <tr>
      <th>Python Version:</th>
      <td>{{ sys_version_info }}</td>
    </tr>
    <tr>
      <th>Python Path:</th>
      <td><pre>{{ sys_path|pprint }}</pre></td>
    </tr>
    <tr>
      <th>Server time:</th>
      <td>{{server_time|date:"r"}}</td>
    </tr>
      <tr>
        <th>Installed Applications:</th>
        <td><ul>
          {% for item in settings.INSTALLED_APPS %}
            <li><code>{{ item }}</code></li>
          {% endfor %}
        </ul></td>
      </tr>
      <tr>
        <th>Installed Middleware:</th>
        <td><ul>
          {% for item in settings.MIDDLEWARE_CLASSES %}
            <li><code>{{ item }}</code></li>
          {% endfor %}
        </ul></td>
      </tr>
      <tr>
        <th>settings module:</th>
        <td><code>{{ settings.SETTINGS_MODULE }}</code></td>
      </tr>
    </table>
  </div>
  <div id="info">
    <p>
    Available URL patterns:
    </p>
    <ul>
    {% for pattern in urlpatterns %}
        <li style="margin-left:{% widthratio pattern.level 1 16 %}px;">
        {{ pattern.full_url}}
        {% if pattern.full_name.strip %}&nbsp;[{% url pattern.name as the_url %}{% if the_url %}<a href="{{the_url}}">{% endif %}name='{{pattern.name}}'{% if the_url %}</a>{% endif %}]
        {% endif %}
        {% if pattern.namespace %}&nbsp;[namespace='{{pattern.namespace}}']{% endif %}
        {% if pattern.name.default_args %}&nbsp;[args='{{pattern.default_args|join:", "}}']{% endif %}
        &nbsp;({{pattern.url|type}})
        </li>
    {% endfor %}
    </ul>
    <p>
    Available URL names:
    </p>
    <ul>
    {% for full_qualified_name, pattern in urlnames %}
        <li>
        {{full_qualified_name}}
        {% if pattern.reverse_url %}&nbsp;<a href="{{ pattern.reverse_url }}">{{ pattern.reverse_url }}</a>{% endif %}
        {% if pattern.name.default_args %}&nbsp;[args='{{pattern.default_args|join:", "}}']{% endif %}
        &nbsp;({{pattern.url|type}})
        </li>
    {% endfor %}
    </ul>
  </div>

  <div id="explanation">
    <p>
      This page contains information to investigate issues with this web application.
    </p>
  </div>
</body>
</html>
"""
