# Generated by Django 4.2.8 on 2024-01-10 10:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0008_remove_submission_updated_submission_modified_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="updated",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
