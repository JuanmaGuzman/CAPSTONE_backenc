from conf import settings
from ninja.files import UploadedFile
from publications.models import Item, Publication, PublicationItem
from publications.forms import ItemCreationForm
from typing import Union
from os import path


def check_for_duplicate_sku(
    pub_items: dict
) -> tuple[bool, Union[set[str], None]]:
    sku_list = [item['sku'] for item in pub_items]
    sku_set = set(sku_list)
    if len(sku_list) != len(sku_set):
        return True, None
    return False, sku_set


def check_for_item_conflict(
    publication: dict,
    sku_set: set[str]
) -> tuple[bool, list[dict]]:
    # Store conflicts in list
    error_list = []
    # Get existing items
    item_query = (
        Item.objects.select_related()
    ).filter(sku__in=sku_set)
    # Create publication item info
    proto_pub_item = {
        'name': publication['item_name'].lower(),
        'brand': publication['item_brand'].lower(),
        'category_id': publication['item_category_id']
    }
    # Iterate over items to look for conflicts
    for pub_item in publication['publication_items']:
        pub_item_info = proto_pub_item | {
            'size': pub_item['size'].lower(),
            'color': pub_item['color'].lower(),
            'sku': pub_item['sku']
        }
        existing_item_query = item_query.filter(sku=pub_item['sku'])
        if existing_item_query.exists():
            item_info = existing_item_query.get().serialize()
            if item_info != pub_item_info:
                error_list.append(
                    {'current_item': item_info, 'item_in_form': pub_item_info}
                )
    if len(error_list) != 0:
        return True, error_list
    return False, []


def check_item_information(publication) -> tuple[bool, Union[dict, None]]:
    error_dict = {}
    # Check publication_item is not empty
    if len(publication['publication_items']) == 0:
        return True, {'publication_items': ['List can not be empty.']}
    # Check if publication item is valid
    proto_pub_item = {
        'name': publication['item_name'].lower(),
        'brand': publication['item_brand'].lower(),
        'category_id': publication['item_category_id']
    }
    for i, pub_item in enumerate(publication['publication_items']):
        pub_item_info = proto_pub_item | {
            'size': pub_item['size'].lower(),
            'color': pub_item['color'].lower(),
            'sku': pub_item['sku']
        }
        form = ItemCreationForm(pub_item_info)
        if not form.is_valid() or not isinstance(pub_item['amount'], int):
            error_dict[i] = ['Invalid parameters.']
    if error_dict:
        return True, error_dict
    return False, None


def check_for_duplicate_pub(
    user_id,
    sku_set: set[str]
) -> tuple[bool, dict]:
    pub_query = PublicationItem.objects.filter(
        item__sku__in=sku_set,
        publication__seller_id=user_id
    )
    if pub_query.exists():
        return True, {
            pub.item.sku: ['User has publication with this item already.']
            for pub in pub_query.all()
        }
    return False, {}


def validate_publication(
    user_id,
    body: dict
) -> tuple[int, Union[dict, None]]:
    publication_query = Publication.objects.filter(
        seller_id=user_id,
        is_active=True,
        publication_items__item__name=body['item_name'],
        publication_items__item__brand=body['item_brand']
    )
    if publication_query.exists():
        error_message = 'Publication for items with this name and brand' \
            + 'already exist.'
        return 400, {'message': error_message}
    return 1, None


def validate_publication_items(
    user_id: int,
    body: dict
) -> tuple[int, Union[dict, None]]:
    # Check item information format
    format_error_found, errors = check_item_information(body)
    if format_error_found:
        return 400, {'errors': errors}
    # Check for duplicate sku
    pub_items = body['publication_items']
    duplicate_found, sku_set = check_for_duplicate_sku(pub_items)
    if duplicate_found or sku_set is None:
        return 400, {'message': 'Duplicate sku.'}
    # Check for conflicts with existing items
    conflict_found, conflict_list = check_for_item_conflict(body, sku_set)
    if conflict_found:
        return 409, {'conflicts': conflict_list}
    # Check for duplicate publication item
    duplicate_pub_found, dup_dict = check_for_duplicate_pub(user_id, sku_set)
    if duplicate_pub_found:
        return 400, {'errors': dup_dict}
    return 1, None


def check_for_wrong_file_extension(file):
    valid_extensions = ['.jpeg', '.png', '.jpg']
    extension = path.splitext(file.name)[1]
    return extension not in valid_extensions


def validate_files(files: list[UploadedFile]) -> bool:
    too_many_files = len(files) > int(settings.MAX_FILE_NUMBER)
    file_too_big = sum(
        map(lambda file: int(file.size > int(settings.MAX_FILE_SIZE)), files)
    ) > 0
    wrong_file_type = sum(
        map(lambda file: int(check_for_wrong_file_extension(file)), files)
    ) > 0
    return not(too_many_files or file_too_big or wrong_file_type)
