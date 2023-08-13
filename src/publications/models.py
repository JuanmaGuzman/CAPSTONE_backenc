from django.db import models
from django.db.models import Q, Sum
from django.contrib.auth import get_user_model
from django.utils.timezone import now


_ITEM_SIZE_CHOICES = [
    ('xs', 'xs'),
    ('s', 's'),
    ('m', 'm'),
    ('l', 'l'),
    ('xl', 'xl'),
    ('xxl', 'xxl'),
    ('XS', 'xs'),
    ('S', 's'),
    ('M', 'm'),
    ('L', 'l'),
    ('XL', 'xl'),
    ('XXL', 'xxl'),
    ('36', '36'),
    ('38', '38'),
    ('40', '40'),
    ('42', '42'),
    ('44', '44'),
    ('46', '46'),
    ('48', '48'),
    ('50', '50'),
    ('52', '52')
]


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    image = models.FileField(blank=True, null=True)
    image_uri = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        return super(Category, self).save(*args, **kwargs)


class Item(models.Model):
    name = models.CharField(max_length=64)
    brand = models.CharField(max_length=32)
    size = models.CharField(
        max_length=8,
        choices=_ITEM_SIZE_CHOICES,
        blank=True,
        null=True
    )
    color = models.CharField(max_length=32)
    sku = models.IntegerField()
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="items",
        blank=True,
        null=True
    )

    def serialize(self):
        return {
            "name": self.name,
            "brand": self.brand,
            "size": self.size,
            "color": self.color,
            "sku": self.sku,
            "category_id": self.category.id
        }

    def referenced_by_others(self, user_id: int) -> bool:
        return self.publication_items.filter(
            ~Q(publication__seller_id=user_id)
        ).count() > 0


class Publication(models.Model):
    seller = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name="publications"
    )
    price = models.FloatField()
    publish_date = models.DateField(default=now, editable=False)
    is_active = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)
    description = models.TextField(default="")

    @property
    def general_item_info(self):
        publication_items_query = self.publication_items.all()
        sample_item = publication_items_query.first().item
        total_amount = publication_items_query.aggregate(
            Sum('amount')
        )['amount__sum']
        total_reserved = publication_items_query.aggregate(
            Sum('reserved')
        )['reserved__sum']
        return {
            'name': sample_item.name,
            'brand': sample_item.brand,
            'category': sample_item.category,
            'total_amount': total_amount - total_reserved
        }

    @property
    def photo_uris(self):
        return (
            photo.image_uri
            for photo in self.photos.all()
        )


class PublicationItem(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name="publication_items"
    )
    publication = models.ForeignKey(
        Publication,
        on_delete=models.CASCADE,
        related_name="publication_items"
    )
    amount = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)

    class Meta:
        unique_together = ('item', 'publication')

    @property
    def available(self):
        return self.amount - self.reserved

    @property
    def publication_info(self):
        return {
            'price': self.publication.price,
            'image_uris': [x for x in self.publication.photo_uris]
        }


class PublicationPhoto(models.Model):
    publication = models.ForeignKey(
        Publication,
        related_name='photos',
        on_delete=models.CASCADE
    )
    image = models.FileField(blank=True, null=True)
    image_uri = models.TextField(blank=True, null=True)


class ShoppingCartPointer(models.Model):

    cart_owner = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name="cart_items"
    )
    publication_item = models.ForeignKey(
        PublicationItem,
        on_delete=models.PROTECT
    )
    amount = models.IntegerField(default=1)

    class Meta:
        unique_together = ("cart_owner", "publication_item")
