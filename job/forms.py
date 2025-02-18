from django import forms 
from .models import EmployerProfile,Jobs
from django.core.exceptions import ValidationError

class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = ['employer_image','company_name','company_logo','company_website_url','company_description','company_location','employer_email','employer_contact','company_startdate','company_linkedin','company_size']
        widgets = {
            'company_startdate':forms.DateInput(attrs={'type': 'date'}),
            'company_name': forms.TextInput(attrs={'placeholder': 'Enter company name'}),
            'company_website_url': forms.URLInput(attrs={'placeholder':'Enter company webiste'}),
            'company_description': forms.Textarea(attrs={'placeholder':'About Company'}),
            'company_location':forms.TextInput(attrs={'placeholder':'Enter company location'}),
            'employer_email':forms.EmailInput(attrs={'placeholder':'Enter employer email'}),
            'employer_contact':forms.TextInput(attrs={'placeholder':'Enter employer contact number'}),
            'company_linkedin': forms.URLInput(attrs={'placeholder': "Enter Linkedin Url"}),
           'company_size': forms.TextInput(attrs={'placeholder':'Enter company size'})
        }

    def clean(self):
        cleaned_data = super().clean()
        fields = ['employer_image','company_name','company_logo','company_website_url','company_description','company_location','employer_email','employer_contact','company_startdate','company_linkedin','company_size']

        for data in fields:
            if not cleaned_data.get(data):
                raise ValidationError('Please fill the fields')

        return cleaned_data 

class JobForm(forms.ModelForm):
    class Meta:
        model = Jobs 
        fields = ['title','description','location','salary_range','work_mode','experience','application_deadline','role','number_of_openings','job_skills','status']

        widgets = {
            'application_deadline': forms.DateInput(attrs={'type':'date'}),
            'title': forms.TextInput(attrs={'placeholder':"Enter job title"}),
            'description': forms.Textarea(attrs={'placeholder': "Enter job description"}),
            'location': forms.TextInput(attrs={'placeholder':"Enter job location"}),
            'role': forms.TextInput(attrs={'placeholder':"Enter job role"}),
        }