from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django import forms
from .models import CustomUsers

class CustomUserForm(UserCreationForm):
    email = forms.EmailField()
    class Meta:
        model = CustomUsers
        fields = ['username','email','user_type','password1','password2']
    
class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter your username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Enter your password'}))