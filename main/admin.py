from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Image
from .models import User


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "user", "uploaded", "processed"]
    search_fields = ["id"]
    list_filter = ["uploaded"]
    ordering = ["-uploaded"]


@admin.register(User)
class MyUserAdmin(UserAdmin):
    fieldsets = (
        ("Credentials", {"fields": ("username", "email", "password", "api_key")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        (
            "Payment stuff",
            {"fields": ("last_payment", "upgraded_until", "storage_space")},
        ),
    )
    list_display = ("email", "upgraded_until", "is_staff", "date_joined")
    search_fields = ("email",)
    ordering = ["email"]
