from django.contrib.auth import get_user_model
from ninja import Schema
from ninja.orm import create_schema


UsernameSchemaMixin = create_schema(
    get_user_model(),
    fields=[get_user_model().USERNAME_FIELD]
)

EmailSchemaMixin = create_schema(
    get_user_model(),
    fields=[get_user_model().EMAIL_FIELD]
)

# UserOut = create_schema(
#     get_user_model(),
#     name='UserOut',
#     fields=[
#         'id',
#         get_user_model().USERNAME_FIELD,
#         get_user_model().EMAIL_FIELD,
#     ]
# )


class UserOut(Schema):
    id: int
    username: str
    email: str


class LoginIn(EmailSchemaMixin):
    password: str


class RequestPasswordResetIn(EmailSchemaMixin):
    pass


class SetPasswordIn(EmailSchemaMixin):
    new_password1: str
    new_password2: str
    token: str


class ChangePasswordIn(Schema):
    old_password: str
    new_password1: str
    new_password2: str
