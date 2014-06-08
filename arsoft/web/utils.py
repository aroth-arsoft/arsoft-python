#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
import sys
import os.path

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

def initialize_settings(settings_module, setttings_file):
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
    else:
        settings_obj.BASE_PATH = ''

    #print('initialize_settings for ' + appname + ' appdir ' + appdir + ' debug=' + str(in_devserver) + ' basepath=' + str(settings_obj.BASE_PATH))

    settings_obj.DEBUG = in_devserver
    settings_obj.TEMPLATE_DEBUG = settings_obj.DEBUG

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
    settings_obj.MEDIA_ROOT = ''

    # URL that handles the media served from MEDIA_ROOT. Make sure to use a
    # trailing slash.
    # Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
    settings_obj.MEDIA_URL = settings_obj.BASE_PATH + '/media/'

    settings_obj.ROOT_URLCONF = appname + '.urls'

    # Python dotted path to the WSGI application used by Django's runserver.
    settings_obj.WSGI_APPLICATION = appname + '.wsgi.application'

    settings_obj.SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

    settings_obj.MIDDLEWARE_CLASSES = [
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ]

    settings_obj.AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
    
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
    if in_devserver:
        app_template_dir = os.path.join(appdir, 'templates')
        if os.path.exists(app_template_dir):
            settings_obj.TEMPLATE_DIRS = [ app_template_dir ]
        else:
            settings_obj.TEMPLATE_DIRS = []
    else:
        settings_obj.TEMPLATE_DIRS = [ os.path.join(app_etc_dir, 'templates') ]
    # always include the app_directories loader to get templates from various applications
    # working (e.g. admin)
    settings_obj.TEMPLATE_LOADERS = [ 'django.template.loaders.filesystem.Loader', 'django.template.loaders.app_directories.Loader' ]

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
                    'class': 'django.utils.log.NullHandler',
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
                    'handlers': ['mail_admins', 'logfile'],
                    'level': 'ERROR',
                    'propagate': True,
                },
                # Might as well log any errors anywhere else in Django
                'django': {
                    'handlers': ['logfile'],
                    'level': 'ERROR',
                    'propagate': True,
                },
                appname: {
                    'handlers': ['console', 'logfile'],
                    'level': 'DEBUG',
                    'propagate': True,
                },
            }
        }

    custom_settings_file = os.path.join(settings_obj.CONFIG_DIR, 'settings.py')
    #print(custom_settings_file)
    if os.path.exists(custom_settings_file):
        exec(compile(open(custom_settings_file).read(), custom_settings_file, 'exec'))

    #print(settings_obj.INSTALLED_APPS)

def _django_request_info_view_dict(request, dict_name):
    from django.utils.html import escape
    ret = ''
    if hasattr(request, dict_name):
        ret += '<h1>%s</h1>' % dict_name
        d = getattr(request, dict_name)
        if isinstance(d, dict):
            d_keys = sorted(d.keys())
            ret += '<table border=\'1\'>'
            for key in d_keys:
                value = d[key]
                ret += '<tr><td>%s</td><td>%s</td></tr>' % (escape(str(key)), escape(str(value)))
            ret += '</table>'
        else:
            ret += '<pre>%s</pre>' % (escape(str(d)))
    else:
        ret += '<h1>%s (not available)</h1>' % dict_name
    return ret

def _django_request_info_view_impl(request, attr_names):
    from django.utils.html import escape
    ret = ''
    ret += '<table border=\'1\'>\n'
    for attr in attr_names:
        ret += '<tr><td>%s</td><td>\n' % escape(str(attr))

        if hasattr(request, attr):
            d = getattr(request, attr)
            if isinstance(d, dict):
                d_keys = sorted(d.keys())
                if d_keys:
                    ret += '<table border=\'1\'>\n'
                    for key in d_keys:
                        value = d[key]
                        ret += '<tr><td>%s</td><td>%s</td></tr>\n' % (escape(str(key)), escape(str(value)))
                    ret += '</table>\n'
                else:
                    ret += '<i>empty</o>\n'
            else:
                ret += '<pre>%s (%s)</pre>\n' % (escape(str(d)), escape(str(type(d))))
        else:
            ret += 'NA'
        ret += '</td></tr>\n'
    ret += '</table>\n'
    return ret

def django_request_info_view(request):
    from django.http import HttpResponse
    body = ''
    body += '<html><head><style>\n'
    body += 'table { border-collapse:collapse; vertical-align:top; }\n'
    body += 'tr, th, td, tbody {\n'
    body += 'border-style: inherit;\n'
    body += 'border-color: inherit;\n'
    body += 'border-width: inherit;\n'
    body += 'text-align: left;\n'
    body += 'vertical-align: top;\n'
    body += 'padding:1px 3px 1px 3px;\n'
    body += '}\n'
    body += '</style></head>\n'
    body += _django_request_info_view_impl(request, ['META', 'GET', 'POST', 'REQUEST', 'FILES', 'COOKIES',
                                                     'scheme', 'method', 'path', 'path_info', 'user', 'session', 'urlconf'])
    body += '</html>\n'
    return HttpResponse(body, content_type='text/html')

def django_debug_urls(urls_module, urls_file):
    from django.conf.urls import patterns, include, url

    urls_module_obj = sys.modules[urls_module]
    urls_module_obj_type = type(urls_module_obj)

    # add debug handler here
    urls_module_obj.urlpatterns.append(url(r'^debug/request$', 'arsoft.web.utils.django_request_info_view', name='django_request'))
