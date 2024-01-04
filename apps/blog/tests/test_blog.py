"""
Tests for the 'Submission' and 'Comment' models.
"""

from django.test import TestCase, Client
from django.contrib.auth import authenticate, get_user_model
from django.urls import reverse

from apps.blog.forms import SubmissionForm
from apps.blog.models import Submission

import pytest


@pytest.fixture
def client():
    return Client()

