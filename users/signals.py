from django.db.models.signals import post_save
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