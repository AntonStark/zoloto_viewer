import boto3
import io
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage   # noqa


class S3MediaStorage(S3Boto3Storage):
    location = 'media/public'
    file_overwrite = False


class S3StaticStorage(S3Boto3Storage):
    location = settings.AWS_LOCATION


def s3_download_bytes(name):
    buf = io.BytesIO()
    s3 = boto3.client('s3')
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    bucket_location = S3MediaStorage.location
    s3.download_fileobj(bucket_name, f'{bucket_location}/{name}', buf)
    buf.seek(0)
    return buf
