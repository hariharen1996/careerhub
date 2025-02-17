from django import forms 
from .models import EmployerProfile

class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = ['employer_image','company_name','company_logo','company_website_url','company_description','company_location','employer_email','employer_contact','company_startdate','company_linkedin','company_size']
    