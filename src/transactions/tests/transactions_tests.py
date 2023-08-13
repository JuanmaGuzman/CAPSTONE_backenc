import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from publications.models import Publication
from transactions.tests.conftest import _IMAGE_URI
from unittest.mock import Mock, patch
import json


mock_send_payment_intent = Mock()
mock_send_payment_intent.side_effect = [
    {f'pmntid{i}', f'wdgttk1{i}'}
    for i in range(20)
]
failed_mock_send_payment_intent = Mock(return_value=(None, None))


def _generate_publication_permissions() -> None:
    seller_group, _ = Group.objects.get_or_create(name='Seller')
    # Check for permission to create publication
    pub_permission, _ = Permission.objects.get_or_create(
        id=1000,
        codename='can_create',
        name='Can create publication',
        content_type=ContentType.objects.get_for_model(Publication)
    )
    allow_pub_permission, _ = Permission.objects.get_or_create(
        id=1001,
        codename='can_allow',
        name='Can allow publiction',
        content_type=ContentType.objects.get_for_model(Publication)
    )
    seller_group.permissions.add(pub_permission, allow_pub_permission)


def _generate_publications(
    ninja_client,
    super_user,
    user_one,
    user_one_creation_info,
    user_two,
    user_two_creation_info,
    address_creation_info,
    publication_creation_info,
    category_creation_info,
    category_photo_file,
    publication_photo_file
) -> None:
    # Create user 1
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Create user 2
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_two_creation_info
    )
    # Add user 2 address
    ninja_client.post(
        '/user_profiles/user_profiles/shipping_address',
        json=address_creation_info,
        user=user_two
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
    # create publication
    assert ninja_client.post(
        '/publications/publications/create',
        data={
            'body': json.dumps(publication_creation_info),
        },
        FILES=publication_photo_file,
        user=user_one
    ).status_code == 201
    # allow publication
    assert ninja_client.patch(
        '/publications/publications/accept/1',
        user=user_one
    ).status_code == 200


@pytest.fixture(scope='function')
def generate_publication_and_permissions(
    ninja_client,
    super_user,
    user_one,
    user_one_creation_info,
    user_two,
    user_two_creation_info,
    address_creation_info,
    publication_creation_info,
    category_creation_info,
    category_photo_file,
    publication_photo_file
) -> None:
    _generate_publication_permissions()
    _generate_publications(
        ninja_client,
        super_user,
        user_one,
        user_one_creation_info,
        user_two,
        user_two_creation_info,
        address_creation_info,
        publication_creation_info,
        category_creation_info,
        category_photo_file,
        publication_photo_file
    )


@pytest.fixture(scope="function")
def user_transactions_result(address_creation_info):
    return [{
        'id': 1,
        'shipping_address': address_creation_info | {'id': 1, 'user': 2},
        'coupon': None,
        'transaction_pointers': [{
            'id': 1,
            'amount': 2,
            'price_per_unit': 25000,
            'publication_item': {
                'id': 1,
                'publication': 1,
                'item': {
                    'id': 1,
                    'name': 'jockey',
                    'brand': 'adidas',
                    'size': 'xl',
                    'color': 'azul',
                    'sku': 222,
                    'category': {
                        'id': 1,
                        'name': 'categorytest'
                    },
                },
                'available': 0,
                'publication_info': {
                    'price': 25000,
                    'image_uris': [_IMAGE_URI]
                }
            },
        }],
    }]


@pytest.fixture(scope="function")
def seller_transactions_result(address_creation_info):
    return {
        'transaction_pointers': [
            {
                'id': 1,
                'amount': 2,
                'price_per_unit': 25000,
                'transaction': {
                    'shipping_address': address_creation_info |
                    {'id': 1, 'user': 2},
                    'buyer': {
                        'email': 'js2@email.com',
                        'first_name': 'John2',
                        'last_name': 'Smith2'
                    },
                    'coupon': None
                },
                'publication_item': {
                    'id': 1,
                    'publication': 1,
                    'item': {
                        'id': 1,
                        'name': 'jockey',
                        'brand': 'adidas',
                        'size': 'xl',
                        'color': 'azul',
                        'category': {
                            'id': 1,
                            'name': 'categorytest'
                        },
                        'sku': 222,
                    },
                    'available': 0
                }
            }
        ],
        'accountless_transaction_pointers': [
            {
                'id': 1,
                'amount': 1,
                'price_per_unit': 25000,
                'transaction': {
                    'buyer_name': 'John',
                    'buyer_lastname': 'Wick',
                    'phone_number': '+56911111111',
                    'region': 'RegionTest',
                    'commune': 'CommuneTest',
                    'address': 'AddressTest',
                    'coupon': None
                },
                'publication_item': {
                    'id': 1,
                    'publication': 1,
                    'item': {
                        'id': 1,
                        'name': 'jockey',
                        'brand': 'adidas',
                        'size': 'xl',
                        'color': 'azul',
                        'category': {
                            'id': 1,
                            'name': 'categorytest'
                        },
                        'sku': 222,
                    },
                    'available': 0
                }
            }
        ]
    }


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@patch(
    'transactions.api.transactions.send_payment_intent',
    new=mock_send_payment_intent
)
def test_transaction_creation(
    ninja_client,
    user_two,
    generate_publication_and_permissions
):
    # add publication to user cart
    ninja_client.post(
        '/publications/shopping_cart/add_to_cart/1',
        json={'amount': 1},
        user=user_two
    )
    # create transaction
    response = ninja_client.post(
        '/transactions/transactions/create/',
        json={'shipping_address_id': 1},
        user=user_two
    )
    assert [
        key
        for key in response.json().keys()
    ] == ['payment_id', 'widget_token']


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@patch(
    'transactions.api.transactions.send_payment_intent',
    new=mock_send_payment_intent
)
def test_accountless_transaction_creation(
    ninja_client,
    correct_accountless_transaction_creation_info,
    generate_publication_and_permissions
):
    # create transaction
    response = ninja_client.post(
        '/transactions/transactions/create_acountless/',
        json=correct_accountless_transaction_creation_info
    )
    assert [
        key
        for key in response.json().keys()
    ] == ['payment_id', 'widget_token']


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@patch(
    'transactions.api.transactions.send_payment_intent',
    new=mock_send_payment_intent
)
def test_not_enough_amount(
    ninja_client,
    user_two,
    wrong_accountless_transaction_creation_info,
    generate_publication_and_permissions
):
    # add publication to user cart
    ninja_client.post(
        '/publications/shopping_cart/add_to_cart/1',
        json={'amount': 4},
        user=user_two
    )
    # create transaction
    assert ninja_client.post(
        '/transactions/transactions/create/',
        json={'shipping_address_id': 1},
        user=user_two
    ).json() == {
        'errors': {
            'publication_1': ['No hay suficientes unidades disponibles.']
        }
    }
    # create transaction
    assert ninja_client.post(
        '/transactions/transactions/create_acountless/',
        json=wrong_accountless_transaction_creation_info
    ).json() == {
        'errors': {
            'publication_1': ['No hay suficientes unidades disponibles.']
        }
    }


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@patch(
    'transactions.api.transactions.send_payment_intent',
    new=mock_send_payment_intent
)
def test_not_enough_available(
    ninja_client,
    user_two,
    correct_accountless_transaction_creation_info,
    generate_publication_and_permissions
):
    # add publication to user cart
    ninja_client.post(
        '/publications/shopping_cart/add_to_cart/1',
        json={'amount': 2},
        user=user_two
    )
    # create transaction
    assert ninja_client.post(
        '/transactions/transactions/create_acountless/',
        json=correct_accountless_transaction_creation_info
    ).status_code == 200
    # fail creating transaction
    assert ninja_client.post(
        '/transactions/transactions/create/',
        json={'shipping_address_id': 1},
        user=user_two
    ).json() == {
        'errors': {
            'publication_1': ['No hay suficientes unidades disponibles.']
        }
    }
    # fail in an accountless fashion
    assert ninja_client.post(
        '/transactions/transactions/create_acountless/',
        json=correct_accountless_transaction_creation_info
    ).json() == {
        'errors': {
            'publication_1': ['No hay suficientes unidades disponibles.']
        }
    }


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@patch(
    'transactions.api.transactions.send_payment_intent',
    new=mock_send_payment_intent
)
def test_canel_transaction(
    ninja_client,
    user_two,
    correct_accountless_transaction_creation_info,
    generate_publication_and_permissions
):
    # add publication to user cart
    ninja_client.post(
        '/publications/shopping_cart/add_to_cart/1',
        json={'amount': 2},
        user=user_two
    )
    # create transaction
    transaction_resp = ninja_client.post(
        '/transactions/transactions/create_acountless/',
        json=correct_accountless_transaction_creation_info
    )
    assert transaction_resp.status_code == 200
    # confirm new available amount
    assert ninja_client.get(
        'publications/publications/obtener/1'
    ).json()['publication_items'][0]['available'] == 1
    # cancel transaction
    canel_path = 'transactions/transaction_confirmation/cancel/' \
        + f'{transaction_resp.json()["payment_id"]}'
    assert ninja_client.patch(canel_path).status_code == 200
    # confirm new available amount
    assert ninja_client.get(
        'publications/publications/obtener/1'
    ).json()['publication_items'][0]['available'] == 3


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@patch(
    'transactions.api.transactions.send_payment_intent',
    new=mock_send_payment_intent
)
def test_confirm_transaction_request_deletes_cart(
    ninja_client,
    user_two,
    generate_publication_and_permissions
):
    # add publication to user cart
    ninja_client.post(
        '/publications/shopping_cart/add_to_cart/1',
        json={'amount': 2},
        user=user_two
    )
    # create transaction
    transaction_resp = ninja_client.post(
        '/transactions/transactions/create/',
        json={'shipping_address_id': 1},
        user=user_two
    )
    assert transaction_resp.status_code == 200
    # confirm transaction
    confirm_path = 'transactions/transaction_confirmation/confirm_request/' \
        + f'{transaction_resp.json()["payment_id"]}'
    assert ninja_client.patch(confirm_path, user=user_two).status_code == 200
    # confirm new available amount
    assert ninja_client.get(
        'publications/shopping_cart/shopping_cart/me',
        user=user_two
    ).json() == []


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@patch(
    'transactions.api.transactions.send_payment_intent',
    new=mock_send_payment_intent
)
@patch(
    'transactions.api.confirmation.validate_signature',
    new=Mock(return_value=True)
)
def test_resolving_transaction(
    ninja_client,
    user_one,
    user_two,
    address_creation_info,
    correct_accountless_transaction_creation_info,
    user_transactions_result,
    seller_transactions_result,
    generate_publication_and_permissions
):
    # add publication to user cart
    ninja_client.post(
        '/publications/shopping_cart/add_to_cart/1',
        json={'amount': 2},
        user=user_two
    )
    # create user transaction
    response = ninja_client.post(
        '/transactions/transactions/create/',
        json={'shipping_address_id': 1},
        user=user_two
    )
    assert response.status_code == 200
    payment_id = response.json()['payment_id']
    # create accountless transaction
    correct_accountless_transaction_creation_info[
        'publication_items_list'
    ][0]['amount'] = 1
    accountless_response = ninja_client.post(
        '/transactions/transactions/create_acountless/',
        json=correct_accountless_transaction_creation_info
    )
    assert accountless_response.status_code == 200
    accountless_payment_id = accountless_response.json()["payment_id"]
    # resolve transaction
    assert ninja_client.post(
        '/transactions/transaction_confirmation/resolved',
        json={'id': payment_id, 'type': 'payment_intent.succeeded'}
    ).status_code == 200
    assert ninja_client.post(
        '/transactions/transaction_confirmation/resolved',
        json={'id': accountless_payment_id, 'type': 'payment_intent.succeeded'}
    ).status_code == 200
    # check buyer purchase list
    assert ninja_client.get(
        '/transactions/transactions/my-purchases',
        user=user_two
    ).json() == user_transactions_result
    # check seller 'my-sells' list
    assert ninja_client.get(
        '/transactions/transactions/my-sells',
        user=user_one
    ).json() == seller_transactions_result


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@patch(
    'transactions.api.transactions.send_payment_intent',
    new=mock_send_payment_intent
)
@patch(
    'transactions.api.confirmation.validate_signature',
    new=Mock(return_value=True)
)
def test_resolving_transaction_with_coupons(
    ninja_client,
    user_one,
    user_two,
    super_user,
    publication_creation_info,
    correct_accountless_transaction_creation_info,
    user_transactions_result,
    seller_transactions_result,
    coupon_creation_info,
    generate_publication_and_permissions,
    generate_coupon_permissions
):
    # Assign user 1 as admin
    ninja_client.patch(
        '/user_profiles/permissions/assign_admin/1',
        user=super_user
    )

    # Create coupon by admin
    assert ninja_client.post(
        'transactions/coupons/create',
        json=coupon_creation_info,
        user=user_one
    ).status_code == 200
    # Create second coupon by admin
    second_coupon_creation_info = {**coupon_creation_info}
    second_coupon_creation_info['code'] = 'randomstringhere'
    assert ninja_client.post(
        'transactions/coupons/create',
        json=second_coupon_creation_info,
        user=user_one
    ).status_code == 200

    # add publication to user cart
    ninja_client.post(
        '/publications/shopping_cart/add_to_cart/1',
        json={'amount': 2},
        user=user_two
    )
    exp_price = publication_creation_info['price'] \
        * (1 - coupon_creation_info['discount_percentage']/100)
    # create user transaction
    response = ninja_client.post(
        '/transactions/transactions/create/',
        json={'shipping_address_id': 1, 'coupon_id': 1},
        user=user_two
    )
    assert response.status_code == 200
    payment_id = response.json()['payment_id']
    mock_send_payment_intent.assert_called_with(exp_price * 2)

    # create accountless transaction
    correct_accountless_transaction_creation_info[
        'publication_items_list'
    ][0]['amount'] = 1
    # fail repeating cupon
    assert ninja_client.post(
        '/transactions/transactions/create_acountless/',
        json=correct_accountless_transaction_creation_info | {'coupon_id': 1}
    ).status_code == 404
    # succeed using second coupon
    accountless_response = ninja_client.post(
        '/transactions/transactions/create_acountless/',
        json=correct_accountless_transaction_creation_info | {'coupon_id': 2}
    )
    assert accountless_response.status_code == 200
    accountless_payment_id = accountless_response.json()['payment_id']
    mock_send_payment_intent.assert_called_with(exp_price)

    # resolve transaction
    assert ninja_client.post(
        '/transactions/transaction_confirmation/resolved',
        json={'id': payment_id, 'type': 'payment_intent.succeeded'}
    ).status_code == 200
    # resolve accountless transaction
    assert ninja_client.post(
        '/transactions/transaction_confirmation/resolved',
        json={'id': accountless_payment_id, 'type': 'payment_intent.succeeded'}
    ).status_code == 200

    # update response info to contain coupons
    succint_coupon_info = {**coupon_creation_info} | {'id': 1}
    del succint_coupon_info['name']
    # check buyer purchase list
    user_transactions_result[0].update({'coupon': succint_coupon_info})
    assert ninja_client.get(
        '/transactions/transactions/my-purchases',
        user=user_two
    ).json() == user_transactions_result

    # update response info to contain coupons
    second_succinct_coupon_info = {**second_coupon_creation_info} | {'id': 2}
    del second_succinct_coupon_info['name']
    seller_transactions_result[
        'transaction_pointers'
    ][0]['transaction'].update({'coupon': succint_coupon_info})
    seller_transactions_result[
        'accountless_transaction_pointers'
    ][0]['transaction'].update({'coupon': second_succinct_coupon_info})
    # check seller 'my-sells' list
    assert ninja_client.get(
        '/transactions/transactions/my-sells',
        user=user_one
    ).json() == seller_transactions_result


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@patch(
    'transactions.api.transactions.send_payment_intent',
    new=failed_mock_send_payment_intent
)
def test_transaction_restoration(
    ninja_client,
    user_two,
    publication_get_info,
    generate_publication_and_permissions
):
    # add publication to user cart
    ninja_client.post(
        '/publications/shopping_cart/add_to_cart/1',
        json={'amount': 1},
        user=user_two
    )
    # create transaction
    response = ninja_client.post(
        '/transactions/transactions/create/',
        json={'shipping_address_id': 1},
        user=user_two
    )
    assert response.status_code == 503
    # Check that publication amount info is resotred correctly
    accepted_publication_get_info = {**publication_get_info}
    accepted_publication_get_info['is_active'] = True
    accepted_publication_get_info['is_accepted'] = True
    assert ninja_client.get(
        '/publications/publications/obtener/1'
    ).json() == accepted_publication_get_info
