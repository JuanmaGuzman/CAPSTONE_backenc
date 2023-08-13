import pytest
from unittest.mock import Mock, patch
import json


_IMAGE_URI = 'https://github.githubassets.com/images/modules/' \
    + 'site/home/globe.jpg?width=619'


mock_send_payment_intent = Mock()
mock_send_payment_intent.side_effect = [
    {f'pmntid{i}', f'wdgttk1{i}'}
    for i in range(20)
]


@pytest.fixture(scope="function")
def publication_set_creation_info():
    return (
        {
            "publication_items": [{
                "size": "m",
                "color": "Color1",
                "sku": 1,
                "amount": 3
            }],
            "price": 25000,
            "item_name": "Item1",
            "item_brand": "Brand1",
            "item_category_id": 1,
            "description": "Test description",
        }, {
            "publication_items": [{
                "size": "42",
                "color": "Color2",
                "sku": 2,
                "amount": 3
            }],
            "price": 25000,
            "item_name": "Item2",
            "item_brand": "Brand2",
            "item_category_id": 1,
            "description": "Test description",
        }, {
            "publication_items": [{
                "size": "44",
                "color": "Color3",
                "sku": 3,
                "amount": 0
            }],
            "price": 25000,
            "item_name": "Item3",
            "item_brand": "Brand3",
            "item_category_id": 1,
            "description": "Test description",
        }, {
            "publication_items": [{
                "size": "",
                "color": "Color4",
                "sku": 4,
                "amount": 3
            }],
            "price": 25000,
            "item_name": "Item4",
            "item_brand": "Brand4",
            "item_category_id": 1,
            "description": "Test description",
        }, {
            "publication_items": [{
                "size": "",
                "color": "Color5",
                "sku": 5,
                "amount": 3
            }],
            "price": 25000,
            "item_name": "Item5",
            "item_brand": "Brand5",
            "item_category_id": 1,
            "description": "Test description",
        }
    )


@pytest.fixture(scope="function")
def publication_recommendation_get_info():
    return [
        {
            "id": 1,
            "seller": 1,
            "price": 25000.0,
            "general_item_info": {
                "name": "item1",
                "brand": "brand1",
                "category": {
                    "id": 1,
                    "name": "categorytest",
                    "image_uri": _IMAGE_URI
                },
                "total_amount": 2
            },
            "photo_uris": [_IMAGE_URI]
        }, {
            "id": 2,
            "seller": 1,
            "price": 25000.0,
            "general_item_info": {
                "name": "item2",
                "brand": "brand2",
                "category": {
                    "id": 1,
                    "name": "categorytest",
                    "image_uri": _IMAGE_URI
                },
                "total_amount": 3
            },
            "photo_uris": [_IMAGE_URI]
        }, {
            "id": 4,
            "seller": 1,
            "price": 25000.0,
            "general_item_info": {
                "name": "item4",
                "brand": "brand4",
                "category": {
                    "id": 1,
                    "name": "categorytest",
                    "image_uri": _IMAGE_URI
                },
                "total_amount": 2
            },
            "photo_uris": [_IMAGE_URI]
        }
    ]


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@patch(
    'transactions.api.transactions.send_payment_intent',
    new=mock_send_payment_intent
)
def test_get_recommendation(
    ninja_client,
    super_user,
    user_one,
    user_one_creation_info,
    address_creation_info,
    publication_set_creation_info,
    publication_photo_file,
    publication_recommendation_get_info,
    category_creation_info,
    category_photo_file,
    generate_seller_permissions
):
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    ninja_client.post(
        '/user_profiles/user_profiles/shipping_address',
        json=address_creation_info,
        user=user_one
    )
    # give the user seller permissions
    ninja_client.patch(
        '/user_profiles/permissions/assign_seller/1',
        user=super_user
    )
    # create category
    assert ninja_client.post(
        '/publications/categories/create',
        data={
            'body': json.dumps(category_creation_info),
        },
        FILES={'file': category_photo_file},
        user=super_user
    ).status_code == 200
    # Create publications
    for i, pub_info in enumerate(publication_set_creation_info):
        assert ninja_client.post(
            '/publications/publications/create',
            data={
                'body': json.dumps(pub_info),
            },
            FILES=publication_photo_file,
            user=user_one
        ).status_code == 201
        assert ninja_client.patch(
            f'/publications/publications/accept/{i + 1}',
            user=super_user
        ).status_code == 200
    # add publication to user cart
    assert ninja_client.post(
        '/publications/shopping_cart/add_to_cart/1',
        json={'amount': 1},
        user=user_one
    ).status_code == 200
    assert ninja_client.post(
        '/publications/shopping_cart/add_to_cart/4',
        json={'amount': 1},
        user=user_one
    ).status_code == 200
    # create transaction
    assert ninja_client.post(
        '/transactions/transactions/create/',
        json={'shipping_address_id': 1},
        user=user_one
    ).status_code == 200
    # Get recommendations
    response = ninja_client.get(
        '/publications/publications/recommendations?amount=3',
        user=user_one
    )
    assert response.json() == publication_recommendation_get_info
