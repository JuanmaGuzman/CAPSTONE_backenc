from ninja import Router
from ninja.security import django_auth
from example_app.api.example import router as example_router


_TGS = ['Example']
router = Router()

router.add_router('example', example_router, tags=_TGS, auth=django_auth)
