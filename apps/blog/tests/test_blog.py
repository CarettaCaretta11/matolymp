"""
Tests for 'Submission', 'Comment', and 'Vote' models.
"""
import random

from django.test import TestCase, Client
from django.contrib.auth import authenticate
from django.urls import reverse

from apps.blog.forms import SubmissionForm
from apps.blog.models import Submission, Comment, Vote
from apps.user.models import User

import pytest


@pytest.fixture
def client():
    return Client()


def comments_url(thread_id=None):
    if thread_id:
        return reverse("apps.blog:post", kwargs={"thread_id": thread_id})
    return reverse("apps.blog:post")


@pytest.fixture
def frontpage_url():
    return reverse("frontpage")


@pytest.fixture
def submissions():
    # note: object_id's are not always 1-30 since we delete submissions
    # and create new ones in other tests
    return [Submission.objects.create(title=f"Submission {i}") for i in range(30)]


@pytest.fixture
def submission_url():
    return reverse('apps.blog:submit')


@pytest.mark.django_db
def test_GET_about(client):
    response = client.get(reverse('apps.blog:about'))
    assert response.status_code == 200
    assert response.templates[0].name == 'about.html'


@pytest.mark.django_db
class TestFrontpageView:
    """Tests for frontpage view"""

    def test_frontpage_GET_authenticated(self, client, frontpage_url, submissions):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        response = client.get(frontpage_url)

        assert response.status_code == 200
        assert "submissions" in response.context

    def test_frontpage_GET_not_authenticated(self, client, frontpage_url, submissions):
        response = client.get(frontpage_url)

        assert response.status_code == 200
        assert "submissions" in response.context

    def test_frontpage_GET_with_submissions(self, client, frontpage_url, submissions):
        response = client.get(frontpage_url)

        assert response.status_code == 200
        assert "submissions" in response.context
        assert len(response.context["submissions"]) == 25

    def test_frontpage_GET_without_submissions(self, client, frontpage_url, submissions):
        Submission.objects.all().delete()
        response = client.get(frontpage_url)

        assert response.status_code == 200
        assert "submissions" in response.context
        assert len(response.context["submissions"]) == 0

    def test_frontpage_page_GET_not_an_integer(self, client, frontpage_url, submissions):
        response = client.get(frontpage_url, {"page": "not_an_integer"})

        assert response.status_code == 404

    def test_frontpage_page_GET_out_of_range(self, client, frontpage_url, submissions):
        response = client.get(frontpage_url, {"page": "2"})

        assert response.status_code == 200
        assert "submissions" in response.context
        assert len(response.context["submissions"]) == 5  # Last page with remaining submissions


@pytest.mark.django_db
class TestCommentsView:
    """Tests for comments view"""

    def test_comments_GET_authenticated(self, client, submissions):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        idx = random.randint(0, 29)
        submission_id = submissions[idx].id
        url = reverse('apps.blog:post', kwargs={'thread_id': submission_id})
        response = client.get(url)

        assert response.status_code == 200
        assert 'comments.html' in response.templates[0].name

    def test_comments_GET_not_authenticated(self, client, submissions):
        idx = random.randint(0, len(submissions)-1)
        post = submissions[idx]
        response = client.get(comments_url(idx))

        assert response.status_code == 302  # Redirect to login page
        assert response.url == '/login/?next=' + comments_url(idx)

    def test_comments_GET_invalid_submission(self, client, submissions):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        IDX = 1  # previous tests delete 1-30 submissions from test database
        response = client.get(comments_url(IDX))

        assert response.status_code == 404
        assert '404.html' in response.templates[0].name

    def test_comments_GET_submission_with_comments(self, client, submissions):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        idx = random.randint(0, 29)
        submission_id = submissions[idx].id
        url = reverse('apps.blog:post', kwargs={'thread_id': submission_id})
        Comment.objects.create(author=user, submission=submissions[idx], content="test comment")

        response = client.get(url)
        submission = response.context['submission']
        comments = response.context['comments']
        comment_votes = response.context['comment_votes']

        assert response.status_code == 200
        assert 'submission' in response.context
        assert 'comments' in response.context
        assert 'comment_votes' in response.context
        assert submission == submissions[idx]
        assert len(comments) == 1
        assert 'comments.html' in response.templates[0].name


@pytest.mark.django_db
class TestSubmitView:
    """Tests for submit view"""

    def test_submission_POST_not_authenticated(self, submission_url):
        pass

    def test_submission_POST_authenticated_not_staff(self, submission_url):
        pass

    def test_submission_POST_staff_valid_data(self, submission_url):
        pass

    def test_submission_POST_staff_invalid_data(self, submission_url):
        pass


