from ninja import NinjaAPI
from user_auth.api import router as auth_router
from user_profiles.api.main import router as user_profiles_router
from publications.api.main import router as publication_router
from transactions.api.main import router as transaction_router
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse


class ShortNameNinjaAPI(NinjaAPI):
    def get_openapi_operation_id(self, operation):
        return operation.view_func.__name__


api = ShortNameNinjaAPI(csrf=True)
api.add_router('/auth/', auth_router)
api.add_router('/user_profiles/', user_profiles_router)
api.add_router('/publications/', publication_router)
api.add_router('/transactions/', transaction_router)



@api.get('csrf')
@ensure_csrf_cookie
def get_csrf(request):
    return HttpResponse()
