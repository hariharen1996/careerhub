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
    
