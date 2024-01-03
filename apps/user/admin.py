from django.contrib import admin

# Register your models here.
from ..blog.admin import SubmissionInline
from .models import User


class UserAdmin(admin.ModelAdmin):
    inlines = [
        SubmissionInline,
    ]


admin.site.register(User, UserAdmin)
