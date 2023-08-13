from django.db import transaction
from django.utils.timezone import make_aware
from publications.models import PublicationItem
from transactions.models import (
    Transaction,
    TransactionPointer,
    AcountlessTransaction,
    AcountlessTransactionPointer
)
from typing import Type, Union
from datetime import datetime, timedelta
from math import floor, ceil


_PUBLICATIONS_TO_CLEAN = 100
_EXP_SECONDS = 15 * 60


@transaction.atomic
def clean_transactions(n: int) -> None:
    fifteen_minutes_ago = datetime.now() - timedelta(seconds=_EXP_SECONDS)
    time_limit = make_aware(fifteen_minutes_ago)
    clean_pointers(floor(n), Transaction, TransactionPointer, time_limit)
    clean_pointers(
        ceil(n),
        AcountlessTransaction,
        AcountlessTransactionPointer,
        time_limit
    )


def clean_pointers(
    n: int,
    transaction_model: Union[Type[Transaction], Type[AcountlessTransaction]],
    pointer_model: Union[
        Type[TransactionPointer],
        Type[AcountlessTransactionPointer]
    ],
    time_limit: datetime
):
    pointers_to_clean = (
        pointer_model
        .objects
        .select_related('transaction')
        .select_related('publication_item')
        .select_for_update('publication_item')
    ).filter(
        transaction__created_at__lte=time_limit,
        transaction__status='CREATED'
    )[:n // 2]
    publication_items = set()
    transactions = set()
    for pointer in pointers_to_clean:
        pointer.publication_item.reserved -= pointer.amount
        pointer.transaction.status = 'CANCELED'
        publication_items.add(pointer.publication_item)
        transactions.add(pointer.transaction)
    PublicationItem.objects.bulk_update(publication_items, ['reserved'])
    transaction_model.objects.bulk_update(transactions, ['status'])


class CleanTransactionMiddleWare:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Clean Transactions Here
        clean_transactions(_PUBLICATIONS_TO_CLEAN)
        return self.get_response(request)
