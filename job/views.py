from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .forms import EmployerProfileForm,JobForm
from django.contrib import messages
from .models import EmployerProfile,Jobs

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
    
    jobs = Jobs.objects.all()
    print(jobs)

    roles = ['Software Development', 'Software Testing', 'Devops', 'Machine Learning', 'Business Development']
    locations = ['all', 'chennai', 'bengaluru', 'coimbatore', 'madurai', 'delhi', 'hyderabad']
    salaries = [('0-3', '0-3 Lakhs'), ('3-6', '3-6 Lakhs'), ('6-10', '6-10 Lakhs'), ('10-15', '10-15 Lakhs'), ('15-20', '15-20 Lakhs'), ('20+', '20+ Lakhs')]

    

    return render(request,'job/dashboard.html',{'jobs':jobs,'title':'Dashboard','roles':roles,'salaries':salaries,'locations':locations})

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


@login_required
def create_jobs_view(request):
    if request.user.user_type == 'APPLICANT':
        return redirect('job-home')

    if request.method == 'POST':
        form = JobForm(request.POST,request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            employer = EmployerProfile.objects.get(user=request.user)
            job.employer = employer
            job.save()
            messages.success(request,'New Job has been created!')
            return redirect('dashboard')
    else:
        form = JobForm()
    
    return render(request,'job/create_job.html',{'form':form,'title':'Job Form'})
