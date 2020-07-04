from django.urls import path

from . import views

urlpatterns = []  # add all functions ending with "view" to urlpatterns
for view in dir(views):
    if view.endswith("view"):
        urlpatterns.append(path(view + "/", getattr(views, view)))
