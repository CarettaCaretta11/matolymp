from django.urls import path, re_path
from . import views


app_name = "apps.blog"
urlpatterns = [
    re_path(r"^comments/(?P<thread_id>[0-9]+)$", views.comments, name="post"),
    re_path(r"^submit/$", views.submit, name="submit"),
    re_path(r"^post/comment/$", views.post_comment, name="post_comment"),
    re_path(r"^vote/$", views.vote, name="vote"),
    path("about/", views.about, name="about"),
]
