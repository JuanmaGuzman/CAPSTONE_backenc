import pytest
from django.contrib.auth.models import Group


@pytest.fixture(scope="function")
def create_seller_permissions() -> None:
    Group.objects.get_or_create(name='Seller')


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_seller_permission(
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
    assert ninja_client.patch(
        '/user_profiles/permissions/assign_seller/1',
        user=super_user
    ).json() == user_one_get_info | {
        'id': 1, 'is_admin': False, 'is_seller': True
    }
    super_user.has_perm.assert_called_with(
        'user_profiles.assign_seller'
    )


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_remove_seller_permission(
    ninja_client,
    super_user,
    user_one_creation_info,
    create_seller_permissions
):
    # Create soon to be seller
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )

    ninja_client.patch(
        '/user_profiles/permissions/assign_seller/1',
        user=super_user
    )

    assert ninja_client.patch(
        '/user_profiles/permissions/remove_seller/1',
        user=super_user
    ).status_code == 204

    super_user.has_perm.assert_called_with(
        'user_profiles.assign_seller'
    )
