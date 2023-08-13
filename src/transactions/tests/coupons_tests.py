import pytest


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_create_delete_coupon(
    ninja_client,
    user_one,
    user_one_creation_info,
    user_two,
    user_two_creation_info,
    super_user,
    coupon_creation_info,
    coupon_get_info,
    generate_coupon_permissions
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
    ).json() == coupon_get_info
    # Fail creating coupon by non admin
    assert ninja_client.post(
        'transactions/coupons/create',
        json=coupon_creation_info,
        user=user_two
    ).status_code == 403
    # Fail to delete coupon as non admin
    assert ninja_client.delete(
        'transactions/coupons/delete/1',
        user=user_two
    ).status_code == 403
    # Succesfully delete coupon by admin
    assert ninja_client.delete(
        'transactions/coupons/delete/1',
        user=user_one
    ).status_code == 204


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_create_duplicate_coupon(
    ninja_client,
    user_one,
    user_one_creation_info,
    super_user,
    coupon_creation_info,
    coupon_get_info,
    generate_coupon_permissions
):
    # Create user 1
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
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
    ).json() == coupon_get_info
    # Create second coupon by admin
    assert ninja_client.post(
        'transactions/coupons/create',
        json=coupon_creation_info,
        user=user_one
    ).status_code == 400


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_deactivate_activate_coupons(
    ninja_client,
    user_one,
    user_one_creation_info,
    super_user,
    coupon_creation_info,
    coupon_get_info,
    generate_coupon_permissions
):
    # Create user 1
    ninja_client.post(
        '/user_profiles/user_profiles/create',
        json=user_one_creation_info
    )
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
    ).json() == coupon_get_info
    # Deactivate coupon
    assert ninja_client.patch(
        'transactions/coupons/deactivate/1',
        user=user_one
    ).status_code == 200
    deactivated_coupon_info = {**coupon_get_info}
    deactivated_coupon_info['active'] = False
    assert ninja_client.get(
        'transactions/coupons/all',
        user=user_one
    ).json() == [deactivated_coupon_info]
    # Reactivate coupon
    assert ninja_client.patch(
        'transactions/coupons/activate/1',
        user=user_one
    ).status_code == 200
    assert ninja_client.get(
        f'transactions/coupons/validate/{coupon_get_info["code"]}',
        user=user_one
    ).json() == coupon_get_info
