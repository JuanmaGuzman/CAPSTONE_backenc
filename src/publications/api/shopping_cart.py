from ninja import Router
from django.contrib.auth import get_user_model
from ninja.security import django_auth
from publications.models import PublicationItem, ShoppingCartPointer
from publications.schema import (
    ShoppingCartDetailSchema,
    ShoppingCartSchema
)
from utilities.errors import (
    ErrorOut,
    inactive_publication,
    not_found
)


router = Router()


@router.post(
    '/add_to_cart/{publication_item_id}',
    response={
        200: None,
        400: ErrorOut,
        404: ErrorOut,
        403: None
    },
    auth=django_auth
)
def add_to_cart(request, publication_item_id: int, body: ShoppingCartSchema):
    user = get_user_model().objects.get(pk=request.user.id)
    publication_item_query = PublicationItem.objects.filter(
        id=publication_item_id
    )

    if not publication_item_query.exists():
        return 404, not_found('Publication item')

    publication_item = publication_item_query.get()
    exist_in_cart = ShoppingCartPointer.objects.filter(
        cart_owner=user, publication_item=publication_item
    )
    if exist_in_cart:
        if publication_item.publication.is_active:
            ShoppingCartPointer.objects.filter(
                cart_owner=user,
                publication_item=publication_item
            ).update(amount=body.dict()["amount"])
            return 200, None
        # informar que la publicación se encuentra inactiva
        return 400, inactive_publication()
    else:
        if publication_item.publication.is_active:
            shopping_cart = ShoppingCartPointer(
                cart_owner=user,
                publication_item=publication_item,
                amount=body.dict()["amount"]
            )
            shopping_cart.save()
            return 200, None
        # informar que la publicacion se encuentra inactiva
        return 400, inactive_publication()


@router.delete(
    '/remove_from_cart/{publication_item_id}',
    response={
        204: None,
        404: ErrorOut
    },
    auth=django_auth
)
def remove_from_cart(request, publication_item_id: int):
    user = get_user_model().objects.get(pk=request.user.id)
    publication_item_query = PublicationItem.objects.filter(
        id=publication_item_id
    )
    if not publication_item_query.exists():
        return 404, not_found('Publication item')
    publication_item = publication_item_query.get()
    shopping_cart_query = ShoppingCartPointer.objects.filter(
        cart_owner=user,
        publication_item=publication_item
    )
    if shopping_cart_query.exists():
        shopping_cart_item = shopping_cart_query.get()
        shopping_cart_item.delete()
        return 204, None
    return 404, not_found('Publication item')


@router.delete(
    '/remove_all_cart/me',
    response={
        200: None
    },
    auth=django_auth
)
def remove_all_cart_from_active_user(request):
    user = get_user_model().objects.get(pk=request.user.id)
    in_cart = ShoppingCartPointer.objects.filter(cart_owner=user).all()
    for pub in in_cart:
        pub.delete()
    return 200, None


@router.get(
    "/shopping_cart/me",
    response={200: list[ShoppingCartDetailSchema]},
    auth=django_auth
)
def show_shopping_cart_user(request):
    user = get_user_model().objects.get(pk=request.user.id)
    return ShoppingCartPointer.objects.filter(cart_owner=user.id)


@router.get(
    "/user_shopping_cart/{user_id}",
    response={
        200: list[ShoppingCartDetailSchema],
        403: ErrorOut
    },
    auth=django_auth
)
def show_shopping_cart_from_specific_user(request, user_id: int):
    # Agregar que es solo para admins.
    # Por mientras por seguridad solo ver propio carrito (JT).
    if user_id != request.user.id:
        return 403, {'message': 'Solo es posible ver tu propio carrito.'}
    return ShoppingCartPointer.objects.filter(cart_owner=user_id)
