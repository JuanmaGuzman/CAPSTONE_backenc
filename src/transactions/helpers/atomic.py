from django.contrib.auth import get_user_model
from django.db import transaction
from publications.models import PublicationItem
from transactions.models import Transaction, AcountlessTransaction
from transactions.helpers import get_publication_items_with_amount_and_lock
from transactions.helpers.validation import (
    validate_publication_item_availablity
)
from transactions.helpers.generation import (
    generate_transaction_pointers,
    generate_accountless_transaction_pointers
)


@transaction.atomic
def atomic_transaction_generation(user):
    user = get_user_model().objects.get(pk=user.id)
    # Get publication_items with amount and lock them
    pub_items_id_with_amount = {
        cart_item.publication_item.id: cart_item.amount
        for cart_item in user.cart_items.all()
    }
    pub_items_with_amount = get_publication_items_with_amount_and_lock(
        pub_items_id_with_amount
    )
    # Validate availability
    _, error_or_none = validate_publication_item_availablity(
        pub_items_with_amount
    )
    if error_or_none is not None:
        return error_or_none, None, None, None
    # Create transaction
    transaction = Transaction(buyer=user)
    # Generate transaction pointers, total price and shallow update pubs.
    price, transaction_pointers, publications = generate_transaction_pointers(
        transaction,
        pub_items_with_amount
    )
    PublicationItem.objects.bulk_update(publications, ['reserved'])
    return None, price, transaction, transaction_pointers


@transaction.atomic
def atomic_publication_items_reversal(transaction_pointers):
    publication_items = set()
    for pointer in transaction_pointers:
        pointer.publication_item.reserved -= pointer.amount
        publication_items.add(pointer.publication_item)
    PublicationItem.objects.bulk_update(publication_items, ['reserved'])


@transaction.atomic
def atomic_accountless_transaction_generation(body):
    # Get publication_items with amount and lock them
    pub_items_id_with_amount: dict[int, int] = {
        pub['id']: pub['amount']
        for pub in body['publication_items_list']
    }
    pub_items_with_amount = get_publication_items_with_amount_and_lock(
        pub_items_id_with_amount
    )
    # Validate availability
    _, error_or_none = validate_publication_item_availablity(
        pub_items_with_amount
    )
    if error_or_none is not None:
        return error_or_none, None, None, None
    # Create transaction
    transaction = AcountlessTransaction(
        buyer_name=body["buyer_name"],
        buyer_lastname=body["buyer_lastname"],
        phone_number=body["phone_number"],
        region=body["region"],
        commune=body["commune"],
        address=body["address"]
    )
    price, transaction_ptrs, pubs = generate_accountless_transaction_pointers(
        transaction,
        pub_items_with_amount
    )
    PublicationItem.objects.bulk_update(pubs, ['reserved'])
    return None, price, transaction, transaction_ptrs


@transaction.atomic
def atomic_save_transaction(
    transaction,
    transaction_pointers,
    transaction_pointer_model,
    coupon=None
):
    if coupon is not None:
        transaction.coupon = coupon
        coupon.active = False
        coupon.save()
    transaction.save()
    transaction_pointer_model.objects.bulk_create(
        transaction_pointers,
        len(transaction_pointers)
    )
