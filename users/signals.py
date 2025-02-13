from django.db.models.signals import post_save,post_migrate
from django.dispatch import receiver 
from .models import CustomUsers,ApplicantProfile

@receiver(post_save,sender=CustomUsers)
def create_applicant_profile(sender,instance,created,**kwargs):
    if created:
        ApplicantProfile.objects.create(user=instance)

@receiver(post_save,sender=CustomUsers)
def save_applicant_profile(sender,instance,**kwargs):
    try:
        instance.applicantprofile.save()
    except ApplicantProfile.DoesNotExist:
        pass

@receiver(post_migrate)
def create_existing_profile(sender,**kwargs):
    applicant_profile = CustomUsers.objects.filter(applicantprofile__isnull=True,user_type='APPLICANT')
    for user in applicant_profile:
        ApplicantProfile.objects.get_or_create(user=user)