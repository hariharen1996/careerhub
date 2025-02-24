from rest_framework import serializers
from .models import EmployerProfile,Jobs

class EmployerSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    class Meta:
        model = EmployerProfile
        fields = ['employer_image','company_name','company_logo','company_website_url','company_description','company_location','employer_email','employer_contact','company_startdate','company_linkedin','company_size']

class JobSerializer(serializers.ModelSerializer):
    employer = serializers.PrimaryKeyRelatedField(queryset=EmployerProfile.objects.all())
    posted_time = serializers.DateTimeField(format='%Y-%m-%d %H-%M-S')
    application_deadline = serializers.DateField(format='%Y-%m-%d')
    company_name = serializers.CharField(source='employer.company_name',read_only=True)
    company_logo = serializers.CharField(source='employer.company_logo',read_only=True)

    class Meta:
        model = Jobs
        fields = ['employer','title','description','location','min_salary','max_salary','salary_range','work_mode','role','experience','time_range','created_at','posted_time','application_deadline','number_of_openings','job_skills','status','company_name','company_logo']
    



