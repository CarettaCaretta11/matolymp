from django.urls import re_path
from . import views


app_name = "apps.user"
urlpatterns = [
    re_path(r"^$", views.user_profile, name="user_profile"),
    re_path(r"^(?P<username>[0-9a-zA-Z_]*)/$", views.user_profile, name="user_profile"),
    re_path(r"^edit-profile/$", views.edit_profile, name="edit_profile"),
]
