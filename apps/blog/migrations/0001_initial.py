# Generated by Django 4.2.8 on 2024-01-02 13:25

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("author_name", models.CharField(max_length=12)),
                ("timestamp", models.DateTimeField(default=django.utils.timezone.now)),
                ("ups", models.IntegerField(default=0)),
                ("downs", models.IntegerField(default=0)),
                ("score", models.IntegerField(default=0)),
                ("content", models.TextField(blank=True)),
                ("lft", models.PositiveIntegerField(editable=False)),
                ("rght", models.PositiveIntegerField(editable=False)),
                ("tree_id", models.PositiveIntegerField(db_index=True, editable=False)),
                ("level", models.PositiveIntegerField(editable=False)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Submission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("author_name", models.CharField(max_length=12)),
                ("title", models.CharField(max_length=250)),
                ("url", models.URLField(blank=True, null=True)),
                ("content", models.TextField(blank=True, max_length=5000)),
                ("ups", models.IntegerField(default=0)),
                ("downs", models.IntegerField(default=0)),
                ("score", models.IntegerField(default=0)),
                ("timestamp", models.DateTimeField(default=django.utils.timezone.now)),
                ("comment_count", models.IntegerField(default=0)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Vote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("vote_object_id", models.PositiveIntegerField()),
                ("value", models.IntegerField(default=0)),
                ("submission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="blog.submission")),
            ],
        ),
    ]
