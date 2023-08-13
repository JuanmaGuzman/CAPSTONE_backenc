from typing import Optional
from ninja.orm import create_schema
from ninja import Schema
from transactions.models import (
    Transaction,
    AcountlessTransaction,
    TransactionPointer,
    AcountlessTransactionPointer,
    Coupon
)
from publications.schema import (
    PublicationItemSchema,
    DetailedPublicationItemSchema
)
from user_profiles.schema import PublicUserProfileSchema


CouponCreationSchema = create_schema(
    Coupon,
    name='CouponCreate',
    fields=['name', 'code', 'discount_percentage']
)


MassCouponCreationSchema = create_schema(
    Coupon,
    name='MassCouponCreationSchema',
    fields=['name', 'discount_percentage'],
    custom_fields=[('amount', int, 0)]
)


CouponSchema = create_schema(
    Coupon,
    name='Coupon',
    fields=['id', 'name', 'code', 'discount_percentage', 'active']
)


SuccinctCouponSchema = create_schema(
    Coupon,
    name='SuccinctCouponSchema',
    fields=['id', 'code', 'discount_percentage']
)


TransactionPointerSchema = create_schema(
    TransactionPointer,
    name='TransactionPointerSchema',
    exclude=['transaction', 'publication_item'],
    custom_fields=[('publication_item', DetailedPublicationItemSchema, None)]
)


TransactionSchema = create_schema(
    Transaction,
    name='TransactionSchema',
    exclude=['buyer', 'payment_id', 'created_at', 'status', 'coupon'],
    custom_fields=[
        ('transaction_pointers', list[TransactionPointerSchema], None),
        ('coupon', SuccinctCouponSchema, None)
    ],
    depth=1
)


class TransactionCreateSchema(Schema):
    shipping_address_id: int
    coupon_id: Optional[int]


class TransactionCreateResponseSchema(Schema):
    payment_id: str
    widget_token: str


class TransactionAccountlessPublicationItems(Schema):
    id: int
    amount: int


class TransactionAcountlessCreateSchema(Schema):
    buyer_name: str
    buyer_lastname: str
    phone_number: str
    email: str
    region: str
    commune: str
    address: str
    publication_items_list: list[TransactionAccountlessPublicationItems]
    coupon_id: Optional[int]


# TransactionAcountlessCreateSchema = create_schema(
#    AcountlessTransaction,
#    name='TransactionAcountlessCreate',
#    fields=[
#        'buyer_name',
#        'buyer_lastname',
#        'phone_number',
#        'region',
#        'commune',
#        'address'
#    ],
#    custom_fields=[
#        ('publications_list', list[TransactionAccountlessPublications], None),
#        ('coupon_id', int, None)
#    ]
# )


AccountlessTransactionSchema = create_schema(
    AcountlessTransaction,
    name='AccountlessTransactionSchema',
    fields=[
        'buyer_name',
        'buyer_lastname',
        'phone_number',
        'region',
        'commune',
        'address'
    ],
    custom_fields=[('coupon', SuccinctCouponSchema, None)]
)


SellerTransactionSchema = create_schema(
    TransactionPointer,
    name='SellerTransaction',
    exclude=['publication_item', 'transaction'],
    custom_fields=[
        (
            'transaction',
            create_schema(
                Transaction,
                fields=['shipping_address'],
                custom_fields=[
                    ('buyer', PublicUserProfileSchema, None),
                    ('coupon', SuccinctCouponSchema, None)
                ],
                depth=1
            ),
            None
        ),
        ('publication_item', PublicationItemSchema, None)
    ]
)


SellerAccountlessTransactionSchema = create_schema(
    AcountlessTransactionPointer,
    name='SellerAccountlessTransaction',
    exclude=['publication_item', 'transaction'],
    custom_fields=[
        ('transaction', AccountlessTransactionSchema, None),
        ('publication_item', PublicationItemSchema, None)
    ],
    depth=1
)


class AllSellerTransactionsSchema(Schema):
    transaction_pointers: list[SellerTransactionSchema]
    accountless_transaction_pointers: list[SellerAccountlessTransactionSchema]


class TransactionResolveSchema(Schema):
    id: str
    type: str
    mode: Optional[str]
    createdAt: Optional[str]
    data: Optional[dict[str, str]]
    object: Optional[str]
