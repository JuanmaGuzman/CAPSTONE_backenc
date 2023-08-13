from ninja import Router
from transactions.api.transactions import router as transaction_router
from transactions.api.confirmation import router as confirmation_router
from transactions.api.coupons import router as coupon_router


_TGS = ['Transactions']
router = Router()


router.add_router(
    'transactions',
    transaction_router,
    tags=_TGS,
)
router.add_router(
    'transaction_confirmation',
    confirmation_router,
    tags=_TGS
)

router.add_router(
    'coupons',
    coupon_router,
    tags=_TGS
)