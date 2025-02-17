from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .forms import EmployerProfileForm
from django.contrib import messages

# Create your views here.
@login_required
def home_view(request):
    return render(request,'job/home.html',{'title':'Home'})

@login_required
def dashboard_view(request):
    if request.user.user_type == 'APPLICANT':
        if hasattr(request.user,'applicantprofile'):
            applicantprofile = request.user.applicantprofile
            print(applicantprofile)
            if not applicantprofile.is_allfields_completed():
                messages.warning(request,f"Please complete you profile details to access dashboard")
                return redirect('job-home')
        else:
            messages.warning(request,f"Please complete you profile details to access dashboard")
            return redirect('job-home') 

    elif request.user.user_type == 'EMPLOYER':
        if hasattr(request.user,'employerprofile'):
            employerprofile = request.user.employerprofile
            print(employerprofile)
            if not employerprofile.is_allfields_completed():
                messages.warning(request,f"Please complete you profile details to access dashboard")
                return redirect('job-home')
        else:
            messages.warning(request,f"Please complete you profile details to access dashboard")
            return redirect('job-home') 
    

    return render(request,'job/dashboard.html',{'title':'Dashboard'})

@login_required
def employer_view(request):
    if request.user.user_type == 'APPLICANT':
        return redirect('job-home')

    if request.method == 'POST':
        form = EmployerProfileForm(request.POST,request.FILES,instance=request.user.employerprofile)
        if form.is_valid():
            employer = form.save(commit=False)
            employer.user = request.user
            employer.save()
            messages.success(request,'Employer profile details has been updated!')
            return redirect('dashboard')
    else:
        form = EmployerProfileForm(instance=request.user.employerprofile)
    return render(request,'job/employer.html',{'form':form,'title':'EmployerProfileForm'})
