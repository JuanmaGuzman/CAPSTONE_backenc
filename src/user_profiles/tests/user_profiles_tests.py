import pytest
from utilities.errors import missing_permission


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_get_user(
    ninja_client,
    user_one,
    user_one_creation_info,
    user_one_get_info
):
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Assert endpoint
    assert ninja_client.get(
        '/user_profiles/user_profiles/me',
        user=user_one
    ).json() == user_one_get_info


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_create_user(ninja_client, user_one_creation_info, user_one_get_info):
    assert ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    ).json() == user_one_get_info


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_delete_user(ninja_client, user_one, user_one_creation_info):
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Assert endpoint
    assert ninja_client.delete(
        '/user_profiles/user_profiles/remove_user',
        user=user_one
    ).status_code == 204


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_update_user(
    ninja_client,
    user_one,
    user_one_creation_info,
    user_one_get_info
):
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Assert endpoint
    assert ninja_client.patch(
        '/user_profiles/user_profiles/update',
        json={
            'username': 'js',
            'email': 'new_email@email.com',
            'first_name': 'new_first_name',
            'last_name': 'new_last_name'
        },
        user=user_one
    ).json() == {
        'id': 1,
        'username': 'js',
        'email': 'new_email@email.com',
        'first_name': 'new_first_name',
        'last_name': 'new_last_name',
        'phone_number': user_one_get_info['phone_number'],
        'rut': user_one_get_info['rut'],
        'birthdate': user_one_get_info['birthdate'],
        'is_admin': False,
        'is_seller': False
    }


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_email_verification(ninja_client, user_one, user_one_creation_info):
    # Imports
    from user_profiles.tokens import email_confrimation_token_generator
    from django.contrib.auth import get_user_model
    # Create User
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Update email to set email_verified to False
    ninja_client.patch(
        '/user_profiles/user_profiles/update',
        json={
            'username': 'js',
            'email': 'new_email@email.com',
            'first_name': 'new_first_name',
            'last_name': 'new_last_name'
        },
        user=user_one
    )
    # Attempt and fail to log in
    assert ninja_client.post(
        '/auth/',
        json={
            'email': 'new_email@email.com',
            'password': user_one_creation_info['password1']
        }
    ).status_code == 403
    # Generate token
    user = get_user_model().objects.get(pk=user_one.id)
    token = email_confrimation_token_generator.make_token(user)
    # Confirm email using token
    assert ninja_client.patch(
        '/user_profiles/user_profiles/confirm_email',
        json={
            'id': user_one.id,
            'token': token
        }
    ).status_code == 200
    user.refresh_from_db()
    # Login
    assert ninja_client.post(
        '/auth/',
        json={
            'email': 'new_email@email.com',
            'password': user_one_creation_info['password1']
        }
    ).status_code == 200


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_create_delete_shipping_address(
    ninja_client,
    user_one,
    user_one_creation_info,
    address_creation_info
):
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Create address
    assert ninja_client.post(
        '/user_profiles/user_profiles/shipping_address',
        json=address_creation_info,
        user=user_one
    ).json() == address_creation_info | {'id': 1, 'user': 1}
    # Delete address
    assert ninja_client.delete(
        '/user_profiles/user_profiles/shipping_address/1',
        user=user_one
    ).status_code == 204


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_create_duplicate_shipping_address(
    ninja_client,
    user_one,
    user_one_creation_info,
    address_creation_info
):
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Create address
    assert ninja_client.post(
        '/user_profiles/user_profiles/shipping_address',
        json=address_creation_info,
        user=user_one
    ).json() == address_creation_info | {'id': 1, 'user': 1}
    # Create address
    assert ninja_client.post(
        '/user_profiles/user_profiles/shipping_address',
        json=address_creation_info,
        user=user_one
        ).json() == {'errors': {'user_id': ['Duplicate address.']}}


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_get_shipping_address(
    ninja_client,
    user_one,
    user_one_creation_info,
    user_two,
    user_two_creation_info,
    address_creation_info
):
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Create second user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_two_creation_info
    )
    # Create address
    assert ninja_client.post(
        '/user_profiles/user_profiles/shipping_address',
        json=address_creation_info,
        user=user_one
    ).status_code == 200
    # Get all addresses
    assert ninja_client.get(
        '/user_profiles/user_profiles/shipping_address/me',
        user=user_one
    ).json() == [address_creation_info | {'id': 1, 'user': 1}]
    # Get specific addresses
    assert ninja_client.get(
        '/user_profiles/user_profiles/shipping_address/me/1',
        user=user_one
    ).json() == address_creation_info | {'id': 1, 'user': 1}
    # Fail getting other user address
    assert ninja_client.get(
        '/user_profiles/user_profiles/shipping_address/me/1',
        user=user_two
    ).status_code == 404


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_delete_other_user_shipping_address(
    ninja_client,
    user_one,
    user_one_creation_info,
    user_two,
    user_two_creation_info,
    address_creation_info
):
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Create second user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_two_creation_info
    )
    # Create address
    ninja_client.post(
        '/user_profiles/user_profiles/shipping_address',
        json=address_creation_info,
        user=user_one
    )
    # Fail to delete other user address
    assert ninja_client.delete(
        '/user_profiles/user_profiles/shipping_address/1',
        user=user_two
    ).status_code == 404


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_get_seller_info(
    ninja_client,
    super_user,
    user_one_creation_info,
    user_one_get_info,
    create_seller_permissions
):
    # Create soon to be seller
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Make seller
    ninja_client.patch(
        '/user_profiles/permissions/assign_seller/1',
        user=super_user
    )
    # Get seller info
    assert ninja_client.get(
        '/user_profiles/user_profiles/seller/1'
    ).json() == {
        'email': user_one_get_info['email'],
        'first_name': user_one_get_info['first_name'],
        'last_name': user_one_get_info['last_name']
    }


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_fail_getting_non_seller_info(
    ninja_client,
    user_one_creation_info
):
    # Create user
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Fail to get non seller user info
    assert ninja_client.get(
        '/user_profiles/user_profiles/seller/1'
    ).status_code == 404


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_get_all_users(
    ninja_client,
    user_one_creation_info,
    user_one,
    user_one_get_info,
    user_two_creation_info,
    user_two_get_info,
    super_user
):
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
    # Get users that are active (1 and 2)
    assert ninja_client.get(
        '/user_profiles/user_profiles/all',
        user=super_user
    ).json() == [user_one_get_info, user_two_get_info]
    super_user.has_perm.assert_called_with(
        'user_profiles.can_get_all_user_profiles'
    )
    # Delete user 1
    ninja_client.delete(
        '/user_profiles/user_profiles/remove_user',
        user=user_one
    )
    # Get users that are active (2)
    assert ninja_client.get(
        '/user_profiles/user_profiles/all',
        user=super_user
    ).json() == [user_two_get_info]


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_fail_to_get_all_users(
    ninja_client,
    user_one_creation_info,
    mid_user
):
    # Create user 1
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Get users that are active (1 and 2)
    assert ninja_client.get(
        '/user_profiles/user_profiles/all',
        user=mid_user
    ).status_code == 403


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_delete_user_by_id(
    ninja_client,
    user_one_creation_info,
    super_user
):
    # Create user 1
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Delete user
    assert ninja_client.delete(
        '/user_profiles/user_profiles/remove_user/1',
        user=super_user
    ).status_code == 204
    super_user.has_perm.assert_called_with(
        'user_profiles.can_delete_user'
    )
    # Check user does not exist
    assert ninja_client.get(
        '/user_profiles/user_profiles/all',
        user=super_user
    ).json() == []


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_fail_to_delete_user_by_id(
    ninja_client,
    user_one_creation_info,
    super_user,
    mid_user,
    create_admin_permissions
):
    # Create user 1
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
    # Assign admin
    assert ninja_client.patch(
        '/user_profiles/permissions/assign_admin/1',
        user=super_user
    ).status_code == 200
    # Fail to delete user: not an admin
    assert ninja_client.delete(
        '/user_profiles/user_profiles/remove_user/1',
        user=mid_user
    ).json() == missing_permission()
    # Fail to delete user: 404
    assert ninja_client.delete(
        '/user_profiles/user_profiles/remove_user/2',
        user=super_user
    ).status_code == 404
    # Fail to delete user: user is admin
    assert ninja_client.delete(
        '/user_profiles/user_profiles/remove_user/1',
        user=super_user
    ).json() == {'message': 'Target user is an Admin.'}
