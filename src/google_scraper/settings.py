import os

import djcelery

from django.contrib import messages

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'l$@_+jn!@s%ko1p(ju+i9-4pv7+cmm=03niwwr()(+ad@%aa0#'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django_admin_bootstrapped',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'debug_toolbar',
    'djcelery',
    'import_export',
    'scraper',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'google_scraper.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'google_scraper.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'google_scraper_db',
        'USER': 'google_scraper_user',
        'PASSWORD': '=mTY4Ct/u4*-wHX&',
        'HOST': 'localhost',
        'PORT': '',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilari'
        'tyValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidato'
        'r',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidat'
        'or',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValida'
        'tor',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

DAB_FIELD_RENDERER = 'django_admin_bootstrapped.renderers.BootstrapFieldRende'\
    'rer'

MESSAGE_TAGS = {
            messages.SUCCESS: 'alert-success success',
            messages.WARNING: 'alert-warning warning',
            messages.ERROR: 'alert-danger error'
}

BROKER_URL = 'redis://localhost:6379/0'

CELERY_SEND_EVENTS = True

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

CELERY_ROUTES = {
    'scraper.tasks._online_check_task': {'queue': 'google_scraper'},
    'scraper.tasks._google_ban_check_task': {'queue': 'google_scraper'},
    'scraper.tasks._search_task': {'queue': 'google_scraper'},
    'scraper.tasks.online_check_task': {'queue': 'google_scraper'},
    'scraper.tasks.google_ban_check_task': {'queue': 'google_scraper'},
    'scraper.tasks.search_task': {'queue': 'google_scraper'}
}

djcelery.setup_loader()

USE_PROXY = False

PROXY_TIMEOUT = 10

REQUEST_TIMEOUT = 60

MIN_REQUEST_SLEEP = 10

MAX_REQUEST_SLEEP = 60

MIN_RETRY_SLEEP = 10

MAX_RETRY_SLEEP = 60

MAX_RETRY = 3

MAX_PAGE = 3

RESULT_PER_PAGE = 10
