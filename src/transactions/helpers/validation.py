from django.conf import settings
from transactions.models import Coupon
from transactions.forms import AccountlessTransactionCreationForm
from user_profiles.models import UserProfile
from publications.models import PublicationItem, ShoppingCartPointer
from transactions.helpers import PublicationItemWithAmount
from user_profiles.models import UserShippingAddress
from typing import Type, Union, Iterable
from hashlib import sha256
import hmac


def validate_transaction_shopping_cart(
    buyer: Type[UserProfile]
) -> dict[str, list[str]]:
    error_dict = {}
    cart_items = ShoppingCartPointer.objects.filter(cart_owner_id=buyer.id)
    if not cart_items.exists():
        error_dict = error_dict | {
            'cart_items': ['Usuario no tiene items en su carro de compras.']
        }
    return error_dict


def validate_accountless_transaction_publications(
    publication_items_list: list[dict[str, int]]
) -> dict[str, list[str]]:
    error_dict = {}
    # publication_amount_dict = {
    #     pub['id']: pub['amount'] for pub in publication_items_list
    # }
    publication_items_query = PublicationItem.objects.filter(
        id__in=(item['id'] for item in publication_items_list)
    )
    if not publication_items_query.exists():
        error_dict = error_dict | {'publications': ['No hay publicaciones.']}
    # for pub_item in publication_items_query:
    #     if pub_item.available < publication_amount_dict[pub_item.id]:
    #         error_dict = error_dict | {
    #             f'publication_{pub_item.id}': [
    #                 'No hay suficientes unidades disponibles.'
    #             ]
    #         }
    return error_dict


def validate_publication_item_availablity(
    publication_items_with_amount: Iterable[PublicationItemWithAmount]
) -> tuple[int, Union[None, dict]]:
    error_dict = {}
    for item in publication_items_with_amount:
        error_list = []
        if item.pub_item.available < item.amount:
            error_list.append(
                'No hay suficientes unidades disponibles.'
            )
        if not item.pub_item.publication.is_active:
            error_list.append(
                'Publicación no está disponible.'
            )
        if len(error_list) > 0:
            error_dict = error_dict | {
                f'publication_{item.pub_item.id}': error_list
            }
    if error_dict:
        return 400, {'errors': error_dict}
    return 1, None


def validate_signature(request) -> bool:
    timestamp, event_signature = [
        x.split('=')[1]
        for x in request.headers.get('Finctoc-Signature').split(',')
    ]
    message = f'{timestamp}.{request.body().decode("utf-8")}'
    signature = hmac.new(
        settings.fintoc_webhook_secret.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=sha256
    ).hexdigest()
    return hmac.compare_digest(signature, event_signature)


def validate_coupon(coupon_id) -> bool:
    if coupon_id is None:
        return True
    coupon_query = Coupon.objects.filter(
        id=coupon_id,
        active=True,
        transaction__isnull=True,
        accountless_transaction__isnull=True
    )
    if coupon_query.exists():
        return True
    return False


def validate_transaction(user, body) -> tuple[int, Union[dict, None]]:
    shipping_address_query = UserShippingAddress.objects.filter(
        id=body.shipping_address_id,
        user_id=user.id
    )
    if not shipping_address_query.exists():
        return 404, {'errors': {
            'shipping_address_id': ['Shipping address not found.']}
        }
    shopping_cart_validation = validate_transaction_shopping_cart(user)
    if not validate_coupon(body.coupon_id):
        return 404, {'errors': {
            'shipping_address_id': ['Shipping address not found.']}
        }
    if shopping_cart_validation:
        return 400, {'errors': shopping_cart_validation}
    return 0, None


def validate_accountless_transaction(
    body
) -> tuple[int, Union[int, Union[dict, None]]]:
    form = AccountlessTransactionCreationForm(body.dict())
    if not form.is_valid():
        return 400, {'errors': dict(form.errors)}
    if not validate_coupon(body.coupon_id):
        return 404, {'errors': {
            'shipping_address_id': ['Shipping address not found.']}
        }
    publications_validation = validate_accountless_transaction_publications(
        body.dict()['publication_items_list']
    )
    if publications_validation:
        return 400, {'errors': publications_validation}
    return 0, None
