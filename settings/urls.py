from django.urls import path

from settings.views import SettingListView

urlpatterns = [
    path('', SettingListView.update_or_create_setting, name='setting-update'),
]
