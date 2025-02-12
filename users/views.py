from django.shortcuts import render,redirect
from .forms import CustomUserForm,LoginForm
from django.contrib.auth import login,authenticate,logout
from django.contrib import messages
from .mixins import RedirectUserMixin
from django.contrib.auth.views import PasswordResetView,PasswordResetCompleteView,PasswordResetConfirmView,PasswordResetDoneView

# Create your views here.
def register_view(request):
    if request.user.is_authenticated:
        return redirect('job-home')
    
    if request.method == 'POST':
        forms = CustomUserForm(request.POST)
        if forms.is_valid():
            forms.save()
            messages.success(request,f'Registered Successfully!')
            return redirect('login')
    else:
        forms = CustomUserForm()

    return render(request,'users/register.html',{'forms':forms,'title':'Register'})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('job-home')

    if request.method == 'POST':
        forms = LoginForm(request,data=request.POST)
        if forms.is_valid():
            username = forms.cleaned_data.get('username')
            password = forms.cleaned_data.get('password')
            user = authenticate(request,username=username,password=password)
            login(request,user)
            if user is not None:
                messages.success(request,f"LoggedIn as {request.user.username}")
                return redirect('job-home')    
    else:
        forms = LoginForm()
    return render(request,'users/login.html',{'forms':forms,'title':'Login'})

def logout_view(request):
    logout(request)
    messages.warning(request,f"You have been logged out!😕")
    return redirect('login')

class CustomPasswordResetView(RedirectUserMixin,PasswordResetView):
    template_name = 'users/password_reset.html'

class CustomPasswordResetCompleteView(RedirectUserMixin,PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'

class CustomPasswordResetDoneView(RedirectUserMixin,PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(RedirectUserMixin,PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'



    

