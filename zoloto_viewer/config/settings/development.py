import os

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

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
        'NAME': 'zoloto_viewer',
        'USER': 'zoloto_viewer',
        'PASSWORD': 'sd13rb2o',
        'HOST': 'localhost',
        'PORT': 5432
    }
}
