from publications.models import Publication, PublicationItem
from transactions.models import TransactionPointer
from django.db.models import Avg, Q, F
from typing import Union, Iterable


_SIZE_IDENTITY_CLASSES = {
    'xs': {'xs', '36'},
    's': {'s', '38', '40'},
    'm': {'m', '42', '44'},
    'l': {'l', '46', '48'},
    'xl': {'xl', '50', '52'},
    'xxl': {'xxl', '54'}
}


def size_identity_class_representative(
    size: Union[str, None]
) -> Union[str, None]:
    if size == '':
        return None
    for rep, size_class in _SIZE_IDENTITY_CLASSES.items():
        if size in size_class:
            return rep


def size_suggestion(
    sizes: Iterable[str]
) -> tuple[set[str], bool]:
    sizes_set = set(sizes)
    size_class_rep_set = set()
    suggestion_set = set()

    for size in sizes_set:
        size_class_rep = size_identity_class_representative(size)
        if size_class_rep is not None:
            size_class_rep_set.add(size_class_rep)
    for size_class_rep in size_class_rep_set:
        for size in _SIZE_IDENTITY_CLASSES[size_class_rep]:
            suggestion_set.add(size)

    return suggestion_set, '' in sizes_set


def get_user_recommendations(
    user_id: int,
    amount: int
) -> Union[Iterable[Publication], None]:
    # Criteria:
    # 1. Recent publications
    # 2. Same price range as previous purchases
    # 3. Same categories as previous purchases
    # 4. If none null size in sizes of previous purchases then similar sizes

    # Get user purchases
    recent_transactions = (
        TransactionPointer.objects
        .select_related('publication_item')
        .select_related('transaction')
        .filter(transaction__buyer_id=user_id)
    ).order_by('transaction__created_at')[:amount]
    if not recent_transactions.exists():
        return []
    # Determine average price to recommend
    average_price = recent_transactions.aggregate(
        Avg('price_per_unit')
    )['price_per_unit__avg']
    top_price_limit = average_price * 1.5
    bottom_price_limit = average_price * 0.5
    # Determine categories to recommend
    recommended_categories = (
        pointer.publication_item.item.category
        for pointer in recent_transactions
    )
    # Determine sizes to recommend
    sizes = (
        pointer.publication_item.item.size
        for pointer in recent_transactions
    )
    recommended_sizes, has_none_value = size_suggestion(sizes)
    size_filter = Q(item__size__in=recommended_sizes)
    if has_none_value:
        size_filter = size_filter | Q(item__size='')
    # return suggestions
    suggestions = (
        PublicationItem.objects
        .select_related('publication')
        .select_related('item')
        .filter(
            size_filter,
            publication__price__lte=top_price_limit,
            publication__price__gte=bottom_price_limit,
            item__category__in=recommended_categories,
            amount__gt=F('reserved')
        ).order_by('publication__publish_date')[:amount]
    )
    return {
        suggestion.publication
        for suggestion in suggestions
    }
