from ninja import Router
from transactions.helpers.confirmation import (
    confirm_transaction_payment,
    get_ambiguous_transaction,
    cancel_transaction_payment
)
from transactions.helpers.validation import validate_signature
from transactions.mail import (
    get_email_and_send,
    send_purchase_in_process_email,
    send_purchase_succeded_email,
    send_purchase_failed_email
)
from transactions.models import Transaction
from transactions.schema import TransactionResolveSchema
from publications.models import ShoppingCartPointer
from utilities.errors import ErrorOut, not_found


router = Router()


@router.post(
    '/resolved',
    response={
        200: None,
        400: None,
        403: None,
        404: ErrorOut
    }
)
def resolve_transaction(request, body: TransactionResolveSchema):
    if not validate_signature(request):
        return 403, None
    data = body.dict()
    transaction, pointer_type = get_ambiguous_transaction(data['id'])
    if transaction is None or pointer_type is None:
        return 404, not_found(
            f'No existe una transaccion con payment_id:{data["id"]}'
        )
    if transaction.status in ('SUCCEDED', 'FAILED'):
        return 400, None
    if data['type'] == 'payment_intent.succeeded':
        confirm_transaction_payment(transaction, pointer_type)
        get_email_and_send(
            request,
            transaction,
            send_purchase_succeded_email
        )
    elif data['type'] in ('payment_intent.failed', 'payment_intent.rejected'):
        transaction.status = 'FAILED'
        transaction.save()
        get_email_and_send(
            request,
            transaction,
            send_purchase_failed_email
        )
    return 200, None


@router.patch(
    '/confirm_request/{payment_id}',
    response={
        200: None,
        404: ErrorOut,
    }
)
def confirm_transaction_request(request, payment_id: str):
    transaction, _ = get_ambiguous_transaction(payment_id)
    if transaction is None:
        return 404, not_found(
            f'No existe una transaccion con payment_id:{payment_id}'
        )
    transaction.status = 'REQUESTED'
    transaction.save()
    if (isinstance(transaction, Transaction)
            and request.user.id == transaction.buyer.id):
        for cart_item in ShoppingCartPointer.objects.filter(
            cart_owner__id=request.user.id
        ):
            cart_item.delete()
    get_email_and_send(request, transaction, send_purchase_in_process_email)
    return 200, transaction


@router.patch(
    '/cancel/{payment_id}',
    response={
        200: None,
        400: ErrorOut,
        404: ErrorOut
    }
)
def cancel_transaction(request, payment_id: str):
    transaction, _ = get_ambiguous_transaction(payment_id)
    if transaction is None:
        return 404, not_found(
            f'No existe una transaccion con payment_id:{payment_id}'
        )
    return cancel_transaction_payment(transaction)
