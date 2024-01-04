import django
from django.conf import settings

def pytest_configure():
    django.setup()
