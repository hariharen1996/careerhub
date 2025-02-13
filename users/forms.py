from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django import forms
from .models import CustomUsers,ApplicantProfile
import re
from django.core.exceptions import ValidationError

class CustomUserForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder':'Email'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Confirm Password'}))
    
    class Meta:
        model = CustomUsers
        fields = ['username','email','user_type','password1','password2']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise forms.ValidationError('Username must be atleast 3 characters in length')
        if CustomUsers.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUsers.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already exists')
        return email
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if not re.search(r'[A-Z]',password):
            raise ValidationError('Password must contain atleast one uppercase letters')
        if not re.search(r'[a-z]',password):
            raise ValidationError('Password must contain atleast one lowercase letters')
        if not re.search(r'[0-9]',password):
            raise ValidationError('Password must contain atleast one digit')
        if not re.search(r'[@#$!%*?&^()]',password):
            raise ValidationError('Password must contain atleast one special character')
        return password
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError('password and confirm password must match')
        return password2

        
    
class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter your username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Enter your password'}))

class ApplicantProfileForm(forms.ModelForm):
    class Meta:
        model = ApplicantProfile
        fields = ['user_image','user_bio','user_education','user_cgpa','work_experience','user_resume','user_location','user_skills']

class CustomUserUpdateForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'update your username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder':'update your email'}))

    class Meta:
        model = CustomUsers
        fields = ['username','email']
    