from django.db import models
from django.contrib.auth.models import AbstractUser
from utilities.models import phone_regex


class UserProfile(AbstractUser):
    email_verified = models.BooleanField(default=False)
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
    )
    rut = models.CharField(max_length=20, unique=True)
    birthdate = models.DateField()

    @property
    def is_seller(self) -> bool:
        return self.groups.filter(name='Seller').exists()

    @property
    def is_admin(self) -> bool:
        return self.groups.filter(name='Admin').exists()

    REQUIRED_FIELDS = ['phone_number', 'rut', 'birthdate']


class UserShippingAddress(models.Model):
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        related_name='shipping_addresses'
    )
    region = models.CharField(max_length=64)
    commune = models.CharField(max_length=64)
    address = models.CharField(max_length=128)

    class Meta:
        unique_together = ('region', 'commune', 'address', 'user')
