from ninja.orm import create_schema
from django.contrib.auth import get_user_model
from user_profiles.models import UserShippingAddress


UserSchemaMixin = create_schema(
    get_user_model(),
    fields=[
        'username',
        'email',
        'first_name',
        'last_name',
        'phone_number',
        'rut',
        'birthdate'
    ]
)


UserProfileSchema = create_schema(
    get_user_model(),
    name='UserProfile',
    fields=[
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'phone_number',
        'rut',
        'birthdate'
    ],
    custom_fields=[
        ('is_admin', bool, None),
        ('is_seller', bool, None)
    ]
)


class UserProfileCreationSchema(UserSchemaMixin):
    password1: str
    password2: str


EmailConfirmationSchema = create_schema(
    get_user_model(),
    name='EmailConfirmation',
    fields=['id'],
    custom_fields=[('token', str, None)]
)


UserUpdateSchema = create_schema(
    get_user_model(),
    name='UserUpdate',
    fields=[
        'username',
        'email',
        'first_name',
        'last_name'
    ]
)


PublicUserProfileSchema = create_schema(
    get_user_model(),
    name='PublicUserProfile',
    fields=['email', 'first_name', 'last_name']
)


UserShippingAddressCreateSchema = create_schema(
    UserShippingAddress,
    name='UserShippingAddressCreate',
    exclude=['id', 'user']
)


UserShippingAddressSchema = create_schema(
    UserShippingAddress,
    name='UserShippingAddress',
)
