from ninja import Router
from ninja.security import django_auth
from django.contrib.auth import get_user_model
from django.db import transaction
from transactions.models import (
    Coupon,
    Transaction,
    TransactionPointer,
    AcountlessTransactionPointer
)
from transactions.helpers.generation import send_payment_intent
from transactions.helpers.validation import (
    validate_transaction,
    validate_accountless_transaction
)
from transactions.helpers.atomic import (
    atomic_accountless_transaction_generation,
    atomic_publication_items_reversal,
    atomic_save_transaction,
    atomic_transaction_generation
)
from transactions.schema import (
    AllSellerTransactionsSchema,
    TransactionSchema,
    TransactionAcountlessCreateSchema,
    TransactionCreateResponseSchema,
    TransactionCreateSchema
)
from user_profiles.models import UserShippingAddress
from utilities.errors import (
    ErrorOut,
    ErrorsOut
)


router = Router()


@router.get(
    '/my-purchases',
    response={200: list[TransactionSchema]},
    auth=django_auth
)
def get_my_purchases(request):
    transactions = Transaction.objects.filter(
        buyer_id=request.user.id,
        status='SUCCEDED'
    )
    return 200, transactions


@router.get(
    '/my-sells',
    response={200: AllSellerTransactionsSchema},
    auth=django_auth
)
def get_my_sells(request):
    transactions = TransactionPointer.objects.filter(
        publication_item__publication__seller_id=request.user.id,
        transaction__status='SUCCEDED'
    )
    accountless_transactions = AcountlessTransactionPointer.objects.filter(
        publication_item__publication__seller_id=request.user.id,
        transaction__status='SUCCEDED'
    )
    return 200, {
        'transaction_pointers': list(transactions),
        'accountless_transaction_pointers': list(accountless_transactions)
    }


@router.post(
    '/create/',
    response={
        200: TransactionCreateResponseSchema,
        400: ErrorsOut,
        404: ErrorsOut,
        503: ErrorOut
    },
    auth=django_auth
)
@transaction.non_atomic_requests
def create_transaction(request, body: TransactionCreateSchema):
    code, error_or_none = validate_transaction(request.user, body)
    if error_or_none is not None:
        return code, error_or_none
    user = get_user_model().objects.get(pk=request.user.id)
    (
        error_or_none,
        price,
        transaction_obj,
        transaction_pointers
    ) = atomic_transaction_generation(user)
    if error_or_none is not None or price is None or transaction_obj is None:
        return 400, error_or_none

    shipping_address = UserShippingAddress.objects.filter(
        id=body.shipping_address_id
    ).get()
    coupon = Coupon.objects.get(
        pk=body.coupon_id
    ) if body.coupon_id is not None else None
    # Attempt to make payment
    discount = 1 if coupon is None else 1 - coupon.discount_percentage / 100
    payment_id, widget_tkn = send_payment_intent(price * discount)
    # If something goes wrong revert changes
    if payment_id is None or widget_tkn is None:
        atomic_publication_items_reversal(transaction_pointers)
        return 503, {'message': 'Error generando cobro.'}
    # If everything works then save
    transaction_obj.shipping_address = shipping_address
    transaction_obj.payment_id = payment_id
    atomic_save_transaction(
        transaction_obj,
        transaction_pointers,
        TransactionPointer,
        coupon
    )
    return 200, {'payment_id': payment_id, 'widget_token': widget_tkn}


@router.post(
    '/create_acountless/',
    response={
        200: TransactionCreateResponseSchema,
        400: ErrorsOut,
        404: ErrorsOut,
        503: ErrorOut
    }
)
def create_accountless_transaction(
    request,
    body: TransactionAcountlessCreateSchema
):
    code, error_or_none = validate_accountless_transaction(body)
    if error_or_none is not None:
        return code, error_or_none
    (
        error_or_none,
        price,
        transaction_obj,
        transaction_pointers
    ) = atomic_accountless_transaction_generation(body.dict())
    if error_or_none is not None or price is None or transaction_obj is None:
        return 400, error_or_none

    coupon = Coupon.objects.get(
        pk=body.coupon_id
    ) if body.coupon_id is not None else None
    # Attempt to make payment
    discount = 1 if coupon is None else 1 - coupon.discount_percentage / 100
    payment_id, widget_tkn = send_payment_intent(price * discount)
    # If something goes wrong revert changes
    if payment_id is None or widget_tkn is None:
        atomic_publication_items_reversal(transaction_pointers)
        return 503, {'message': 'Error generando cobro.'}
    # If everything works then save
    transaction_obj.payment_id = payment_id
    atomic_save_transaction(
        transaction_obj,
        transaction_pointers,
        AcountlessTransactionPointer,
        coupon
    )
    return 200, {'payment_id': payment_id, 'widget_token': widget_tkn}
    # return generate_accountless_transaction(body.dict(), coupon)
