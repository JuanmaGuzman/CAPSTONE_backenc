from django.contrib.auth import get_user_model
from ninja.security import django_auth
from ninja import Router, File
from ninja.files import UploadedFile
from datetime import date
from publications.helpers.generation import (
    upload_publication_images,
    generate_items
)
from publications.helpers.validation import (
    validate_publication_items,
    validate_publication
)
from publications.helpers.validation import validate_files
from publications.helpers.suggestions import get_user_recommendations
from publications.mail import send_publication_rejection_email
from publications.models import (
    PublicationItem,
    Publication,
    Item,
)
from publications.schema import (
    ItemConflictErrorSchema,
    PublicationItemAddSchema,
    PublicationSchema,
    PublicationItemSchema,
    PublicationUpdateSchema,
    PublicationItemUpdateSchema,
    PublicationCreationSchema,
    SuccinctPublicationSchema
)
from publications.forms import PublicationCreationForm
from utilities.errors import (
    ErrorsOut,
    ErrorOut,
    not_found,
    missing_permission,
)
from typing import Union

router = Router()


@router.get(
    '/recommendations',
    response={
        200: list[SuccinctPublicationSchema]
    },
    auth=django_auth
)
def get_publication_recommendations(request, amount: int):
    return 200, get_user_recommendations(request.user.id, amount)


@router.get(
    "/all",
    response={
        200: list[SuccinctPublicationSchema],
        403: ErrorOut
    },
    auth=django_auth
)
def show_publications(request):
    user = get_user_model().objects.get(pk=request.user.id)
    if not user.has_perm('publications.can_allow'):
        return 403, missing_permission()
    return 200, Publication.objects.all()


@router.get(
    "/all/{user_id}",
    response={
        200: list[SuccinctPublicationSchema],
        403: ErrorOut,
        404: ErrorOut
    },
    auth=django_auth
)
def show_publications_user(request, user_id: int):
    user = get_user_model().objects.get(pk=request.user.id)
    perm_1 = user.has_perm('publications.can_allow')
    perm_2 = user.has_perm('publications.can_create')
    perm_3 = (int(request.user.id) == int(user_id))
    if not (perm_1 or (perm_2 and perm_3)):
        return 403, missing_permission()
    publications = Publication.objects.filter(
        seller=user_id,
        is_active=True
    )
    if not publications.exists():
        return 404, not_found("Publications for that User")
    return 200, publications


@router.get(
    "/active",
    response={
        200: list[SuccinctPublicationSchema]
    }
)
def show_active_publications(request):
    return 200, Publication.objects.filter(is_active=True)


@router.get(
    "/pending",
    response={
        200: list[SuccinctPublicationSchema],
        403: ErrorOut
    },
    auth=django_auth
)
def show_inactive_publications(request):
    user = get_user_model().objects.get(pk=request.user.id)
    if not user.has_perm('publications.can_allow'):
        return 403, missing_permission()
    return 200, Publication.objects.filter(is_accepted=False)


@router.get(
    '/obtener/{publication_id}',
    response={
        200: PublicationSchema,
        404: ErrorOut
    }
)
def show_specific_publication(request, publication_id: int):
    publication_search = Publication.objects.filter(
        id=publication_id,
        is_active=True
    ).first()
    if publication_search is None:
        return 404, not_found("Publication")
    return 200, publication_search


@router.get(
    '/obtener_as_admin/{publication_id}',
    response={
        200: PublicationSchema,
        404: ErrorOut
    },
    auth=django_auth
)
def show_specific_publication_as_admin(request, publication_id: int):
    publication_search = Publication.objects.filter(
        id=publication_id
    ).first()
    if publication_search is None:
        return 404, not_found("Publication")
    return 200, publication_search


@router.post(
    '/create',
    response={
        201: PublicationSchema,
        400: Union[ErrorOut, ErrorsOut],
        409: ItemConflictErrorSchema,
        403: ErrorOut
    },
    auth=django_auth
)
def create_publication(
    request,
    body: PublicationCreationSchema,
    files: list[UploadedFile] = File(...)
):
    # Validate permissions
    user = get_user_model().objects.get(pk=request.user.id)
    if not user.has_perm('publications.can_create'):
        return 403, missing_permission()
    # Validate publication info
    code, error_or_none = validate_publication(user.id, body.dict())
    if error_or_none is not None:
        return code, error_or_none
    # Validate publication items
    code, error_or_none = validate_publication_items(user.id, body.dict())
    if error_or_none is not None:
        return code, error_or_none
    # Validate publication
    form = PublicationCreationForm(
        {'price': body.price, 'description': body.description}
    )
    if not form.is_valid():
        return 400, {'errors': dict(form.errors)}
    # Validate publications images
    if not validate_files(files):
        error_mesage = 'Only upload 5 or less images of at most 10MB each' \
            + ' with extenstion "jpeg", "jpg" or "png".'
        return 400, {'message': error_mesage}
    # Generate publication
    publication = Publication.objects.create(
        seller=user,
        price=body.price,
        description=body.description,
        publish_date=date.today()
    )
    # Generate publication items
    generate_items(publication, body.dict())
    # Upload images
    upload_publication_images(publication, files)
    return 201, publication


@router.post(
    '/add_publication_item/{publication_id}',
    response={
        200: PublicationSchema,
        400: ErrorsOut,
        403: ErrorOut,
        404: ErrorOut
    },
    auth=django_auth
)
def add_publication_item(
    request,
    publication_id: int,
    body: PublicationItemAddSchema
):
    # Validate permissions
    user = get_user_model().objects.get(pk=request.user.id)
    if not user.has_perm('publications.can_create'):
        return 403, missing_permission()
    # Validate publication
    publication_query = Publication.objects.filter(
        pk=publication_id,
        seller_id=user.id
    )
    if not publication_query.exists():
        return 404, not_found('Publication')
    # Generate acceptable interface for validation
    publication = publication_query.get()
    item_general_info = publication.general_item_info
    publication_info = {
        'item_name': item_general_info['name'],
        'item_brand': item_general_info['brand'],
        'item_category_id': item_general_info['category'].id,
        'publication_items': body.dict()['publication_items']
    }
    # Validate publication items
    code, error_or_none = validate_publication_items(user.id, publication_info)
    if error_or_none is not None:
        return code, error_or_none
    # Generate new items
    generate_items(publication, publication_info)
    return 200, publication


@router.patch(
    '/update_publication/{pub_id}',
    response={
        200: PublicationSchema,
        400: ErrorsOut,
        403: ErrorOut,
        404: ErrorOut
    },
    auth=django_auth
)
def update_publication(request, pub_id: int, body: PublicationUpdateSchema):
    # Validate permission
    user = get_user_model().objects.get(pk=request.user.id)
    if not user.has_perm('publications.can_update'):
        return 403, missing_permission()
    # Query publication
    publication_query = Publication.objects.filter(
        id=pub_id,
        seller_id=user.id
    )
    if not publication_query.exists():
        return 404, not_found("Publication you are trying to update")
    publication = publication_query.get()
    # Validate ownership
    if user.id != publication.seller.id:
        return 403, missing_permission()
    # Update
    publication_dict = {
        "price": body.price,
        "description": body.description
    }
    publication_form = PublicationCreationForm(
        publication_dict,
        instance=publication
    )
    if publication_form.is_valid():
        publication_form.save()
        publication.refresh_from_db()
        return 200, publication
    return 400, {'errors': dict(publication_form.errors)}


@router.patch(
    '/update_publication_item/{pub_item_id}',
    response={
        200: PublicationItemSchema,
        400: ErrorOut,
        403: ErrorOut,
        404: ErrorOut
    },
    auth=django_auth
)
def update_publication_item(
    request,
    pub_item_id: int,
    body: PublicationItemUpdateSchema
):
    # Validate permission
    user = get_user_model().objects.get(pk=request.user.id)
    if not user.has_perm('publications.can_update'):
        return 403, missing_permission()
    # Query publication
    publication_item_query = PublicationItem.objects.filter(
        id=pub_item_id,
        publication__seller_id=user.id
    )
    if not publication_item_query.exists():
        return 404, not_found("Publication item you are trying to update")
    publication_item = publication_item_query.get()
    # Validate amount
    if body.amount > publication_item.reserved:
        publication_item.amount = body.amount
        publication_item.save()
        return 200, publication_item
    return 400, {
        'message': 'Existen reservas superiores a la cantidad entregada.'
    }


@router.delete(
    '/remove_publication/{publication_id}',
    response={
        204: None,
        403: ErrorOut,
        404: ErrorOut
    },
    auth=django_auth
)
def remove_publication(request, publication_id: int):
    publication_query = Publication.objects.filter(
        id=publication_id,
        is_active=True
    )
    if not publication_query.exists():
        return 404, not_found('Publication')
    publication = publication_query.get()

    is_admin = request.user.has_perm('publications.can_allow')
    is_owner = publication.seller.id == request.user.id
    if not (is_admin or is_owner):
        return 403, missing_permission()

    publication.is_active = False
    publication.save()
    return 204, None


@router.patch(
    '/accept/{publication_id}',
    response={
        200: PublicationSchema,
        403: ErrorOut,
        404: ErrorOut
    },
    auth=django_auth
)
def accept_publication(request, publication_id: int):
    if not request.user.has_perm('publications.can_allow'):
        return 403, missing_permission()
    publication_query = Publication.objects.filter(
        id=publication_id,
        is_accepted=False
    )
    if publication_query.exists():
        publication = publication_query.get()
        publication.is_active = True
        publication.is_accepted = True
        publication.save()
        return 200, publication
    return 404, not_found('Publication')


@router.delete(
    '/reject/{publication_id}',
    response={
        204: None,
        403: ErrorOut,
        404: ErrorOut
    },
    auth=django_auth
)
def reject_publication(request, publication_id: int):
    if not request.user.has_perm('publications.can_allow'):
        return 403, missing_permission()

    publication_query = Publication.objects.filter(
        id=publication_id,
        is_accepted=False
    )
    if publication_query.exists():
        publication = publication_query.get()
        send_publication_rejection_email(publication, request)
        pub_item_id_and_item_tuples = [
            (pub_item.id, pub_item.item)
            for pub_item in publication.publication_items.all()
        ]
        publication.delete()
        for pub_item_id, item in pub_item_id_and_item_tuples:
            if not item.referenced_by_others(pub_item_id):
                item.delete()
        return 204, None
    return 404, not_found('Publication')


@router.get("/existing_brands", response={200: list[str]})
def show_brands(request):
    brands = Item.objects.values('brand').distinct()
    return 200, [brand['brand'] for brand in brands]
