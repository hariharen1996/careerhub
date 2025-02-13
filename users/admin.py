from django.contrib import admin
from .models import CustomUsers,ApplicantProfile

# Register your models here.
admin.site.register(CustomUsers)
admin.site.register(ApplicantProfile)
