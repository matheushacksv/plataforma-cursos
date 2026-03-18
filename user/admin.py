from django.contrib import admin
from .models import CustomUser, CustomUserManager

admin.register(CustomUser)
admin.register(CustomUserManager)