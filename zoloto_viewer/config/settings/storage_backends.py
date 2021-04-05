import boto3
import io
from storages.backends.s3boto3 import setting, S3Boto3Storage   # noqa


class S3MediaStorage(S3Boto3Storage):
    location = 'media/private'
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False


def s3_download_bytes(name):
    buf = io.BytesIO()
    s3 = boto3.client('s3')
    bucket_name = setting('AWS_STORAGE_BUCKET_NAME')
    bucket_location = S3MediaStorage.location
    s3.download_fileobj(bucket_name, f'{bucket_location}/{name}', buf)
    buf.seek(0)
    return buf
