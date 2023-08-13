from ninja import Schema
from ninja.orm import create_schema
from publications.models import (
    Publication,
    Item,
    PublicationItem,
    ShoppingCartPointer,
    Category
)
from typing import Union


CategorySchema = create_schema(
    Category,
    name='CategorySchema',
    exclude=['image']
)


SuccinctCategorySchema = create_schema(
    Category,
    name='SuccinctCategorySchema',
    exclude=['image_uri', 'image']
)


CategoryCreationSchema = create_schema(
    Category,
    name='CategorySchema',
    exclude=('id', 'image', 'image_uri')
)


ItemSchema = create_schema(
    Item,
    name='ItemSchema',
    exclude=('id',)
)


DetailedItemSchema = create_schema(
    Item,
    name='DetailedItemSchema',
    exclude=['category'],
    custom_fields=[('category', SuccinctCategorySchema, None)]
)


ItemCreationSchema = create_schema(
    Item,
    name='ItemCreate',
    fields=[
        'name',
        'brand',
        'size',
        'color',
        'sku'
    ],
    custom_fields=[
        ('category_id', int, None)
    ]
)


class PublicationItemGeneralInfoSchema(Schema):
    name: str
    brand: str
    category: CategorySchema
    total_amount: int


PublicationItemSchema = create_schema(
    PublicationItem,
    name='PublicationItemSchema',
    exclude=['item', 'amount', 'reserved'],
    custom_fields=[
        ('item', DetailedItemSchema, None),
        ('available', int, None)
    ]
)


class PublicationItemCreationSchema(Schema):
    size: str
    color: str
    sku: int
    amount: int


class PublicationItemAddSchema(Schema):
    publication_items: list[PublicationItemCreationSchema]


PublicationSchema = create_schema(
    Publication,
    name='PublicationsShow',
    custom_fields=[
        ('publication_items', list[PublicationItemSchema], None),
        ('photo_uris', list[str], None)
    ]
)


SuccinctPublicationSchema = create_schema(
    Publication,
    name='SuccinctPublicationSchema',
    fields=['id', 'seller', 'price'],
    custom_fields=[
        ('general_item_info', PublicationItemGeneralInfoSchema, None),
        ('photo_uris', list[str], None)
    ]
)


class PublicationCreationSchema(Schema):
    price: float
    description: str
    item_name: str
    item_brand: str
    item_category_id: int
    publication_items: list[PublicationItemCreationSchema]


PublicationUpdateSchema = create_schema(
    Publication,
    name='Publication Update',
    fields=[
        'price',
        'description'
    ]
)


PublicationItemUpdateSchema = create_schema(
    PublicationItem,
    name='PublicationItemUpdateSchema',
    fields=['amount']
)


ShoppingCartSchema = create_schema(
    ShoppingCartPointer,
    name='Shopping Cart',
    fields=['amount']
)


class PublictionItemPublictionInfo(Schema):
    price: int
    image_uris: list[str]


DetailedPublicationItemSchema = create_schema(
    PublicationItem,
    name='DetailedPublicationItemSchema',
    exclude=['item', 'amount', 'reserved'],
    custom_fields=[
        ('item', DetailedItemSchema, None),
        ('available', int, None),
        ('publication_info', PublictionItemPublictionInfo, None)
    ]
)


ShoppingCartDetailSchema = create_schema(
    ShoppingCartPointer,
    name='ShoppingCartDetail',
    fields=['amount'],
    custom_fields=[
        ('publication_item', DetailedPublicationItemSchema, None)
    ],
    depth=1
)


class ItemConflictInfo(Schema):
    current_item: ItemSchema
    item_in_form: ItemSchema


class ItemConflictErrorSchema(Schema):
    conflicts: list[Union[ItemConflictInfo, str]]
