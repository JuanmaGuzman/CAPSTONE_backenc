from ninja import Router
from django.conf import settings
from ninja.security import django_auth
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator

from django.contrib.auth.forms import (
    SetPasswordForm,
    PasswordChangeForm
)

from .forms import VerifiedEmailPasswordResetForm

from django.contrib.auth import (
    login as django_login,
    logout as django_logout,
    authenticate
)

from .schema import (
    UserOut,
    LoginIn,
    RequestPasswordResetIn,
    SetPasswordIn,
    ChangePasswordIn
)

from utilities.errors import ErrorsOut

router = Router()
_TGS = ['User Auth']
_LOGIN_BACKEND = 'user_auth.backend.EmailBackend'


@router.post('/', tags=_TGS, response={200: UserOut, 403: None}, auth=None)
def login(request, data: LoginIn):
    user = authenticate(backend=_LOGIN_BACKEND, **data.dict())
    if user is not None and user.is_active:
        django_login(request, user, backend=_LOGIN_BACKEND)
        return user
    return 403, None


@router.delete('/', tags=_TGS, response={204: None}, auth=django_auth)
def logout(request):
    django_logout(request)
    return 204, None


@router.get('/me', tags=_TGS, response=UserOut, auth=django_auth)
def me(request):
    return request.user


@router.post('/request_password_reset',
             tags=_TGS,
             response={204: None},
             auth=None)
def request_password_reset(request, data: RequestPasswordResetIn):
    form = VerifiedEmailPasswordResetForm(data.dict())
    if form.is_valid():
        front_url = settings.FRONTEND_URL + '/profile/reset-password'
        form.save(
            subject_template_name="password_reset_subject.txt",
            email_template_name="password_reset_email.html",
            request=request,
            extra_email_context=({'frontend_url': front_url}),
            from_email=settings.EMAIL_DEFAULT_FROM
        )
    return 204, None


@router.post('/reset_password',
             tags=_TGS,
             response={200: None, 403: ErrorsOut, 422: None},
             auth=None)
def reset_password(request, data: SetPasswordIn):
    user_field = get_user_model().EMAIL_FIELD
    user_data = {user_field: getattr(data, user_field)}
    user = get_user_model().objects.filter(**user_data)

    if user.exists():
        user = user.get()
        if default_token_generator.check_token(user, data.token):
            form = SetPasswordForm(user, data.dict())
            if form.is_valid():
                form.save()
                # django_login(request, user, backend=_LOGIN_BACKEND)
                # return user
                return 200, None
            return 403, {'errors': dict(form.errors)}
    return 422, None


@router.post('/change_password',
             tags=_TGS,
             response={200: None, 403: ErrorsOut},
             auth=django_auth)
def change_password(request, data: ChangePasswordIn):
    form = PasswordChangeForm(request.user, data.dict())
    if form.is_valid():
        form.save()
        update_session_auth_hash(request, request.user)
        return 200
    return 403, {'errors': dict(form.errors)}
