from typing import Type, Union
from publications.models import PublicationItem
from transactions.models import (
    Transaction,
    TransactionPointer,
    AcountlessTransaction,
    AcountlessTransactionPointer
)


def confirm_transaction_payment(
    transaction: Union[Transaction, AcountlessTransaction],
    ptr_class: Union[
        Type[TransactionPointer],
        Type[AcountlessTransactionPointer]
    ]
) -> None:
    transactions_pointers = ptr_class.objects.filter(
        transaction=transaction
    )
    publication_items = list()
    for pointer in transactions_pointers:
        pointer.publication_item.amount -= pointer.amount
        pointer.publication_item.reserved -= pointer.amount
        publication_items.append(pointer.publication_item)
    PublicationItem.objects.bulk_update(
        publication_items,
        ['amount', 'reserved']
    )
    transaction.status = 'SUCCEDED'
    transaction.save()


def get_ambiguous_transaction(payment_id: str) -> Union[
    tuple[
        Union[Transaction, AcountlessTransaction],
        Union[Type[TransactionPointer], Type[AcountlessTransactionPointer]]
    ],
    tuple[None, None]
]:
    # Find transaction or accountless_transactions
    transaction_query = Transaction.objects.filter(payment_id=payment_id)
    accountless_transaction_query = AcountlessTransaction.objects.filter(
        payment_id=payment_id
    )
    # Return one is found
    if transaction_query.exists():
        return transaction_query.get(), TransactionPointer
    elif accountless_transaction_query.exists():
        return (
            accountless_transaction_query.get(),
            AcountlessTransactionPointer
        )
    # Return empty tuple
    return None, None


def cancel_transaction_payment(
    transaction: Union[Transaction, AcountlessTransaction]
) -> tuple[int, Union[None, dict[str, str]]]:
    if transaction.status in ('REQUESTED', 'SUCCEDED', 'CANCELED'):
        return (
            400,
            {'message': 'Transaction has already been resolved.'}
        )
    transaction.status = 'CANCELED'
    publication_items = set()
    for pointer in transaction.transaction_pointers.all():
        pointer.publication_item.reserved -= pointer.amount
        publication_items.add(pointer.publication_item)
    PublicationItem.objects.bulk_update(publication_items, ['reserved'])
    transaction.save()
    return 200, None
