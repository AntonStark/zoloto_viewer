from zoloto_viewer.config.settings.common import *
from zoloto_viewer.config import sentry

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'vh2)6un#nhgh%ytl^%edf7=n^ihkc0$nl5o)6*+$(4sv@lu_61'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

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

MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/var/www/zoloto_viewer/media/')
MEDIA_URL = '/media/'

BASE_URL = f'http://localhost:8000'

AWS_STORAGE_BUCKET_NAME = 'zoloto-viewer-dev'
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

AWS_HEADERS = {
    'Cache-Control': 'max-age=%d, s-maxage=%d, must-revalidate' % (AWS_EXPIREY, AWS_EXPIREY)
}
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_LOCATION = 'static'

STATICFILES_STORAGE = 'zoloto_viewer.config.settings.storage_backends.S3StaticStorage'
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_LOCATION)

DEFAULT_FILE_STORAGE = 'zoloto_viewer.config.settings.storage_backends.S3MediaStorage'

SENTRY_DSN = 'https://d4fe35ed88c04fc4b404de8cc3a4765a@o578628.ingest.sentry.io/5734971'
sentry.init(SENTRY_DSN)
