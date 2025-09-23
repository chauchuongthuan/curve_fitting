from django.urls import path
from .api import IndexDataViewSet
from .views import IndexDataCreateView

urlpatterns = [
    path('api', IndexDataViewSet.as_view(), name='index_data_api'),
    path('create', IndexDataCreateView.create, name='index_data_create_view'),
]

