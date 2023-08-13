# from django.conf import settings
# from django.contrib import admin
from django.urls import path
from conf.api import api


urlpatterns = [
    # path('admin/', admin.site.urls),
    path('api/', api.urls),
]
