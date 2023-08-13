from publications.models import PublicationItem
from dataclasses import dataclass


@dataclass
class PublicationItemWithAmount:
    pub_item: PublicationItem
    amount: int


def get_publication_items_with_amount_and_lock(
        id_amount_dict: dict[int, int]
) -> list[PublicationItemWithAmount]:
    pub_items = PublicationItem.objects.select_for_update().filter(
        id__in=(id for id in id_amount_dict.keys())
    )
    return [
        PublicationItemWithAmount(pub_item, id_amount_dict[pub_item.id])
        for pub_item in pub_items
    ]
