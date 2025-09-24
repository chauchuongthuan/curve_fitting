from django.urls import path
from .api import IndexDataViewSet, TestSuperpositionLinearRegression
from .views import IndexDataCreateView

urlpatterns = [
    path('api/create', IndexDataViewSet.as_view(), name='index_data_api'),
    path('api/regression', TestSuperpositionLinearRegression.as_view(), name='superposition_linear_regression'),
    path('cms/create', IndexDataCreateView.create, name='index_data_create_view'),
]
