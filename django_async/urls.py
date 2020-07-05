from django.urls import path

from . import views
from . import just_sync

def urls_with_prefix(prefix, all_functions):
    return [path(f"{prefix}/{name}/", view) for name, view in all_functions]

urlpatterns = []
urlpatterns.extend(urls_with_prefix("views", views.all_functions))
urlpatterns.extend(urls_with_prefix("sync", just_sync.all_functions))