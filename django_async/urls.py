from django.urls import path

from . import views

urlpatterns = [path(name + "/", view) for name, view in views.all_functions]