from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from user_profiles.models import UserProfile
from publications.models import Category, Item, Publication, PublicationItem
from typing import Iterable
from random import randint
from datetime import date


_PUBLICATION_AMOUNT = 10


def create_users() -> tuple[UserProfile, UserProfile]:
    UserModel = get_user_model()
    seller = UserModel.objects.create(
        username='seller',
        email='seller@email.com',
        first_name='seller_first_name',
        last_name='seller_last_name',
        rut='0000000-1',
        phone_number='+56900001',
        birthdate=date.today(),
        email_verified=True
    )
    buyer = UserModel.objects.create(
        username='buyer',
        email='buyer@email.com',
        first_name='buyer_first_name',
        last_name='buyer_last_name',
        rut='0000000-0',
        phone_number='+56900000',
        birthdate=date.today(),
        email_verified=True
    )
    buyer.set_password('password')
    seller.groups.add(Group.objects.get(name='Seller'))
    seller.set_password('password')
    seller.save()
    buyer.save()
    return seller, buyer


def create_items(n: int) -> Iterable[Item]:
    items = list()
    category = Category.objects.create(name='category')
    for i in range(n):
        items.append(
            Item(
                name=f'item_{i}',
                brand=f'brand_{i}',
                size=f'size_{i}',
                color=f'color_{i}',
                sku=i,
                category=category
            )
        )
    Item.objects.bulk_create(items, len(items))
    return items


def create_publication(n: int, seller: UserProfile) -> None:
    items = create_items(n)
    publications = list()
    publication_items = list()
    for i, item in enumerate(items):
        publications.append(
            Publication(
                seller=seller,
                price=1,
                is_active=True,
                is_accepted=True,
                description=f'description n.{i}'
            )
        )
        publication_items.append(
            PublicationItem(
                item=item,
                publication=publications[i],
                amount=randint(10, 20),
            )
        )
    Publication.objects.bulk_create(publications, len(publications))
    PublicationItem.objects.bulk_create(
        publication_items,
        len(publication_items)
    )


class Command(BaseCommand):

    help: str = 'Reset and populate db with dummy data.'

    def handle(self, *args, **options):
        if settings.PROD:
            raise CommandError(
                'This command can not be executed in a production enviroment.'
            )
        # Reset database
        call_command('reset_db')
        call_command('migrate')
        # Create seller and buyer users
        seller, _ = create_users()
        # Create publications
        create_publication(_PUBLICATION_AMOUNT, seller)
