import pytest
import json
from copy import deepcopy
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict


_IMAGE_URI = 'https://github.githubassets.com/images/modules/' \
    + 'site/home/globe.jpg?width=619'


@pytest.fixture(scope="function")
def publication_creation_info():
    return {
        "publication_items": [{
            "size": 40,
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


@pytest.fixture(scope="function")
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
                "size": "40",
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


@pytest.fixture(scope="function")
def generate_basic_publications(
    ninja_client,
    super_user,
    user_one,
    user_one_creation_info,
    publication_creation_info,
    publication_photo_file,
    category_creation_info,
    category_photo_file,
    generate_seller_permissions,
) -> None:
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
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
    ).json() == category_creation_info | {'id': 1, 'image_uri': _IMAGE_URI}
    # check the post by creating a publication
    response = ninja_client.post(
        '/publications/publications/create',
        data={
            'body': json.dumps(publication_creation_info),
        },
        FILES=publication_photo_file,
        user=user_one
    )
    assert response.status_code == 201


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_post_and_get_pub(
    ninja_client,
    super_user,
    publication_get_info,
    generate_basic_publications
):
    # Check if the publication was created successfully and if the gets work
    assert ninja_client.get(
        'publications/publications/obtener_as_admin/1',
        user=super_user
    ).json() == publication_get_info


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_accept_and_get_pub(
    ninja_client,
    super_user,
    publication_get_info,
    generate_basic_publications
):
    # Check if the publication was created successfully and if the gets work
    assert ninja_client.get(
        'publications/publications/obtener_as_admin/1',
        user=super_user
    ).json() == publication_get_info
    accept_publication_get_info = {**publication_get_info}
    accept_publication_get_info['is_active'] = True
    accept_publication_get_info['is_accepted'] = True
    response = ninja_client.patch(
        'publications/publications/accept/1',
        user=super_user
    )
    assert response.status_code == 200
    assert response.json() == accept_publication_get_info


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_reject_and_get_pub(
    ninja_client,
    super_user,
    publication_get_info,
    generate_basic_publications
):
    # Check if the publication was created successfully and if the gets work
    assert ninja_client.get(
        'publications/publications/obtener_as_admin/1',
        user=super_user
    ).json() == publication_get_info
    assert ninja_client.delete(
        'publications/publications/reject/1',
        user=super_user
    ).status_code == 204


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def show_all_publications(
    ninja_client,
    super_user,
    generate_basic_publications
):
    # Accept publicatio
    assert ninja_client.get(
        '/publications/publications/all',
        user=super_user
    ).json() == [{
        'id': 1,
        'seller': 1,
        'photo_uris': [_IMAGE_URI],
        'description': 'Test description',
        'general_item_info': {
            'name': 'jockey',
            'brand': 'adidas',
            'category': {'id': 1, 'name': 'categorytest'},
            'total_amount': 3
        }
    }]


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_category_create_delete(
    ninja_client,
    super_user,
    category_creation_info,
    category_photo_file
):
    # create category
    assert ninja_client.post(
        '/publications/categories/create',
        data={
            'body': json.dumps(category_creation_info),
        },
        FILES={'file': category_photo_file},
        user=super_user
    ).json() == category_creation_info | {'id': 1, 'image_uri': _IMAGE_URI}
    # get all categories
    assert ninja_client.get(
        '/publications/categories/all'
    ).json() == [category_creation_info | {'id': 1, 'image_uri': _IMAGE_URI}]
    # delete categories
    assert ninja_client.delete(
        '/publications/categories/remove/1',
        user=super_user
    ).status_code == 204
    # get empty list
    assert ninja_client.get(
        '/publications/categories/all'
    ).json() == []


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_create_invalid_item(
    ninja_client,
    user_one,
    publication_creation_info,
    publication_photo_file,
    generate_basic_publications
):
    # create invalid publication
    wrong_pub_info = deepcopy(publication_creation_info)
    wrong_pub_info['item_brand'] = 'WrongBrand'
    assert ninja_client.post(
        '/publications/publications/create',
        data={
            'body': json.dumps(wrong_pub_info),
        },
        FILES=publication_photo_file,
        user=user_one
    ).status_code == 409


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_create_publication_with_valid_existing_item(
    ninja_client,
    super_user,
    user_two,
    user_two_creation_info,
    publication_creation_info,
    publication_photo_file,
    publication_get_info,
    generate_basic_publications
):
    # create second user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_two_creation_info
    )
    # give new user seller permissions
    ninja_client.patch(
        '/user_profiles/permissions/assign_seller/2',
        user=super_user
    )
    # create valid publication with existing item
    capitalized_pub_info = deepcopy(publication_creation_info)
    capitalized_pub_info['item_brand'] = 'ADIDAS'
    response = ninja_client.post(
        '/publications/publications/create',
        data={
            'body': json.dumps(capitalized_pub_info),
        },
        FILES=publication_photo_file,
        user=user_two
    )
    assert 'publication_items' in response.json().keys()
    assert response.json()['publication_items'][0]['item'] \
        == publication_get_info['publication_items'][0]['item']


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_wrong_field_value_publication_post(
    ninja_client,
    super_user,
    user_one,
    user_one_creation_info,
    publication_creation_info,
    publication_photo_file,
    category_creation_info,
    category_photo_file,
    generate_seller_permissions
):
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
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
    ).json() == category_creation_info | {'id': 1, 'image_uri': _IMAGE_URI}
    # Give empty publication items list
    empty_publication_creation_info = {**publication_creation_info}
    empty_publication_creation_info['publication_items'] = []
    assert ninja_client.post(
        '/publications/publications/create',
        data={
            'body': json.dumps(empty_publication_creation_info),
        },
        FILES=publication_photo_file,
        user=user_one
    ).json() == {'errors': {'publication_items': ['List can not be empty.']}}
    # Give too long of a fied
    size_too_long_creation_info = {**publication_creation_info}
    size_too_long_creation_info['publication_items'][0]['size'] = 'a' * 64
    response = ninja_client.post(
        '/publications/publications/create',
        data={
            'body': json.dumps(size_too_long_creation_info),
        },
        FILES=publication_photo_file,
        user=user_one
    )
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_duplicate_sku_in_publication_items(
    ninja_client,
    super_user,
    user_one,
    user_one_creation_info,
    publication_creation_info,
    publication_photo_file,
    category_creation_info,
    category_photo_file,
    generate_seller_permissions
):
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
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
    ).json() == category_creation_info | {'id': 1, 'image_uri': _IMAGE_URI}
    # Give empty publication items list
    duplicate_sku_creation_info = {**publication_creation_info}
    duplicate_sku_creation_info['publication_items'].append({
        'size': 'S',
        'color': 'Red',
        'amount': 10,
        'sku': 222
    })
    assert ninja_client.post(
        '/publications/publications/create',
        data={
            'body': json.dumps(duplicate_sku_creation_info),
        },
        FILES=publication_photo_file,
        user=user_one
    ).json() == {'message': 'Duplicate sku.'}


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_get_all_existing_brands(
    ninja_client,
    generate_basic_publications
):
    assert ninja_client.get(
        '/publications/publications/existing_brands'
    ).json() == ['adidas']


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def create_duplicate_publication(
    ninja_client,
    super_user,
    user_one,
    user_one_creation_info,
    publication_creation_info,
    publication_photo_file,
    category_creation_info,
    generate_basic_publications
):
    # Create post
    response = ninja_client.post(
        '/publications/publications/create',
        data={
            'body': json.dumps(publication_creation_info),
        },
        FILES=publication_photo_file,
        user=user_one
    )
    expected_error = 'Publication for items with this name and brand' \
        + 'already exist.'
    assert response.status_code == 400
    assert response.json() == {'message': expected_error}


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def add_publication_items(
    ninja_client,
    user_one,
    publication_get_info,
    generate_basic_publications
):
    # Add valid publication_item
    new_pub_items = [
        {'size': 'S', 'color': 'White', 'sku': 223, 'amount': 1},
        {'size': 'S', 'color': 'Red', 'sku': 224, 'amount': 1},
    ]
    # Create expected response
    new_publication_items = publication_get_info['publication_items']
    for i, info in enumerate(new_pub_items):
        new_publication_items.append({
            'id': i + 2,
            'publication': 1,
            'item': {
                'id': i + 2,
                'name': 'jockey',
                'brand': 'adidas',
                'category': {'id': 1, 'name': 'categorytest'},
                'color': info['color'],
                'size': info['size'],
                'sku': info['sku']
            },
            'available': info['amount']
        })
    # Assert correct response
    add_valid_pub_item_response = ninja_client.post(
        '/publications/publications/add_publication_item/1',
        json={'publication_items': new_pub_items},
        user=user_one
    )
    assert add_valid_pub_item_response.status_code == 200
    assert add_valid_pub_item_response.status_code == publication_get_info


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def update_publications(
    ninja_client,
    user_one,
    publication_get_info,
    generate_basic_publications
):
    # Update publication
    publication_get_info['price'] = 20000
    publication_get_info['description'] = 'new description'
    assert ninja_client.patch(
        '/pubications/publications/update_publication/1',
        json={
            'price': publication_get_info['price'],
            'description': publication_get_info['description']
        },
        user=user_one
    ).json() == publication_get_info
    # Update publication item
    new_amount = 10
    publication_get_info['publication_items'][0]['amount'] = new_amount
    assert ninja_client.patch(
        '/pubications/publications/update_publication_item/1',
        json={'amount': new_amount},
        user=user_one
    ).json() == publication_get_info
    # Fail invalid update
    assert ninja_client.patch(
        '/pubications/publications/update_publication_item/1',
        json={'amount': -10},
        user=user_one
    ).status_code == 400


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_upload_wrong_publication_files(
    ninja_client,
    super_user,
    user_one,
    user_one_creation_info,
    publication_creation_info,
    # publication_get_info,
    category_creation_info,
    category_photo_file,
    generate_seller_permissions
):
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
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
    ).json() == category_creation_info | {'id': 1, 'image_uri': _IMAGE_URI}
    # Give too many files
    publication_photo_files = MultiValueDict({
        'files': [
            SimpleUploadedFile(f'test{i}.jpeg', b'img_data')
            for i in range(6)
        ]
    })
    assert ninja_client.post(
        '/publications/publications/create',
        data={
            'body': json.dumps(publication_creation_info),
        },
        FILES=publication_photo_files,
        user=user_one
    ).status_code == 400
    # Give wrong extension
    wrong_extensions_publication_photo_files = MultiValueDict({
        'files': [
            SimpleUploadedFile('test.txt', b'img_data')
        ]
    })
    response = ninja_client.post(
        '/publications/publications/create',
        data={
            'body': json.dumps(publication_creation_info),
        },
        FILES=wrong_extensions_publication_photo_files,
        user=user_one
    )
    assert response.status_code == 400
