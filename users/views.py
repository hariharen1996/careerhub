from django.shortcuts import render,HttpResponse,redirect
from .forms import UserCreationForm,LoginForm

# Create your views here.
def register_view(request):
    if request.method == 'POST':
        forms = UserCreationForm(request.POST)
        if forms.is_valid():
            forms.save()
            return redirect('login')
    else:
        forms = UserCreationForm()

    return render(request,'users/register.html',{'forms':forms})

def login_view(request):
    if request.method == 'POST':
        forms = LoginForm(request,data=request.POST)
        if forms.method == 'POST':
            forms.save()
            return redirect('login')
    else:
        forms = LoginForm()
    return render(request,'users/login.html',{'forms':forms})