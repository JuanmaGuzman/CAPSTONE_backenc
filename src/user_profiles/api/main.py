from ninja import Router
from ninja.security import django_auth
from user_profiles.api.user_profiles import router as user_profile_router
from user_profiles.api.permissions import router as permissions_router


_TGS = ['User Profile']
router = Router()

router.add_router(
    'user_profiles',
    user_profile_router,
    tags=_TGS
)
router.add_router(
    'permissions',
    permissions_router,
    tags=_TGS,
    auth=django_auth
)
