from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from users.models import ApplicantProfile

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

    def is_allfields_completed(self):
        all_fields = [self.employer_image,self.company_name,self.company_logo,self.company_website_url,self.company_description,self.company_location,self.employer_email,self.employer_contact,self.company_startdate,self.company_linkedin,self.company_size]

        return not any(fields is None or (isinstance(fields,str) and fields.strip() == '') or (isinstance(fields,list) and len(fields) == 0) for fields in all_fields)

    def __str__(self):
        return f"{self.user.username} employer"

class Jobs(models.Model):
    SALARY_CHOICES = (
        ('0-3','0-3 Lakhs'),
        ('3-6','3-6 Lakhs'),
        ('6-10','6-10 Lakhs'),
        ('10-15','10-15 Lakhs'),
        ('15-20','15-20 Lakhs'),
        ('20+','20+ Lakhs'),
    )

    
    WORK_MODE_CHOICES = (
        ('WFO',"Work from Office"),
        ('hybrid','Hybrid'),
        ('remote','Remote')
    )

    FRESHNESS_CHOICES = (
        (0, 'Freshness'),
        (1, 'Last 1 Day'),
        (3, 'Last 3 Days'),
        (7, 'Last 7 Days'),
        (15, 'Last 15 Days'),
        (30, 'Last 30 Days'),
    )

    JOB_STATUS_CHOICES = (
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('filled', 'Filled'),
    )

    EXPERIENCE_CHOICES = (
        ('0-1', '0-1 years'),
        ('1-3', '1-3 years'),
        ('3-5', '3-5 years'),
        ('5-7', '5-7 years'),
        ('7-10', '7-10 years'),
        ('10+', '10+ years'),
    )

    employer = models.ForeignKey(EmployerProfile,on_delete=models.CASCADE,related_name='jobs')
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=200)
    min_salary = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    max_salary = models.DecimalField(max_digits=10,decimal_places=2,default=3)
    salary_range = models.CharField(max_length=5,choices=SALARY_CHOICES,default='0-3')
    work_mode = models.CharField(max_length=10,choices=WORK_MODE_CHOICES,default='WFO')
    role = models.CharField(max_length=255)
    experience = models.CharField(max_length=5,choices=EXPERIENCE_CHOICES,default='0-1')
    time_range = models.IntegerField(choices=FRESHNESS_CHOICES,default=0)
    created_at = models.DateTimeField(default=timezone.now)
    posted_time = models.DateTimeField(auto_now_add=True)
    application_deadline = models.DateField(blank=False, null=False,default=timezone.now)
    number_of_openings = models.PositiveIntegerField(default=1)
    job_skills = models.CharField(max_length=500,blank=True,default='python,java,react')
    status = models.CharField(max_length=10,choices=JOB_STATUS_CHOICES,default='open')
    
    def get_job_skills(self):
        return [skill.strip() for skill in self.job_skills.split(',') if skill]
    
    def save(self,*args,**kwargs):
        if self.salary_range == '0-3':
            self.min_salary = 0 
            self.max_salary = 3 
        elif self.salary_range == '3-6':
            self.min_salary = 3
            self.max_salary = 6 
        elif self.salary_range == '6-10':
            self.min_salary = 6
            self.max_salary = 10 
        elif self.salary_range == '10-15':
            self.min_salary = 10
            self.max_salary = 15
        elif self.salary_range == '15-20':
            self.min_salary = 15
            self.max_salary = 20
        elif self.salary_range == '20+':
            self.min_salary = 20
            self.max_salary = 100000
        super(Jobs,self).save(*args,**kwargs)

    def __str__(self):
        return f"{self.title}"

class SaveJobs(models.Model):
    user = models.ForeignKey(CustomUsers,on_delete=models.CASCADE)
    job = models.ForeignKey(Jobs,on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user','job')
    
    def __str__(self):
        return f'{self.user.username} saved {self.job.title}' 

class JobApplicationSkills(models.Model):
    job_application_skills = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['job_application_skills'],name='unique_job_skills')
        ]

    def __str__(self):
        return self.job_application_skills


class JobApplications(models.Model):
    applicant = models.ForeignKey(CustomUsers,on_delete=models.CASCADE)
    job = models.ForeignKey(Jobs,on_delete=models.CASCADE)
    profile = models.ForeignKey(ApplicantProfile,on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)
    JobApplications_skills = models.ManyToManyField(JobApplicationSkills,related_name='job_applications',blank=True)

    class Meta:
        unique_together = ('applicant','job')
    
    def __str__(self):
        return f"{self.applicant.username} applied for {self.job.title}"