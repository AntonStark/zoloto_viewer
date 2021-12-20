from zoloto_viewer.config.settings.common import *
from zoloto_viewer.config import sentry

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'vh2)6un#nhgh%ytl^%edf7=n^ihkc0$nl5o)6*+$(4sv@lu_61'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

INSTALLED_APPS = INSTALLED_APPS + INSTALLED_APPS_DEV

MIDDLEWARE = MIDDLEWARE_DEV + MIDDLEWARE

ALLOWED_HOSTS = ['*']

INTERNAL_IPS = [
    '127.0.0.1',
]

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'zoloto_viewer'),
        'USER': os.getenv('POSTGRES_USER', 'zoloto_viewer'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'kebfa2b'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', 5432)
    }
}

REDIS_URL = os.getenv('REDIS_URL')

MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/var/www/zoloto_viewer/media/')
MEDIA_URL = '/media/'

BASE_URL = f'http://localhost:8000'

AWS_STORAGE_BUCKET_NAME = 'zoloto-viewer-dev'
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

AWS_EXPIREY = 1 * 24 * 60 * 60
AWS_HEADERS = {
    'Cache-Control': 'max-age=%d, s-maxage=%d, must-revalidate' % (AWS_EXPIREY, AWS_EXPIREY)
}
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_LOCATION = 'static'
AWS_DEFAULT_ACL = 'public-read'

# STATICFILES_STORAGE = 'zoloto_viewer.config.settings.storage_backends.S3StaticStorage'
# STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_LOCATION)
STATIC_URL = '/static/'

DEFAULT_FILE_STORAGE = 'zoloto_viewer.config.settings.storage_backends.S3MediaStorage'

SENTRY_DSN = 'https://d4fe35ed88c04fc4b404de8cc3a4765a@o578628.ingest.sentry.io/5734971'
sentry.init(SENTRY_DSN)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'zoloto_viewer.documents.pdf_generation.plan_page_writer': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'zoloto_viewer.documents.pdf_generation.plan': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    }
}
