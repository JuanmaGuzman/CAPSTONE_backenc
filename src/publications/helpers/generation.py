from conf import settings
from ninja.files import UploadedFile
from publications.models import (
    Publication,
    PublicationItem,
    PublicationPhoto,
    Item,
    Category
)
from utilities.models import get_latest_id
from typing import Union
from os import path


def make_new_file_name(file, model, proto_name: str) -> str:
    file_extension = path.splitext(file.name)[1]
    return f'{proto_name}_{get_latest_id(model)}' + file_extension


def upload_publication_images(
    pub: Publication,
    files: list[UploadedFile]
) -> tuple[int, Union[dict, None]]:
    if not settings.PROD:
        for _ in files:
            image_uri = 'https://github.githubassets.com/images/modules/' \
                + 'site/home/globe.jpg?width=619'
            photo = PublicationPhoto.objects.create(
                publication=pub,
                image_uri=image_uri
            )
    else:
        for file in files:
            new_name = make_new_file_name(file, PublicationPhoto, 'pub_img')
            file.name = new_name
            photo = PublicationPhoto(
                publication=pub,
                image=file
            )
            photo.save()
            photo.image_uri = photo.image.url
            photo.save()
    return 1, None


def upload_category_image(
    category: Category,
    file: UploadedFile
) -> tuple[int, Union[dict[str, str], None]]:
    if not settings.PROD:
        image_uri = 'https://github.githubassets.com/images/modules/' \
            + 'site/home/globe.jpg?width=619'
        category.image_uri = image_uri
        category.save()
    else:
        new_name = make_new_file_name(file, Category, 'cat_img')
        file.name = new_name
        category.image = file
        category.save()
        category.image_uri = category.image.url
        category.save()
    return 1, None


def generate_items(
    publication: Publication,
    publication_info: dict,
) -> None:
    # Extract information from pub_items
    sku_set = {item['sku'] for item in publication_info['publication_items']}
    item_query = Item.objects.filter(sku__in=sku_set)
    category_query = Category.objects.filter(
        pk=publication_info['item_category_id']
    )
    # Store items to be created to make use of bulk_create
    items_to_create = []
    publication_items_to_create = []
    for pub_item in publication_info['publication_items']:
        item_query_by_sku = item_query.filter(sku=pub_item['sku'])
        if item_query_by_sku.exists():
            item = item_query_by_sku.get()
        else:
            item = Item(
                name=publication_info['item_name'].lower(),
                brand=publication_info['item_brand'].lower(),
                category=category_query.get(
                    pk=publication_info['item_category_id']
                ),
                size=pub_item['size'].lower(),
                color=pub_item['color'].lower(),
                sku=pub_item['sku']
            )
            items_to_create.append(item)
        publication_items_to_create.append(
            PublicationItem(
                item=item,
                publication=publication,
                amount=pub_item['amount']
            )
        )
    if len(items_to_create) > 0:
        Item.objects.bulk_create(items_to_create, len(items_to_create))
    PublicationItem.objects.bulk_create(
        publication_items_to_create,
        len(publication_items_to_create)
    )
