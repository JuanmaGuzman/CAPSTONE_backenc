from ninja import Router
from ninja.security import django_auth
from django.contrib.auth import (
    login as django_login,
    logout as django_logout
)
from user_profiles.tokens import email_confrimation_token_generator
from user_profiles.models import UserProfile, UserShippingAddress
from user_profiles.schema import (
    PublicUserProfileSchema,
    UserProfileSchema,
    UserProfileCreationSchema,
    UserShippingAddressSchema,
    UserShippingAddressCreateSchema,
    UserUpdateSchema,
    EmailConfirmationSchema
)
from user_profiles.forms import (
    UserCreationForm,
    UserUpdateForm,
    UserShippingAddressCreationForm
)
from user_profiles.mail import send_confirmation_email
from utilities.errors import ErrorsOut, ErrorOut, missing_permission, not_found


router = Router()
_LOGIN_BACKEND = 'user_auth.backend.EmailBackend'


@router.get('/me', response=UserProfileSchema, auth=django_auth)
def get_user(request):
    return UserProfile.objects.get(id=request.user.id)


@router.get(
    '/seller/{seller_id}',
    response={
        200: PublicUserProfileSchema,
        404: ErrorsOut
    }
)
def get_seller(request, seller_id: int):
    seller_query = UserProfile.objects.filter(
        id=seller_id,
        groups__name='Seller'
    )
    if seller_query.exists():
        seller = seller_query.get()
        return 200, seller
    return 404, {'errors': {'seller_id': ['User not found.']}}


@router.get(
    '/all',
    response={
        200: list[UserProfileSchema],
        403: ErrorOut
    },
    auth=django_auth
)
def get_all_users(request):
    if not request.user.has_perm('user_profiles.can_get_all_user_profiles'):
        return 403, missing_permission()
    return 200, UserProfile.objects.filter(is_active=True)


@router.post(
    '/create',
    response={
        200: UserProfileSchema,
        400: ErrorsOut
    },
)
def create_user(request, body: UserProfileCreationSchema):
    if not request.user.is_anonymous:
        return 400, {'errors': {'user': ['A session already exists.']}}
    form = UserCreationForm(body.dict())
    if form.is_valid():
        user = form.save()
        send_confirmation_email(user, request)
        django_login(request, user, backend=_LOGIN_BACKEND)
        return 200, user
    else:
        return 400, {'errors': dict(form.errors)}


@router.delete('/remove_user', response={204: None}, auth=django_auth)
def remove_user(request):
    user = UserProfile.objects.get(pk=request.user.id)
    user.is_active = False
    user.save()
    django_logout(request)
    return 204, None


@router.delete(
    '/remove_user/{user_id}',
    response={
        204: None,
        403: ErrorOut,
        404: ErrorOut
    },
    auth=django_auth
)
def remove_user_by_id(request, user_id: int):
    if not request.user.has_perm('user_profiles.can_delete_user'):
        return 403, missing_permission()
    user_query = UserProfile.objects.filter(id=user_id)
    if not user_query.exists():
        return 404, not_found('User')
    user = user_query.get()
    if user.is_admin:
        return 403, {'message': 'Target user is an Admin.'}
    user.is_active = False
    user.save()
    return 204, None


@router.patch(
    '/update',
    response={
        200: UserProfileSchema,
        400: ErrorsOut
    },
    auth=django_auth
)
def update_user(request, body: UserUpdateSchema):
    user = UserProfile.objects.get(id=request.user.id)
    form = UserUpdateForm(body.dict(), instance=user)
    if form.is_valid():
        user = form.save()
        if not user.email_verified:
            send_confirmation_email(user, request)
        return 200, user
    else:
        return 400, {'errors': dict(form.errors)}


@router.patch(
    '/confirm_email',
    response={
        200: None,
        403: ErrorsOut,
        422: ErrorsOut
    }
)
def confirm_email(request, body: EmailConfirmationSchema):
    user = UserProfile.objects.filter(id=body.id)
    if user.exists():
        user = user.get()
        if email_confrimation_token_generator.check_token(user, body.token):
            user.email_verified = True
            user.save()
            return 200
        else:
            return 403, {'errors': {'token': ['Invalid token']}}
    return 422, {'errors': {'user_id': [f'No valid user with id: {body.id}']}}


@router.get(
    '/shipping_address/me',
    response={200: list[UserShippingAddressSchema]},
    auth=django_auth
)
def get_all_signed_user_shipping_addresses(request):
    return 200, UserShippingAddress.objects.filter(user_id=request.user.id)


@router.get(
    '/shipping_address/me/{shipping_address_id}',
    response={200: UserShippingAddressSchema, 404: ErrorsOut},
    auth=django_auth
)
def get_signed_user_shipping_address(request, shipping_address_id: int):
    shipping_address_query = UserShippingAddress.objects.filter(
        id=shipping_address_id,
        user_id=request.user.id
    )
    if shipping_address_query.exists():
        return 200, shipping_address_query.get()
    return 404, {
        'errors': {'shipping_address_id': ['Shipping address not found.']}
    }


@router.post(
    '/shipping_address',
    response={
        200: UserShippingAddressSchema,
        400: ErrorsOut
    },
    auth=django_auth
)
def create_shipping_address(request, body: UserShippingAddressCreateSchema):
    # add user id to form to validate uniqueness
    form_body = body.dict()
    form_body['user_id'] = request.user.id
    form = UserShippingAddressCreationForm(form_body)
    if form.is_valid():
        shipping_address = form.save()
        return 200, shipping_address
    return 400, {'errors': dict(form.errors)}


@router.delete(
    '/shipping_address/{shipping_address_id}',
    response={
        204: None,
        404: ErrorsOut
    },
    auth=django_auth
)
def delete_shipping_address(request, shipping_address_id: int):
    user = UserProfile.objects.get(pk=request.user.id)
    shipping_address_query = user.shipping_addresses.filter(
        id=shipping_address_id
    )
    if shipping_address_query.exists():
        shipping_address = shipping_address_query.get()
        shipping_address.delete()
        return 204, None
    return 404, {'errors': {
        'shipping_address_id': ['Shipping address not found.']}
    }
