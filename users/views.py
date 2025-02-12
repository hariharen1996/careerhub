from django.shortcuts import render,redirect
from .forms import CustomUserForm,LoginForm
from django.contrib.auth import login,authenticate,logout

# Create your views here.
def register_view(request):
    if request.method == 'POST':
        forms = CustomUserForm(request.POST)
        if forms.is_valid():
            forms.save()
            return redirect('login')
    else:
        forms = CustomUserForm()

    return render(request,'users/register.html',{'forms':forms,'title':'Register'})

def login_view(request):
    if request.method == 'POST':
        forms = LoginForm(request,data=request.POST)
        if forms.is_valid():
            username = forms.cleaned_data.get('username')
            password = forms.cleaned_data.get('password')
            user = authenticate(request,username=username,password=password)
            login(request,user)
            if user is not None:
                return redirect('job-home')    
    else:
        forms = LoginForm()
    return render(request,'users/login.html',{'forms':forms,'title':'Login'})

def logout_view(request):
    logout(request)
    return redirect('login')