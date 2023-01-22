import pytest
from django.test import TestCase

# Create your tests here.
from zoloto_viewer.viewer.models import (
    Page,
    Project,
)


@pytest.fixture
def big_jpg_file():
    file_path = '/Users/anton/Downloads/IMG_8247.JPG'
    return open(file_path, 'rb')


@pytest.mark.django_db
def test_page_create_or_replace(big_jpg_file):
    project = Project()
    page = Page.create_or_replace(project, big_jpg_file, '', '')

