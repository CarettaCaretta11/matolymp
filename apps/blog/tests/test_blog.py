"""
Tests for 'Submission', 'Comment', and 'Vote' models.
"""

from django.test import TestCase, Client
from django.contrib import messages
from django.contrib.auth import authenticate
from django.urls import reverse

from apps.blog.forms import SubmissionForm
from apps.blog.models import Submission, Comment, Vote
from apps.user.models import User

import json
import pytest


@pytest.fixture
def client():
    return Client()


def comments_url(thread_id=None):
    return reverse("apps.blog:post", kwargs={"thread_id": thread_id})


def delete_submission_url(thread_id=None):
    return reverse("apps.blog:delete_post", kwargs={"thread_id": thread_id})


def edit_submission_url(thread_id=None):
    return reverse("apps.blog:update_post", kwargs={"thread_id": thread_id})


@pytest.fixture
def frontpage_url():
    return reverse("frontpage")


@pytest.fixture
def post_comment_url():
    return reverse("apps.blog:post_comment")


@pytest.fixture
def submissions():
    # note: object_id's are not always 1-30 since we delete submissions
    # and create new ones in other tests
    return [Submission.objects.create(title=f"Submission {i}") for i in range(30)]


@pytest.fixture
def submission_url():
    return reverse("apps.blog:submit")


@pytest.fixture
def vote_url():
    return reverse("apps.blog:vote")


@pytest.mark.django_db
def test_GET_about(client):
    response = client.get(reverse("apps.blog:about"))
    assert response.status_code == 200
    assert response.templates[0].name == "about.html"


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
        submission_id = submissions[0].id
        url = reverse("apps.blog:post", kwargs={"thread_id": submission_id})
        response = client.get(url)

        assert response.status_code == 200
        assert "comments.html" in response.templates[0].name

    def test_comments_GET_not_authenticated(self, client, submissions):
        post = submissions[0]
        response = client.get(comments_url(post.id))

        assert response.status_code == 302  # Redirect to login page
        assert response.url == "/login/?next=" + comments_url(post.id)

    def test_comments_GET_invalid_submission(self, client, submissions):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        response = client.get(comments_url(1))  # previous tests delete 1-30 submissions from test database

        assert response.status_code == 404
        assert "404.html" in response.templates[0].name

    def test_comments_GET_submission_with_comments_votes(self, client, submissions):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        submission_id = submissions[0].id
        url = comments_url(submission_id)

        cmt = Comment.create(author=user, content="test comment", parent=submissions[0])
        cmt.save()
        vote = Vote.create(user=user, comment=cmt, vote_value=1)
        vote.save()

        response = client.get(url)
        submission = response.context["submission"]
        comments = response.context["comments"]
        comment_votes = response.context["comment_votes"]

        assert response.status_code == 200
        assert comment_votes == {cmt.id: 1}
        assert submission == submissions[0]
        assert len(comments) == 1
        assert comments[0] == cmt
        assert "comments.html" in response.templates[0].name


@pytest.mark.django_db
class TestPostCommentView:
    """Tests for post_comment view"""

    def test_GET_request(self, client, post_comment_url):
        response_get = client.get(post_comment_url)
        assert response_get.status_code == 405  # HTTP 405 Method Not Allowed

    def test_POST_authenticated(self, client, post_comment_url):
        response = client.post(post_comment_url)
        content = json.loads(response.content)
        expected_message = "You need to log in to post new comments."

        assert response.status_code == 200
        assert content["msg"] == expected_message

    def test_POST_authenticated_invalid_data(self, client, post_comment_url):
        User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        submission = Submission.objects.create(title="test_submission")
        invalid_data = [
            {"parentType": "", "parentId": "", "commentContent": ""},
            {"parentType": "test_type", "parentId": submission.id, "commentContent": "test_content"},
            {"parentType": "comment", "parentId": submission.id, "commentContent": ""},
            {"parentType": "submission", "parentId": "not_an_integer", "commentContent": "test_content"},
            {"parentType": "submission", "parentId": submission.id + 1, "commentContent": "test_content"},
        ]

        response = client.post(post_comment_url, invalid_data[0])
        assert response.status_code == 400

        response = client.post(post_comment_url, invalid_data[1])
        assert response.status_code == 400

        response = client.post(post_comment_url, invalid_data[2])
        assert response.content == b'{"msg": "You have to write something."}'

        response = client.post(post_comment_url, invalid_data[3])
        assert response.status_code == 400

        response = client.post(post_comment_url, invalid_data[4])
        assert response.status_code == 400

    def test_POST_authenticated_submission_parent(self, client, post_comment_url):
        User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        submission = Submission.objects.create(title="test_submission")
        valid_data = {"parentType": "submission", "parentId": submission.id, "commentContent": "test_content"}
        response = client.post(post_comment_url, valid_data)
        new_comment = Comment.objects.all().last()

        assert response.status_code == 200
        assert new_comment.author.username == "test_user"
        assert new_comment.submission == submission
        assert new_comment.content == valid_data["commentContent"]

    def test_POST_authenticated_comment_parent(self, client, post_comment_url):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        submission = Submission.objects.create(title="test_submission")
        comment = Comment.create(author=user, content="test_content", parent=submission)
        comment.save()

        valid_data = {"parentType": "comment", "parentId": comment.id, "commentContent": "test_content"}
        response = client.post(post_comment_url, valid_data)
        new_comment = Comment.objects.all().last()

        assert response.status_code == 200
        assert new_comment.author.username == "test_user"
        assert new_comment.parent == comment
        assert new_comment.content == valid_data["commentContent"]


@pytest.mark.django_db
class TestVoteCommentView:
    """Tests for vote view"""

    def test_GET_request(self, client, vote_url):
        response_get = client.get(vote_url)
        assert response_get.status_code == 405  # HTTP 405 Method Not Allowed

    def test_vote_POST_not_authenticated(self, client, vote_url):
        response = client.post(vote_url)
        assert response.status_code == 403  # HTTP 403 Forbidden

    def test_vote_POST_invalid_new_vote_value(self, client, vote_url):
        User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")

        invalid_value = 0.5
        response = client.post(vote_url, {"vote_value": invalid_value})
        assert response.status_code == 400

        non_convertible_value = "abc"
        client.post(vote_url, {"vote_value": non_convertible_value})
        assert response.status_code == 400

        empty_value = ""
        client.post(vote_url, {"vote_value": empty_value})
        assert response.status_code == 400

    def test_vote_POST_invalid_data(self, client, vote_url):
        User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")

        response = client.post(vote_url, {"vote_value": 1})  # no what_id
        assert response.status_code == 400
        assert response.content == b"Not all values were provided!"

        response = client.post(vote_url, {"what_id": 1})  # no vote_value
        assert response.status_code == 400
        assert response.content == b"Wrong value for the vote!"

        response = client.post(vote_url)  # no data
        assert response.status_code == 400
        assert response.content == b"Wrong value for the vote!"

    def test_vote_POST_new_vote(self, client, submissions, vote_url):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        submission = submissions[0]
        cmt = Comment.create(author=user, content="test_content", parent=submission)
        cmt.save()

        response = client.post(vote_url, {"what_id": cmt.id, "vote_value": 1})
        assert Vote.objects.all().count() == 1  # new vote created
        assert Vote.objects.all().last().user == user
        assert Vote.objects.all().last().comment == cmt
        assert Vote.objects.all().last().value == 1

        response = client.post(vote_url, {"what_id": cmt.id, "vote_value": -1})
        assert Vote.objects.all().count() == 1  # new vote created
        assert Vote.objects.all().last().user == user
        assert Vote.objects.all().last().comment == cmt
        assert Vote.objects.all().last().value == -1

    def test_vote_POST_existing_vote(self, client, submissions, vote_url):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        submission = submissions[0]
        cmt = Comment.create(author=user, content="test_content", parent=submission)
        cmt.save()

        vote = Vote.create(user=user, comment=cmt, vote_value=1)
        vote.save()
        response = client.post(vote_url, {"what_id": cmt.id, "vote_value": 1})
        content = json.loads(response.content)
        assert content["voteDiff"] == -1

        vote = Vote.create(user=user, comment=cmt, vote_value=1)
        vote.save()
        response = client.post(vote_url, {"what_id": cmt.id, "vote_value": -1})
        content = json.loads(response.content)
        assert content["voteDiff"] == -2

        vote = Vote.create(user=user, comment=cmt, vote_value=-1)
        vote.save()
        response = client.post(vote_url, {"what_id": cmt.id, "vote_value": -1})
        content = json.loads(response.content)
        assert content["voteDiff"] == 1

        vote = Vote.create(user=user, comment=cmt, vote_value=-1)
        vote.save()
        response = client.post(vote_url, {"what_id": cmt.id, "vote_value": 1})
        content = json.loads(response.content)
        assert content["voteDiff"] == 2

        vote = Vote.create(user=user, comment=cmt, vote_value=0)
        vote.save()
        response = client.post(vote_url, {"what_id": cmt.id, "vote_value": 1})
        content = json.loads(response.content)
        assert content["voteDiff"] == 1

        vote = Vote.create(user=user, comment=cmt, vote_value=0)
        vote.save()
        response = client.post(vote_url, {"what_id": cmt.id, "vote_value": -1})
        content = json.loads(response.content)
        assert content["voteDiff"] == -1

        # valid existing vote, invalid new vote
        vote = Vote.create(user=user, comment=cmt, vote_value=0)
        vote.save()
        response = client.post(vote_url, {"what_id": cmt.id, "vote_value": -1.5})
        assert response.status_code == 400
        assert response.content == b"Wrong value for the vote!"

        # valid existing vote, invalid new vote
        vote = Vote.create(user=user, comment=cmt, vote_value=0)
        vote.save()
        response = client.post(vote_url, {"what_id": cmt.id, "vote_value": 1.5})
        assert response.status_code == 400
        assert response.content == b"Wrong value for the vote!"

        # invalid existing vote (somehow), valid new vote
        vote = Vote.create(user=user, comment=cmt, vote_value=5)
        vote.save()
        response = client.post(vote_url, {"what_id": cmt.id, "vote_value": 1})
        assert response.status_code == 400
        assert response.content == b"Wrong values for old/new vote combination"


@pytest.mark.django_db
class TestSubmitView:
    """Tests for submit view"""

    def test_submission_GET_not_authenticated(self, client, submission_url):
        response = client.get(submission_url)
        assert response.status_code == 302
        assert response.url == "/login/?next=" + submission_url

    def test_submission_GET_authenticated_not_staff(self, client, submission_url):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        response = client.get(submission_url)
        assert response.status_code == 403

    def test_submission_GET_authenticated_staff(self, client, submission_url):
        user = User.objects.create_user(username="test_user", password="test_password", is_staff=True)
        client.login(username="test_user", password="test_password")
        response = client.get(submission_url)
        assert response.status_code == 200
        assert response.templates[0].name == "submit.html"

    def test_submission_POST_invalid_data(self, client, submission_url):
        User.objects.create_user(username="test_user", password="test_password", is_staff=True)
        client.login(username="test_user", password="test_password")
        invalid_data = [
            {"title": "", "content": "test_content"},  # min_length=1 in Submission
            {"title": "title" * 51, "content": "test_content"},  # max_length=250 for title
        ]

        form = SubmissionForm(data=invalid_data[0])
        assert not form.is_valid()
        assert "title" in form.errors
        assert form.errors["title"][0] == "This field is required."
        response = client.post(submission_url, invalid_data[0])
        assert response.status_code == 200
        assert response.templates[0].name == "submit.html"
        assert "This field is required." in response.content.decode("utf-8")

        form = SubmissionForm(data=invalid_data[1])
        assert not form.is_valid()
        assert "title" in form.errors
        assert form.errors["title"][0] == "Ensure this value has at most 250 characters (it has 255)."
        response = client.post(submission_url, invalid_data[1])
        assert response.status_code == 200
        assert response.templates[0].name == "submit.html"
        assert "Ensure this value has at most 250 characters (it has 255)." in response.content.decode("utf-8")

    def test_submission_POST_valid_data(self, client, submission_url):
        valid_data = [
            {
                "title": "just_the_title",  # content is optional
            },
            {"title": "a", "content": "test_content"},  # len(title) == 1
            {"title": "test_title", "content": "test_content"},
            {"title": "test_title", "content": "content___" * 50000},  # no max_length for content
            {"title": "title" * 50, "content": "test_content"},
        ]

        user = User.objects.create_user(username="test_user", password="test_password", is_staff=True)
        client.login(username="test_user", password="test_password")

        response = client.post(submission_url, valid_data[0])
        submission = Submission.objects.all().last()
        assert response.status_code == 302
        assert response.url == comments_url(submission.id)

        response = client.post(submission_url, valid_data[1])
        submission = Submission.objects.all().last()
        assert response.status_code == 302
        assert response.url == comments_url(submission.id)

        response = client.post(submission_url, valid_data[2])
        submission = Submission.objects.all().last()
        assert response.status_code == 302
        assert response.url == comments_url(submission.id)

        response = client.post(submission_url, valid_data[3])
        submission = Submission.objects.all().last()
        assert response.status_code == 302
        assert response.url == comments_url(submission.id)

        response = client.post(submission_url, valid_data[4])
        submission = Submission.objects.all().last()
        assert response.status_code == 302
        assert response.url == comments_url(submission.id)


@pytest.mark.django_db
class TestUpdateSubmissionView:
    """Tests for update_submission view"""

    def test_update_submission_GET_not_authenticated(self, client, submissions):
        submission = submissions[0]
        response = client.get(edit_submission_url(submission.id))
        assert response.status_code == 302
        assert response.url == "/login/?next=" + edit_submission_url(submission.id)

    def test_update_submission_GET_authenticated_not_author(self, client, submissions):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")

        submission = submissions[0]
        response = client.get(edit_submission_url(submission.id))
        assert response.status_code == 403

    def test_update_submission_GET_authenticated_author(self, client, submissions):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")

        submission = Submission.objects.create(title="test_submission", content="test_content", author=user)
        response = client.get(edit_submission_url(submission.id))
        assert response.status_code == 200
        assert response.templates[0].name == "update_submission.html"

    def test_update_submission_POST_not_authenticated(self, client, submissions):
        submission = submissions[0]
        response = client.post(edit_submission_url(submission.id))
        assert response.status_code == 302
        assert response.url == "/login/?next=" + edit_submission_url(submission.id)

    def test_update_submission_POST_authenticated_not_author(self, client, submissions):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")

        submission = submissions[0]
        response = client.post(edit_submission_url(submission.id))
        assert response.status_code == 403

    def test_update_submission_POST_authenticated_author_invalid_data(self, client):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        submission = Submission.objects.create(title="test_submission", content="test_content", author=user)

        invalid_data = [
            {"title": "", "content": ""},  # min_length=1 in Submission
            {"title": "title" * 51, "content": "test_content"},  # max_length=250 in Submission
        ]

        form = SubmissionForm(data=invalid_data[0])
        assert not form.is_valid()
        assert "title" in form.errors
        assert form.errors["title"][0] == "This field is required."
        response = client.post(edit_submission_url(submission.id), invalid_data[0])
        assert response.status_code == 200
        assert response.templates[0].name == "update_submission.html"
        assert "This field is required." in response.content.decode("utf-8")
        assert submission.title == "test_submission"
        assert submission.content == "test_content"

        form = SubmissionForm(data=invalid_data[1])
        assert not form.is_valid()
        assert "title" in form.errors
        assert form.errors["title"][0] == "Ensure this value has at most 250 characters (it has 255)."
        response = client.post(edit_submission_url(submission.id), invalid_data[1])
        assert response.status_code == 200
        assert response.templates[0].name == "update_submission.html"
        assert "Ensure this value has at most 250 characters (it has 255)." in response.content.decode("utf-8")
        assert submission.title == "test_submission"
        assert submission.content == "test_content"

    def test_update_submission_POST_authenticated_author_valid_data(self, client):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        submission = Submission.objects.create(title="test_submission", content="test_content", author=user)

        valid_data = [
            {
                "title": "just_the_title",  # content is optional
            },
            {"title": "a", "content": "test_content"},  # len(title) == 1
            {"title": "test_title_1", "content": "test_content_1"},
            {"title": "test_title", "content": "content___" * 50000},  # no max_length for content
            {"title": "title" * 50, "content": "test_content"},
        ]

        response = client.post(edit_submission_url(submission.id), valid_data[0])
        submission.refresh_from_db()
        assert response.status_code == 302
        assert response.url == comments_url(submission.id)
        assert submission.title == valid_data[0]["title"]
        assert submission.content == ""
        assert submission.modified
        assert submission.updated

        response = client.post(edit_submission_url(submission.id), valid_data[1])
        submission.refresh_from_db()
        assert response.status_code == 302
        assert response.url == comments_url(submission.id)
        assert submission.title == valid_data[1]["title"]
        assert submission.content == valid_data[1]["content"]
        assert submission.modified
        assert submission.updated

        response = client.post(edit_submission_url(submission.id), valid_data[2])
        submission.refresh_from_db()
        assert response.status_code == 302
        assert response.url == comments_url(submission.id)
        assert submission.title == valid_data[2]["title"]
        assert submission.content == valid_data[2]["content"]
        assert submission.modified
        assert submission.updated

        response = client.post(edit_submission_url(submission.id), valid_data[3])
        submission.refresh_from_db()
        assert response.status_code == 302
        assert response.url == comments_url(submission.id)
        assert submission.title == valid_data[3]["title"]
        assert submission.content == valid_data[3]["content"]
        assert submission.modified
        assert submission.updated


@pytest.mark.django_db
class TestDeleteSubmissionView:
    """Tests for delete_submission view"""

    def test_delete_submission_GET_not_allowed(self, client, submissions):
        submission = submissions[0]
        response = client.get(delete_submission_url(submission.id))
        assert response.status_code == 405  # HTTP 405 Method Not Allowed

        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")
        submission = Submission.objects.create(title="test_submission", author=user)
        response = client.get(delete_submission_url(submission.id))
        assert response.status_code == 405  # HTTP 405 Method Not Allowed

    def test_delete_submission_POST_not_authenticated(self, client, submissions):
        submission = submissions[0]
        response = client.post(delete_submission_url(submission.id))
        assert response.status_code == 302
        assert response.url == "/login/?next=" + delete_submission_url(submission.id)

    def test_delete_submission_POST_authenticated_not_author(self, client, submissions):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")

        submission = submissions[0]
        response = client.post(delete_submission_url(submission.id))
        assert response.status_code == 403

    def test_delete_submission_POST_authenticated_author(self, client):
        user = User.objects.create_user(username="test_user", password="test_password")
        client.login(username="test_user", password="test_password")

        submission = Submission.objects.create(title="test_submission", author=user)
        assert Submission.objects.all().count() == 1
        response = client.post(delete_submission_url(submission.id))
        assert response.status_code == 302
        assert response.url == reverse("frontpage")
        messages_list = list(messages.get_messages(response.wsgi_request))
        assert messages_list[0].message == "Submission deleted"
        assert Submission.objects.all().count() == 0
