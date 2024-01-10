from django.contrib import admin
from .models import Submission, Comment, Vote


# Register your models here.
class SubmissionInline(admin.TabularInline):
    model = Submission
    max_num = 10


class CommentsInline(admin.StackedInline):
    model = Comment
    max_num = 10


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("title", "content", "author", "timestamp", "updated", "comment_count")
    inlines = [CommentsInline]


admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Comment)
admin.site.register(Vote)
