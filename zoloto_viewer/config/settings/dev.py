from zoloto_viewer.config.settings.common import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'vh2)6un#nhgh%ytl^%edf7=n^ihkc0$nl5o)6*+$(4sv@lu_61'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'zoloto_viewer'),
        'USER': os.getenv('POSTGRES_USER', 'zoloto_viewer'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'sd13rb2o'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', 5432)
    }
}

MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/var/www/zoloto_viewer/media/')
MEDIA_URL = '/media/'

STATIC_URL = '/static/'

# for api calls
BASE_URL = 'http://localhost:8000'
