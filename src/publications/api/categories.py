from ninja import Router, File
from ninja.files import UploadedFile
from publications.models import Category
from publications.schema import CategorySchema, CategoryCreationSchema
from publications.forms import CategoryCreationForm
from utilities.errors import (
    ErrorOut,
    ErrorsOut,
    missing_permission,
    not_found
)
from publications.helpers.generation import upload_category_image
from publications.helpers.validation import validate_files
from ninja.security import django_auth
from typing import Union


router = Router()


@router.get("/all", response={200: list[CategorySchema]})
def show_categories(request):
    return 200, Category.objects.all()


@router.post(
    '/create',
    response={
        200: CategorySchema,
        400: Union[ErrorOut, ErrorsOut],
        403: ErrorsOut
    },
    auth=django_auth
)
def add_category(
    request,
    body: CategoryCreationSchema,
    file: UploadedFile = File(...)
):
    if not request.user.has_perm('publications.can_allow'):
        return 403, missing_permission()
    if not validate_files([file]):
        error_mesage = 'Only upload 1 file of at most 10MB each' \
            + ' with extenstion "jpeg", "jpg", "png".'
        return 400, {'message': error_mesage}

    form = CategoryCreationForm(body.dict())
    if form.is_valid():
        category = form.save()
        upload_category_image(category, file)
        return 200, category

    return 400, {'errors': dict(form.errors)}


@router.delete(
    '/remove/{category_id}',
    response={
        204: None,
        403: ErrorOut,
        404: ErrorOut,
    },
    auth=django_auth
)
def delete_category(request, category_id: int):
    if not request.user.has_perm('publications.can_allow'):
        return 403, missing_permission()
    category_query = Category.objects.filter(id=category_id)
    if not category_query.exists():
        return 404, not_found("Category")
    category = category_query.get()
    if category.items.all().exists():
        return 400, {'message', 'Category is in use.'}
    category.delete()
    return 204, None
