from django.urls import path
from .api import IndexDataViewSet

urlpatterns = [
    path('', IndexDataViewSet.as_view(), name='index_data_api'),
]

