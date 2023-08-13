from ninja import Router
from publications.api.publications import router as publications_router
from publications.api.shopping_cart import router as shopping_cart_router
from publications.api.categories import router as categories_router

_TGS = ["Publications"]
router = Router()

router.add_router(
    "publications",
    publications_router,
    tags=_TGS
)

router.add_router(
    "shopping_cart",
    shopping_cart_router,
    tags=_TGS
)

router.add_router(
    "categories",
    categories_router,
    tags=_TGS
)

