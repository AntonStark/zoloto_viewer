import os

from zoloto_viewer.config.settings.common import *
from zoloto_viewer.config import sentry

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS').split(' ')

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': heroku_database_url_adapter(os.getenv('DATABASE_URL')),
}

MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')
MEDIA_URL = '/viewer/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'zoloto_viewer.config.settings.storage_backends.S3StaticStorage'

# fixme after enable ssl
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

X_FRAME_OPTIONS = 'DENY'

# for api calls
BASE_URL = 'https://https://zoloto-viewer.herokuapp.com'


AWS_STORAGE_BUCKET_NAME = 'zoloto-viewer'
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

AWS_EXPIREY = 1 * 24 * 60 * 60
AWS_HEADERS = {
    'Cache-Control': 'max-age=%d, s-maxage=%d, must-revalidate' % (AWS_EXPIREY, AWS_EXPIREY)
}
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=%d' % AWS_EXPIREY,
}
AWS_LOCATION = 'static'

STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_LOCATION)

DEFAULT_FILE_STORAGE = 'zoloto_viewer.config.settings.storage_backends.S3MediaStorage'

SENTRY_DSN = os.getenv('SENTRY_DSN')
sentry.init(SENTRY_DSN)
