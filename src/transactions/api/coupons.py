from ninja import Router
from ninja.security import django_auth
from django.contrib.auth import get_user_model
from transactions.models import (
    Coupon
)
from utilities.errors import (
    ErrorOut,
    ErrorsOut,
    missing_permission,
    not_found
)
from transactions.schema import (
    CouponSchema,
    CouponCreationSchema,
    MassCouponCreationSchema
)
from transactions.forms import (
    CouponCreationForm,
    MassCouponCreationForm
)
from transactions.helpers.generation import generate_coupons


router = Router()


@router.get(
    "/all",
    response={200: list[CouponSchema], 403: ErrorOut},
    auth=django_auth
)
def get_all_coupons(request):
    user = get_user_model().objects.get(pk=request.user.id)
    if not user.has_perm('transactions.can_manage_coupon'):
        return 403, missing_permission()
    return 200, Coupon.objects.all()


@router.post(
    '/create',
    response={
        200: CouponSchema,
        400: ErrorsOut,
        403: ErrorOut
    },
    auth=django_auth
)
def create_coupon(request, body: CouponCreationSchema):
    user = get_user_model().objects.get(pk=request.user.id)
    if not user.has_perm('transactions.can_manage_coupon'):
        return 403, missing_permission()
    form = CouponCreationForm(body.dict())
    if form.is_valid():
        coupon = form.save()
        return 200, coupon
    return 400, {'errors': dict(form.errors)}


@router.post(
    '/mass_create',
    response={
        200: list[CouponSchema],
        400: ErrorsOut,
        403: ErrorOut
    },
    auth=django_auth
)
def mass_create_coupon(request, body: MassCouponCreationSchema):
    user = get_user_model().objects.get(pk=request.user.id)
    if not user.has_perm('transactions.can_manage_coupon'):
        return 403, missing_permission()
    form = MassCouponCreationForm(body.dict())
    if not form.is_valid():
        return 400, {'errors': dict(form.errors)}
    coupons = generate_coupons(**body.dict())
    return 200, coupons


@router.patch(
    '/activate/{coupon_id}',
    response={
        200: CouponSchema,
        403: ErrorOut,
        404: ErrorOut
    },
    auth=django_auth
)
def activate_coupon(request, coupon_id: int):
    user = get_user_model().objects.get(pk=request.user.id)
    if not user.has_perm('transactions.can_manage_coupon'):
        return 403, missing_permission()

    coupon_query = Coupon.objects.filter(id=coupon_id)
    if coupon_query.exists():
        coupon = coupon_query.get()
        coupon.active = True
        coupon.save()
        return 200, coupon

    return 404, not_found("Coupon")


@router.patch(
    '/deactivate/{coupon_id}',
    response={
        200: CouponSchema,
        403: ErrorOut,
        404: ErrorOut
    },
    auth=django_auth
)
def deactivate_coupon(request, coupon_id: int):
    user = get_user_model().objects.get(pk=request.user.id)
    if not user.has_perm('transactions.can_manage_coupon'):
        return 403, missing_permission()

    coupon_query = Coupon.objects.filter(id=coupon_id)
    if coupon_query.exists():
        coupon = coupon_query.get()
        coupon.active = False
        coupon.save()
        return 200, coupon

    return 404, not_found("Coupon")


@router.delete(
    '/delete/{coupon_id}',
    response={
        204: None,
        403: ErrorOut,
        404: ErrorOut
    },
    auth=django_auth
)
def delete_coupon(request, coupon_id: int):
    user = get_user_model().objects.get(pk=request.user.id)
    if not user.has_perm('transactions.can_manage_coupon'):
        return 403, missing_permission()

    coupon_query = Coupon.objects.filter(id=coupon_id)
    if coupon_query.exists():
        coupon = coupon_query.get()
        coupon.delete()
        return 204, None
    return 404, not_found("Coupon")


@router.get(
    '/validate/{coupon_code}',
    response={
        200: CouponSchema,
        404: ErrorOut
    }
)
def validate_coupon(request, coupon_code):
    coupon_query = Coupon.objects.filter(code=coupon_code, active=True)
    if coupon_query.exists():
        coupon = coupon_query.get()
        return 200, coupon
    return 404, not_found("Coupon")
