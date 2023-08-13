import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from publications.models import Publication


@pytest.fixture(scope="module")
def category_creation_info():
    return {'name': 'categorytest'}


@pytest.fixture(scope="module")
def publication_photo_file():
    return MultiValueDict({
        'files': [SimpleUploadedFile('test.jpg', b'img_data')]
    })


@pytest.fixture(scope="module")
def category_photo_file():
    return SimpleUploadedFile('test.jpg', b'img_data')


@pytest.fixture(scope="function")
def generate_seller_permissions() -> None:
    seller_group, _ = Group.objects.get_or_create(name='Seller')
    pub_permission, _ = Permission.objects.get_or_create(
        id=1000,
        codename='can_create',
        name='Can create publication',
        content_type=ContentType.objects.get_for_model(Publication)
    )
    seller_group.permissions.add(pub_permission)
