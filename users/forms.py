from django.contrib.auth.forms import UserCreationForm 
from django import forms
from .models import CustomUsers

class CustomUserForm(UserCreationForm):
    email = forms.EmailField()
    class Meta:
        model = CustomUsers
        fields = ['username','email','user_type','password1','password2']