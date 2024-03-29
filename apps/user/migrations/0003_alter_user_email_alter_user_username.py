# Generated by Django 4.2.8 on 2024-01-04 15:30

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0002_alter_user_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True, verbose_name="email address"),
        ),
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(
                max_length=20,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        code="invalid_username",
                        message="Username can only contain alphanumeric characters and underscores and can't exceed 20 chars.",
                        regex="^[0-9a-zA-Z_]{1,20}$",
                    )
                ],
            ),
        ),
    ]
