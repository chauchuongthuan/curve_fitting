from django.urls import path
from .api import IndexDataViewSet, TestGrgSolver
from .views import IndexDataCreateView
urlpatterns = [
    path('api/create', IndexDataViewSet.as_view(), name='index_data_api'),
    path('api/run_grg_solver', TestGrgSolver.as_view(), name='run_grg_solver'),
    path('cms/create', IndexDataCreateView.create, name='index_data_create_view'),
]
