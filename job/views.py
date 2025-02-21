from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import EmployerProfileForm,JobForm,UpdateJobApplicationForm
from django.contrib import messages
from .models import EmployerProfile,Jobs,SaveJobs,JobApplications
from django.db.models import Q
from django.utils import timezone 
from datetime import timedelta
from django.http import Http404
from users.models import ApplicantProfile
from django.core.mail import send_mail,EmailMessage
from django.conf import settings
import mimetypes
from django.core.exceptions import ObjectDoesNotExist

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
    
    roles = ['Software Development', 'Software Testing', 'Devops', 'Machine Learning', 'Business Development']
    locations = ['all', 'chennai', 'bengaluru', 'coimbatore', 'madurai', 'delhi', 'hyderabad']
    salaries_data = [('0-3', '0-3 Lakhs'), ('3-6', '3-6 Lakhs'), ('6-10', '6-10 Lakhs'), ('10-15', '10-15 Lakhs'), ('15-20', '15-20 Lakhs'), ('20+', '20+ Lakhs')]


    search_query = request.GET.get('search','')
    work_mode_query = request.GET.get('work-mode','')
    salary_query = request.GET.getlist('salary-range[]',[])
    location_query = request.GET.getlist('locations[]',[])
    role_query = request.GET.get('role','')
    experience_query = request.GET.get('experience','')
    time_range_query = request.GET.get('time-range',0)
    current_time = timezone.now()

    if search_query:
        jobs = Jobs.objects.filter(
            Q(title__icontains=search_query) | 
            Q(location__icontains=search_query) | 
            Q(job_skills__icontains=search_query)
        ).distinct()
    
    else:
        jobs = Jobs.objects.all()
    
    if work_mode_query:
        jobs = Jobs.objects.filter(work_mode=work_mode_query)

    if salary_query:
        salary = Q()
        for salaries in salary_query:
            if salaries == '0-3':
                salary |= Q(min_salary__gte=0,max_salary__lte=3)
            if salaries == '3-6':
                salary |= Q(min_salary__gte=3,max_salary__lte=6)
            if salaries == '6-10':
                salary |= Q(min_salary__gte=6,max_salary__lte=10)
            if salaries == '10-15':
                salary |= Q(min_salary__gte=10,max_salary__lte=15)
            if salaries == '15-20':
                salary |= Q(min_salary__gte=15,max_salary__lte=20)
            if salaries == '20+':
                salary |= Q(min_salary__gte=20)
        
        if salary:
            jobs = Jobs.objects.filter(salary)
    
    if location_query:
        location_filter = Q()

        if 'all' not in location_filter:
            for loc in location_query:
                location_filter |= Q(location__icontains=loc)
        jobs = Jobs.objects.filter(location_filter)

    if role_query:
        jobs = Jobs.objects.filter(role__icontains=role_query)

    if experience_query:
        experience = int(experience_query)
        if experience <= 1:
            jobs = Jobs.objects.filter(experience='0-1')
        elif experience <= 3:
            jobs = Jobs.objects.filter(experience='1-3')
        elif experience <= 5:
            jobs = Jobs.objects.filter(experience='3-5')
        elif experience <= 7:
            jobs = Jobs.objects.filter(experience='5-7')
        elif experience <= 10:
            jobs = Jobs.objects.filter(experience='7-10')
        else:
            jobs = Jobs.objects.filter(experience='10+')
    
    if time_range_query:
        try:
            time_range = int(time_range_query)
            if time_range == 0:
                time_limit = current_time - timedelta(hours=1)
            elif time_range_query == 1:
                time_limit = current_time - timedelta(days=1)
            elif time_range_query == 3:
                time_limit = current_time - timedelta(days=3)
            elif time_range_query == 7:
                time_limit = current_time - timedelta(days=7) 
            elif time_range_query == 15:
                time_limit = current_time - timedelta(days=15)
            elif time_range_query == 30:
                time_limit = current_time - timedelta(days=30) 
            else:
                time_limit = current_time
            
            jobs = Jobs.objects.filter(posted_time__gte=time_limit)
        except ValueError:
            pass
    
    saved_job_id = SaveJobs.objects.filter(user=request.user).values_list('job',flat=True)

    return render(request,'job/dashboard.html',{'jobs':jobs,
            'title':'Dashboard',
            'roles':roles,
            'salaries':salaries_data,
            'locations':locations,
            'work_mode_query':work_mode_query,
            'salary_query':salary_query,
            'location_query':location_query,
            'role_query':role_query,
            'experience_query':experience_query,
            'time_range_query':time_range_query,
            'saved_job_id':saved_job_id
            })

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

@login_required
def update_job_view(request,id):
    job = get_object_or_404(Jobs,id=id)

    if request.user != job.employer.user:
        messages.error(request,'You are not allowed to update this job')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = JobForm(request.POST,instance=job)
        if form.is_valid():
            form.save()
            messages.success(request,'Job has been updated!')
            return redirect('dashboard')
    else:
        form = JobForm(instance=job)
    
    return render(request,'job/create_job.html',{'form':form,'title':'Update Job Form'})

@login_required
def delete_job_view(request,id):
    job = get_object_or_404(Jobs,id=id)

    if request.user != job.employer.user:
        messages.error(request,'You are not allowed to delete this job')
        return redirect('dashboard')
    
    if request.method == 'POST':
        job.delete()
        messages.success(request,'Job deleted successfully!')
        return redirect('dashboard')

    return redirect('dashboard')

@login_required
def save_job(request,id):
    try:
        job = Jobs.objects.get(id=id)
    except:
        raise Http404('Job not found')
    
    is_job_saved = SaveJobs.objects.filter(user=request.user,job=job).first()

    if is_job_saved:
        is_job_saved.delete()
        message = 'Job removed from saved jobs'
    else:
        SaveJobs.objects.create(user=request.user,job=job)
        message = 'Job saved successfully'
    
    messages.info(request,message)

    return redirect('dashboard')

def save_jobs(request):
    saved_jobs = SaveJobs.objects.filter(user=request.user)
    return render(request,'job/save_jobs.html',{'saved_jobs':saved_jobs,'title':'Saved Jobs'})


@login_required
def job_details(request,id):
    job = get_object_or_404(Jobs,id=id)
    http_url = request.META.get('HTTP_REFERER','dashboard')
    return render(request,'job/job_details.html',{'title':'Job Details','job':job,'http_url':http_url})


@login_required
def apply_jobs(request,id):
    if not request.user.is_authenticated:  
        messages.error(request,"You need to be logged in to apply for job")
        return redirect('job-home')
    
    job = get_object_or_404(Jobs,id=id)
    profile = get_object_or_404(ApplicantProfile,user=request.user)
    employers = job.employer

    if job.application_deadline > timezone.now().date():
        pass 
    else:
        messages.warning(request,f'Application deadline for this job {job.title} has passed')
        return redirect('dashboard')

    if JobApplications.objects.filter(applicant=request.user,job__employer=employers).exists():
        messages.warning(request,f"You have already applied for a job at {employers.company_name} company")
        return redirect('dashboard')

    if JobApplications.objects.filter(applicant=request.user,job=job).exists():
        messages.warning(request,"You cant apply multiple times for same specific job")
        return redirect('dashboard')
    
    JobApplications.objects.create(applicant=request.user,job=job,profile=profile)

    subject_applicant = f"Job Application Confirmation for {job.title}"
    message_applicant = f"Dear {request.user.username},\n\n" \
                        f"Your application for the job '{job.title}' at {employers.company_name} has been successfully submitted.\n" \
                        f"Best of luck with your application!\n\n" \
                        f"Regards,\nCareerHub Team"
    recipient_applicant = request.user.email
    send_mail(subject_applicant, message_applicant, settings.DEFAULT_FROM_EMAIL, [recipient_applicant])

    subject_employer = f"New Job Application for {job.title}"
    message_employer = f"Dear {employers.user.username},\n\n" \
                       f"New application has been received for the job '{job.title}' from {request.user.username}.\n" \
                       f"Applicant's email: {request.user.email}\n" \
                       f"Profile details: {profile}\n\n" \
                       f"Regards,\nCaeerHub Team"
    recipient_employer = employers.employer_email  

    try:
        resumefile = profile.user_resume
        email = EmailMessage(
            subject_employer,
            message_employer,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_employer]
        )

        if resumefile:
            mime_type, _ = mimetypes.guess_type(resumefile.name)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            email.attach(resumefile.name, resumefile.read(), mime_type)
        
        email.send()
    except ObjectDoesNotExist:
        messages.error(request, "Error: Profile does not have a resume attached.")
        return redirect('dashboard')

    messages.success(request,f"Your application for {job.title} has been submitted successfully")
    return redirect('dashboard')


@login_required
def job_applications(request):
    jobs = JobApplications.objects.all()
    return render(request,'job/job_applications.html',{'applications':jobs})


@login_required
def update_application_skills(request,id):
    if request.user.user_type == 'EMPLOYER':
        return redirect('dashboard')

    job_applications = get_object_or_404(JobApplications,id=id,applicant=request.user)

    if request.method == 'POST':
        form = UpdateJobApplicationForm(request.POST,instance=job_applications)
        if form.is_valid():
            form.save()
            messages.success(request,"Your skills have been updated successfully")
            return redirect('job-applications')
    else:
        form = UpdateJobApplicationForm(instance=job_applications)
    
    return render(request,'job/update_application_skills.html',{'form':form,'job_application':job_applications})
