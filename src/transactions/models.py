from django.db import models
from django.contrib.auth import get_user_model
from publications.models import PublicationItem
from user_profiles.models import UserShippingAddress
from utilities.models import phone_regex


_TRANSACTION_STATUS = (
    ('CREATED', 'created'),
    ('REQUESTED', 'requested'),
    ('CANCELED', 'canceled'),
    ('SUCCEDED', 'confirmed'),
    ('FAILED', 'failed')
)


class Coupon(models.Model):
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=256, unique=True)
    discount_percentage = models.FloatField()
    active = models.BooleanField(default=True)


class ProtoTransaction(models.Model):
    payment_id = models.CharField(max_length=60, unique=True)
    status = models.CharField(
        max_length=10,
        default='CREATED',
        choices=_TRANSACTION_STATUS
    )
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Transaction(ProtoTransaction):
    buyer = models.ForeignKey(
        get_user_model(),  # UserProfile
        on_delete=models.PROTECT,
        related_name="purchases"
    )
    shipping_address = models.ForeignKey(
        UserShippingAddress,
        on_delete=models.PROTECT,
        related_name='purchases',
        null=True
    )
    coupon = models.OneToOneField(
        Coupon,
        on_delete=models.PROTECT,
        related_name='transaction',
        blank=True,
        null=True
    )

    @property
    def publications(self):
        return (
            pointer.publication_item
            for pointer in self.transaction_pointers.all()
        )


class AcountlessTransaction(ProtoTransaction):
    buyer_name = models.CharField(max_length=100)
    buyer_lastname = models.CharField(max_length=100)
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17
    )
    email = models.EmailField(max_length=256, blank=True, null=True)
    address = models.CharField(max_length=128)
    region = models.CharField(max_length=64)
    commune = models.CharField(max_length=64)
    coupon = models.OneToOneField(
        Coupon,
        on_delete=models.PROTECT,
        related_name='accountless_transaction',
        blank=True,
        null=True
    )


class TransactionPointer(models.Model):
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name="transaction_pointers"
    )
    publication_item = models.ForeignKey(
        PublicationItem,
        on_delete=models.PROTECT,
        related_name="transaction_pointers"
    )
    amount = models.IntegerField()
    price_per_unit = models.IntegerField()


class AcountlessTransactionPointer(models.Model):
    transaction = models.ForeignKey(
        AcountlessTransaction,
        on_delete=models.PROTECT,
        related_name="transaction_pointers"
    )
    publication_item = models.ForeignKey(
        PublicationItem,
        on_delete=models.PROTECT,
        related_name="acountless_transaction_pointers"
    )
    amount = models.IntegerField()
    price_per_unit = models.IntegerField()
