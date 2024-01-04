from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(_("email address"), blank=True, null=True, unique=True)
    username_validator = RegexValidator(
        regex=r"^[0-9a-zA-Z_]{1,20}$",
        message="Username can only contain alphanumeric characters and underscores and can't exceed 20 chars.",
        code="invalid_username",
    )
    username = models.CharField(max_length=20, unique=True, validators=[username_validator])
    about_text = models.TextField(blank=True, null=True, max_length=500, default=None)
    post_karma = models.IntegerField(default=0)  # how useful are this user's posts?
    comment_karma = models.IntegerField(default=0)  # how useful are this user's comments?

    REQUIRED_FIELDS = ["email"]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower().strip()
        else:
            self.email = None
        super(AbstractUser, self).save(*args, **kwargs)

    def __unicode__(self):
        return "<User:{}>".format(self.user.username)
