"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 3.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'zoloto_viewer.viewer',     # todo rename to project_creator before full DB clean up
    'zoloto_viewer.infoplan',
    'zoloto_viewer.documents',
    'fontawesome-free',
    'storages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'zoloto_viewer.config.urls'

APPEND_SLASH = True


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

WSGI_APPLICATION = 'zoloto_viewer.config.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'auth.User'

LOGIN_URL = '/viewer/accounts/login/'


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    '/var/www/zoloto_viewer/static/',
]


def heroku_database_url_adapter(url: str):
    """
    :param url: str - database url
    postgres://hxqrxtamhjraxm:facb52c95d37ed447e3a7333467cc7c0d49f5dc7bcd4836d9fbae66d79833e6a@ec2-54-72-155-238.eu-west-1.compute.amazonaws.com:5432/d8smb1guvac85k
    :return: dict with following schema
        {
            'ENGINE':
            'NAME':
            'USER':
            'PASSWORD':
            'HOST':
            'PORT':
        }
    """
    import re, operator

    pattern = r'^(?P<scheme>\w+)://(?P<user>\w+):(?P<password>\w+)@(?P<host>[\w\-.]+):(?P<port>\d+)/(?P<name>\w+)$'
    r = re.match(pattern, url)

    keys = 'user', 'password', 'host', 'port', 'name'
    values = operator.itemgetter(keys)(r)
    res = {str.upper(k): v
           for k, v in zip(keys, values)}

    engine = 'django.db.backends.postgresql'
    res['ENGINE'] = engine
    return res
