# Generated by Django 4.2.8 on 2024-01-09 21:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0007_submission_updated_alter_submission_timestamp"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="submission",
            name="updated",
        ),
        migrations.AddField(
            model_name="submission",
            name="modified",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="comment",
            name="timestamp",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
