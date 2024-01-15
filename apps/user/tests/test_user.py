"""
Tests for 'User' model.
"""

from django.test import TestCase, Client
from django.contrib.auth import authenticate, get_user_model
from django.urls import reverse

from apps.user.forms import UserForm
from apps.user.models import User

import pytest


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def frontpage_url():
    return reverse("frontpage")


@pytest.fixture
def login_url():
    return reverse("login")


@pytest.fixture
def logout_url():
    return reverse("logout")


@pytest.fixture
def register_url():
    return reverse("register")


def profile_url(username=None):
    if username:
        return reverse("apps.user:user_profile", kwargs={"username": username})
    return reverse("apps.user:user_profile")


@pytest.fixture
def edit_profile_url():
    return reverse("apps.user:edit_profile")


@pytest.fixture
def valid_data():
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword",
    }


@pytest.fixture
def invalid_data():
    return {
        "username": "testuser",
        "email": "testusexample.com",
        "password": "wbibfeibveiv",
    }


@pytest.mark.django_db
class TestLoginView:
    """Tests for login view"""

    def test_login_view_GET_authenticated(self, client, frontpage_url, login_url):
        # Test if authenticated user is redirected to frontpage
        User.objects.create_user(username="testuser", password="testpassword")
        client.login(username="testuser", password="testpassword")
        response = client.get(login_url)

        assert response.status_code == 302  # redirect
        assert response.url == frontpage_url

    def test_login_view_GET_not_authenticated(self, client, login_url):
        # Test if the login page is accessible for non-authenticated users
        response = client.get(login_url)

        assert response.status_code == 200  # accessible, ok
        assert "login.html" in [t.name for t in response.templates]

    def test_login_view_POST_valid_user(self, client, login_url):
        # Test login with valid data
        User.objects.create_user(username="testuser", password="testpassword")
        valid_login_data = {"username": "testuser", "password": "testpassword"}
        response = client.post(login_url, valid_login_data)

        assert client.session["_auth_user_id"]  # user is authenticated
        assert response.status_code == 302  # redirect
        assert response.url == reverse("frontpage")  # to frontpage
        assert User.objects.filter(username="testuser").exists()

    def test_login_view_POST_valid_user_redirect(self, client, login_url):
        # Test redirection to the page user was trying to access before logging in
        User.objects.create_user(username="testuser", password="testpassword")
        valid_login_data = {"username": "testuser", "password": "testpassword"}

        protected_url = profile_url()  # accessing profile page without logging in

        response = client.get(protected_url)

        assert response.status_code == 302  # should be redirected
        assert response.url == f"{login_url}?next={protected_url}"  # to the login page with next parameter

        valid_login_data_with_next = valid_login_data.copy()
        valid_login_data_with_next["next"] = protected_url
        response = client.post(login_url, valid_login_data_with_next)

        assert client.session["_auth_user_id"]  # user is authenticated
        assert response.status_code == 302  # redirect
        assert response.url == profile_url()  # to profile page
        assert User.objects.filter(username="testuser").exists()

    def test_login_view_POST_invalid_user(self, client, login_url):
        # Test login with invalid data
        invalid_login_data = {"username": "testuser", "password": "testpassword"}
        response = client.post(login_url, invalid_login_data)

        assert response.context["login_error"] == "Wrong username or password."
        assert "_auth_user_id" not in client.session  # user is not authenticated


@pytest.mark.django_db
class TestLogoutView:
    """Tests for logout view"""

    def test_logout_view_GET_authenticated(self, client, logout_url):
        # Users should not be able to log out with a GET request
        User.objects.create_user(username="testuser", password="testpassword")
        client.login(username="testuser", password="testpassword")
        response = client.get(logout_url)

        assert response.status_code == 405  # method not allowed (@post_only decorator)

    def test_logout_view_POST_authenticated(self, client, logout_url, frontpage_url):
        # Users should be able to log out with a POST request
        User.objects.create_user(username="testuser", password="testpassword")
        client.login(username="testuser", password="testpassword")
        response = client.post(logout_url)

        assert "_auth_user_id" not in client.session  # user is not authenticated
        assert response.status_code == 302  # redirect
        assert response.url == frontpage_url  # to frontpage


@pytest.mark.django_db
class TestRegisterView:
    """Tests for register view"""

    def test_register_view_GET_authenticated(self, client, frontpage_url, register_url):
        # Test if authenticated user is redirected to frontpage
        User.objects.create_user(username="testuser", password="testpassword")
        client.login(username="testuser", password="testpassword")
        response = client.get(register_url)

        assert response.status_code == 302  # redirect
        assert response.url == frontpage_url

    def test_register_view_GET_not_authenticated(self, client, register_url):
        # Test if the registration page is accessible for non-authenticated users
        response = client.get(register_url)

        assert response.status_code == 200  # accessible, ok
        assert "register.html" in [t.name for t in response.templates]

    def test_register_view_POST_valid_data(self, client, register_url, login_url, valid_data):
        # Test registration with valid data
        response = client.post(register_url, valid_data)

        assert response.status_code == 302  # redirect
        assert response.url == login_url
        assert "_auth_user_id" not in client.session  # user needs to log in after registration
        assert User.objects.filter(username="testuser").exists()

    def test_register_view_POST_invalid_data(self, client, register_url, invalid_data):
        # Test registration with invalid data
        response = client.post(register_url, invalid_data)

        assert "_auth_user_id" not in client.session  # user is not authenticated
        # Confirm the expected form errors in response context
        assert "form" in response.context
        form = response.context["form"]
        assert form.errors


@pytest.mark.django_db
class TestProfileView:
    """Tests for profile view"""

    def test_profile_view_GET_authenticated(self, client):
        # Test if authenticated user is able to access their profile page and other users' profile pages
        User.objects.create_user(username="testuser", password="testpassword")
        user = User.objects.create_user(username="testuser1", password="testpassword")
        client.login(username="testuser", password="testpassword")
        response = client.get(profile_url())

        assert response.status_code == 200  # accessible, ok
        assert "profile.html" in [t.name for t in response.templates]

        response = client.get(profile_url(username=user.username))
        assert response.status_code == 200  # accessible, ok
        assert "profile.html" in [t.name for t in response.templates]

    def test_profile_view_GET_not_authenticated(self, client, login_url):
        # Test if non-authenticated user is redirected to login page with next parameter
        response = client.get(profile_url())

        assert response.status_code == 302
        assert response.url == login_url + "?next=/profile/"

    def test_edit_profile_view_GET_authenticated(self, client, edit_profile_url):
        # Test if authenticated user is able to access edit_profile page
        User.objects.create_user(username="testuser", password="testpassword")
        client.login(username="testuser", password="testpassword")
        response = client.get(edit_profile_url)

        assert response.status_code == 200
        assert "edit_profile.html" in [t.name for t in response.templates]

    def test_edit_profile_view_GET_not_authenticated(self, client, login_url, edit_profile_url):
        # Test if non-authenticated user is redirected to login page with next parameter
        response = client.get(edit_profile_url)

        assert response.status_code == 302
        assert response.url == login_url + "?next=/profile/edit-profile/"

    def test_edit_profile_view_POST_valid_data(self, client, edit_profile_url):
        # Test editing profile with valid data
        user = User.objects.create_user(
            username="testuser", password="testpassword", first_name="Lebron", email="user@example.com"
        )
        client.login(username="testuser", password="testpassword")
        valid_edit_data = {"first_name": "Michael", "email": "updated@example.com"}
        response = client.post(edit_profile_url, valid_edit_data)

        # Refresh user instance from the database to reflect changes
        user.refresh_from_db()

        assert response.status_code == 302  # redirect
        assert response.url == profile_url()  # to profile page
        assert user.first_name == "Michael"
        assert user.email == "updated@example.com"

    def test_edit_profile_view_POST_invalid_data(self, client, edit_profile_url):
        # Test editing profile with invalid data
        user = User.objects.create_user(
            username="testuser", password="testpassword", first_name="Michael", email="user@example.com"
        )
        client.login(username="testuser", password="testpassword")

        invalid_edit_data = {"first_name": "Lebron", "email": "updated.com"}
        response = client.post(edit_profile_url, invalid_edit_data)
        user.refresh_from_db()
        assert response.status_code == 200  # accessible, ok
        assert response.templates[0].name == "edit_profile.html"
        assert "Enter a valid email address." in response.content.decode("utf-8")
        assert user.first_name == "Michael"
        assert user.email == "user@example.com"

        invalid_edit_data = {"first_name": "Lebron", "about_text": "test" * 150}  # too long
        response = client.post(edit_profile_url, invalid_edit_data)
        user.refresh_from_db()
        assert response.status_code == 200  # accessible, ok
        assert response.templates[0].name == "edit_profile.html"
        assert "Ensure this value has at most 500 characters (it has 600)." in response.content.decode("utf-8")
        assert user.first_name == "Michael"
        assert user.email == "user@example.com"

    def test_edit_profile_view_POST_duplicate_email(self, client, edit_profile_url):
        # Test editing profile with duplicate email
        user1 = User.objects.create_user(
            username="testuser1", password="testpassword", first_name="Lebron", email="user1@example.com"
        )
        user2 = User.objects.create_user(
            username="testuser2", password="testpassword", first_name="Michael", email="user2@example.com"
        )
        client.login(username="testuser1", password="testpassword")
        invalid_edit_data = {"first_name": "Lebron", "email": "user2@example.com"}
        response = client.post(edit_profile_url, invalid_edit_data)

        user1.refresh_from_db()

        assert user1.first_name == "Lebron"
        assert user1.email == "user1@example.com"
