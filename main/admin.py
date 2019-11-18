from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Image
from .models import User


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "uploaded"]
    search_fields = ["id"]
    list_filter = ["uploaded"]
    ordering = ["-uploaded"]


@admin.register(User)
class MyUserAdmin(UserAdmin):
    fieldsets = (
        ("Credentials", {"fields": ("username", "email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        (
            "Important dates",
            {"fields": ("last_login", "date_joined", "upgraded_until")},
        ),
    )
    list_display = ("email", "upgraded_until", "is_staff", "date_joined")
    search_fields = ("email",)
    ordering = ["email"]
