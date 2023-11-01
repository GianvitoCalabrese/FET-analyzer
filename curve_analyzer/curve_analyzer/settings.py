import os
from django.core.management.utils import get_random_secret_key

SECRET_KEY = get_random_secret_key()
DEBUG = True
BASE_DIR = 'C:/Users/gcalabre/GitHub/FET-analyzer/curve_analyzer/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR + '\\db.sqlite3',
    }
}

INSTALLED_APPS = [
    # ...
    'curve_app',
    'django.contrib.staticfiles',
    # ...
]

# ...



TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'curve_app/templates')],
        'APP_DIRS': True,
        # ...
    },
    # ...
]

# ...

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
ROOT_URLCONF = 'curve_analyzer.urls'
#STATIC_ROOT = 'curve_app/static/'
STATIC_ROOT = 'C:/Users/gcalabre/GitHub/FET-analyzer/curve_analyzer/curve_app/static'


STATIC_URL = '/static/'
STATICFILES_DIRS = ['C:/Users/gcalabre/GitHub/FET-analyzer/curve_analyzer/curve_app/',]
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
