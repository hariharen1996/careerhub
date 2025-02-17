from django.db import models
from django.contrib.auth import get_user_model

CustomUsers = get_user_model()

# Create your models here.
class EmployerProfile(models.Model):
    user = models.OneToOneField(CustomUsers,on_delete=models.CASCADE)
    employer_image = models.ImageField(upload_to='employerprofile/',default='employer_default.png')
    company_name = models.CharField(max_length=200)
    company_logo = models.ImageField(upload_to='companylogo/',default='company_logo.png')
    company_website_url = models.URLField(blank=True,null=True)
    company_description = models.TextField()
    company_location = models.CharField(max_length=200)
    employer_email = models.EmailField()
    employer_contact = models.CharField(max_length=15,blank=True,null=True)
    company_startdate = models.DateField(blank=True,null=True)
    company_linkedin = models.URLField(blank=True,null=True)
    company_size = models.CharField(max_length=100,blank=True,null=True)

    def __str__(self):
        return f"{self.user.username} employer"
