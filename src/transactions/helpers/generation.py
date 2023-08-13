from django.conf import settings
from typing import Iterable, Union
from publications.models import PublicationItem, ShoppingCartPointer
from transactions.helpers import PublicationItemWithAmount
from user_profiles.models import UserShippingAddress
from transactions.models import (
    Coupon,
    Transaction,
    TransactionPointer,
    AcountlessTransaction,
    AcountlessTransactionPointer
)
from transactions.schema import TransactionCreateResponseSchema
from utilities.models import get_latest_id
from secrets import randbelow
from datetime import datetime
import hashlib
import requests
import json


def generate_transaction(
    user,
    shipping_address: UserShippingAddress,
    coupon: Union[Coupon, None],
    cart_items: Iterable[ShoppingCartPointer]
) -> tuple[
    int,
    Union[
        TransactionCreateResponseSchema,
        dict[str, str],
        dict[str, list[str]]
    ]
]:
    # Create transaction
    transaction = Transaction(buyer=user, shipping_address=shipping_address)
    # Generate transaction pointers, total price and shallow update pubs.
    price, transaction_pointers, publications = generate_transaction_pointers(
        transaction,
        cart_items
    )
    # Before saving any changes send and confirm payment intent
    discount = 1 if coupon is None else 1 - coupon.discount_percentage / 100
    payment_id, widget_tkn = send_payment_intent(price * discount)
    if payment_id is None or widget_tkn is None:
        return 503, {'message': 'Error generando cobro.'}

    # If everything works then save
    transaction.payment_id = payment_id
    if coupon is not None:
        transaction.coupon = coupon
        coupon.active = False
        coupon.save()
    transaction.save()
    TransactionPointer.objects.bulk_create(
        transaction_pointers,
        len(transaction_pointers)
    )
    PublicationItem.objects.bulk_update(publications, ['reserved'])
    return 200, {'payment_id': payment_id, 'widget_token': widget_tkn}


def generate_accountless_transaction(
    body: dict,
    coupon: Union[Coupon, None]
) -> tuple[
    int,
    Union[
        TransactionCreateResponseSchema,
        dict[str, str],
        dict[str, list[str]]
    ]
]:
    transaction = AcountlessTransaction(
        buyer_name=body["buyer_name"],
        buyer_lastname=body["buyer_lastname"],
        phone_number=body["phone_number"],
        region=body["region"],
        commune=body["commune"],
        address=body["address"]
    )
    publication_item_amount_dict: dict[int, int] = {
        pub['id']: pub['amount']
        for pub in body['publication_items_list']
    }
    publication_items_query = tuple(
        PublicationItem.objects.filter(
            id__in=(item['id'] for item in body['publication_items_list'])
        )
    )
    price, transaction_ptrs, pubs = generate_accountless_transaction_pointers(
        transaction,
        publication_items_query,
        publication_item_amount_dict
    )
    # Before saving any changes send and confirm payment intent
    discount = 1 if coupon is None else 1 - coupon.discount_percentage / 100
    payment_id, widget_tkn = send_payment_intent(price * discount)
    if payment_id is None or widget_tkn is None:
        return 503, {'message': 'Error generando cobro.'}
    # If everything works then save
    transaction.payment_id = payment_id
    if coupon is not None:
        transaction.coupon = coupon
        coupon.active = False
        coupon.save()
    transaction.save()
    AcountlessTransactionPointer.objects.bulk_create(
        transaction_ptrs,
        len(transaction_ptrs)
    )
    PublicationItem.objects.bulk_update(pubs, ['reserved'])
    return 200, {'payment_id': payment_id, 'widget_token': widget_tkn}


def generate_transaction_pointers(
    transaction: Transaction,
    publication_items_with_amount: Iterable[PublicationItemWithAmount]
) -> tuple[int, list[TransactionPointer], list[PublicationItem]]:
    transaction_pointers = list()
    publications = list()
    total_price = 0
    for item in publication_items_with_amount:
        # Create transaction pointer
        transaction_pointers.append(
            TransactionPointer(
                transaction=transaction,
                publication_item=item.pub_item,
                amount=item.amount,
                price_per_unit=item.pub_item.publication.price
            )
        )
        item.pub_item.reserved += item.amount
        publications.append(item.pub_item)
        total_price += item.amount \
            * item.pub_item.publication.price
    return total_price, transaction_pointers, publications


def generate_accountless_transaction_pointers(
    transaction: AcountlessTransaction,
    # publication_items: tuple[PublicationItem],
    # publication_amount_lookup: dict[int, int]
    publication_items_with_amount: Iterable[PublicationItemWithAmount]
) -> tuple[int, list[AcountlessTransactionPointer], list[PublicationItem]]:
    transaction_pointers = list()
    publication_items = list()
    total_price = 0
    for item in publication_items_with_amount:
        # Create transaction pointer
        transaction_pointers.append(
            AcountlessTransactionPointer(
                transaction=transaction,
                publication_item=item.pub_item,
                amount=item.amount,
                price_per_unit=item.pub_item.publication.price
            )
        )
        item.pub_item.reserved += item.amount
        publication_items.append(item.pub_item)
        total_price += item.amount * item.pub_item.publication.price
    return total_price, transaction_pointers, publication_items


def send_payment_intent(
    price: int,
) -> Union[tuple[str, str], tuple[None, None]]:
    payment_intent = {
        'amount': price,
        'currency': 'clp',
        'recipient_account': settings.FINTOC_ACCOUNT
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': settings.FINTOC_KEY
    }
    response = requests.post(
        settings.FINTOC_PAYMENT_URI,
        json=payment_intent,
        headers=headers
    )
    if response.status_code != 201:
        return None, None
    response_info = json.loads(response.text)
    return response_info['id'], response_info['widget_token']


def generate_coupons(
    name: str,
    discount_percentage: float,
    amount: int
) -> list[Coupon]:
    # generate unique batch base coupon name using last coupon id
    base_code = f'coupon-{get_latest_id(Coupon)}'
    # generate coupons
    coupons = []
    # use sha256, the time and a random int to make coupons costly to guess
    sha256 = hashlib.sha256()
    for i in range(amount):
        proto_code = base_code + f'{i}-{datetime.now()}-{randbelow(100000)}'
        sha256.update(bytes(proto_code, 'utf-8'))
        coupon_code = sha256.hexdigest()
        coupons.append(
            Coupon(
                name=name,
                discount_percentage=discount_percentage,
                code=coupon_code
            )
        )
    Coupon.objects.bulk_create(coupons, len(coupons))
    return coupons
