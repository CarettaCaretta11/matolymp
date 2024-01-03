# import pytest
#
# from apps.user.models import User
# from apps.user.tests.factories import UserFactory
#
#
# @pytest.fixture(autouse=True)
# def media_storage(settings, tmpdir):
#     settings.MEDIA_ROOT = tmpdir.strpath
#
#
# @pytest.fixture
# def user(db) -> User:
#     return UserFactory()
