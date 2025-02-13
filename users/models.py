from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUsers(AbstractUser):
    USER_TYPE = (
        ('APPLICANT','APPLICANT'),
        ('EMPLOYER','EMPLOYER')
    )

    user_type = models.CharField(max_length=20,choices=USER_TYPE,default='APPLICANT')

    def __str__(self):
        return self.username 
    

class ApplicantProfile(models.Model):
    user = models.OneToOneField(CustomUsers,on_delete=models.CASCADE)
    user_image = models.ImageField(upload_to='user_profile',default='default.png')
    user_bio = models.TextField(default='A passionate and result-driven software developer with...')
    user_education = models.CharField(max_length=200,blank=False,null=False,default='ABC Institute Of Technology')
    user_cgpa = models.DecimalField(max_digits=4,decimal_places=2,blank=False,null=False,default=7.65)
    work_experience = models.CharField(max_length=200,default='1 year of experience in software development')
    user_resume = models.FileField(upload_to='user_resume',default='default_resume.pdf')
    user_location = models.CharField(max_length=200,default='State/City')
    user_skills = models.CharField(max_length=500,blank=True,default='python,java,react')

    def __str__(self):
        return f"{self.user.username} Profile"
    
    def get_user_skills(self):
        return [skill.strip() for skill in self.user_skills.split(',') if skill]