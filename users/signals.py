from django.db.models.signals import post_save,post_migrate
from django.dispatch import receiver 
from .models import CustomUsers,ApplicantProfile
from job.models import EmployerProfile

@receiver(post_save,sender=CustomUsers)
def create_applicant_profile(sender,instance,created,**kwargs):
    if created:
        if instance.user_type == 'APPLICANT':
            ApplicantProfile.objects.get_or_create(user=instance)
        elif instance.user_type == 'EMPLOYER':
            EmployerProfile.objects.get_or_create(user=instance)
       

@receiver(post_migrate)
def create_existing_profile(sender,**kwargs):
    applicant_profile = CustomUsers.objects.filter(applicantprofile__isnull=True,user_type='APPLICANT')
    for user in applicant_profile:
        ApplicantProfile.objects.get_or_create(user=user)
    
    employer_profile = CustomUsers.objects.filter(employerprofile__isnull=True,user_type='EMPLOYER')
    for user in employer_profile:
        EmployerProfile.objects.get_or_create(user=user)