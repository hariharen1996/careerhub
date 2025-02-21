from django.contrib import admin
from .models import EmployerProfile,Jobs,SaveJobs,JobApplications,JobApplicationSkills

# Register your models here.
admin.site.register(EmployerProfile)
admin.site.register(Jobs)
admin.site.register(SaveJobs)
admin.site.register(JobApplications)
admin.site.register(JobApplicationSkills)