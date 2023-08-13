import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from transactions.models import Coupon
from datetime import date


_IMAGE_URI = 'https://github.githubassets.com/images/modules/' \
    + 'site/home/globe.jpg?width=619'

_ACCOUNTLESS_TRANSACTION_INFO = {
    'buyer_name': 'John',
    'buyer_lastname': 'Wick',
    'phone_number': '+56911111111',
    'email': 'jw@email.com',
    'region': 'RegionTest',
    'commune': 'CommuneTest',
    'address': 'AddressTest'
}


@pytest.fixture(scope="module")
def address_creation_info():
    return {
        'region': 'RegionTest',
        'commune': 'CommuneTest',
        'address': 'AddressTest'
    }


@pytest.fixture(scope="module")
def category_creation_info():
    return {'name': 'categorytest'}


@pytest.fixture(scope="module")
def category_photo_file():
    return SimpleUploadedFile('test.jpg', b'img_data')


@pytest.fixture(scope="module")
def publication_creation_info():
    return {
        "publication_items": [{
            "size": "XL",
            "color": "azul",
            "sku": 222,
            "amount": 3
        }],
        "price": 25000,
        "item_name": "Jockey",
        "item_brand": "adidas",
        "item_category_id": 1,
        "description": "Test description"
    }


@pytest.fixture(scope="module")
def publication_get_info():
    return {
        "id": 1,
        "seller": 1,
        "photo_uris": [_IMAGE_URI],
        "price": 25000,
        "publication_items": [{
            "id": 1,
            "publication": 1,
            "item": {
                "id": 1,
                "name": "jockey",
                "brand": "adidas",
                "size": "xl",
                "color": "azul",
                "sku": 222,
                "category": {
                    "id": 1,
                    "name": "categorytest"
                },
            },
            "available": 3
        }],
        "description": "Test description",
        "is_active": False,
        "is_accepted": False,
        "publish_date": date.today().strftime("%Y-%m-%d")
    }


@pytest.fixture(scope="module")
def publication_photo_file():
    return MultiValueDict({
        'files': [SimpleUploadedFile('test.jpg', b'img_data')]
    })


@pytest.fixture(scope="module")
def correct_accountless_transaction_creation_info():
    return _ACCOUNTLESS_TRANSACTION_INFO | {
        'publication_items_list': [{'id': 1, 'amount': 2}]
    }


@pytest.fixture(scope="module")
def wrong_accountless_transaction_creation_info():
    return _ACCOUNTLESS_TRANSACTION_INFO | {
        'publication_items_list': [{'id': 1, 'amount': 4}]
    }


@pytest.fixture(scope="module")
def coupon_creation_info():
    return {
        'name': 'CouponTest',
        'code': 'CodeTest',
        'discount_percentage': 10.5
    }


@pytest.fixture(scope="module")
def coupon_get_info(coupon_creation_info):
    return coupon_creation_info | {'id': 1, 'active': True}


@pytest.fixture(scope='function')
def generate_coupon_permissions() -> None:
    coupon_permission = Permission.objects.create(
        id=2000,
        codename='can_manage_coupon',
        name='Can create coupon',
        content_type=ContentType.objects.get_for_model(Coupon)
    )
    admin_group = Group.objects.create(name='Admin')
    admin_group.permissions.add(coupon_permission)
