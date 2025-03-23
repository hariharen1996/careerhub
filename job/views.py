from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import EmployerProfileForm,JobForm,UpdateJobApplicationForm
from django.contrib import messages
from .models import EmployerProfile,Jobs,SaveJobs,JobApplications
from django.utils import timezone 
from django.http import Http404
from users.models import ApplicantProfile
from django.core.mail import send_mail,EmailMessage
from django.conf import settings
import mimetypes
from django.core.exceptions import ObjectDoesNotExist
import requests
from django.core.paginator import Paginator,EmptyPage,InvalidPage
from typing import List,Optional,Dict
import logging


logger = logging.getLogger(__name__)

# Create your views here.
@login_required
def home_view(request):
    return render(request,'job/home.html',{'title':'Home'})

def get_user_profile(user) -> Optional[object]:
    if user.user_type == 'APPLICANT' and hasattr(user, 'applicantprofile'):
        return user.applicantprofile
    elif user.user_type == 'EMPLOYER' and hasattr(user, 'employerprofile'):
        return user.employerprofile
    return None

def check_profile(profile: Optional[object]) -> bool:
    if profile and not profile.is_allfields_completed():
        return False
    return True

def get_job_data(params: Dict[str,List[str]]) -> List[Dict]:
    url = 'http://127.0.0.1:8000/api/dashboard-api/'

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        api_response = response.json()
        job_data = api_response.get('jobs', [])
        return job_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from API: {e}")
        return []
    except ValueError as e:
        logger.error(f"Invalid data received from API: {e}")
        return []

def filter_jobs(job_data:List[Dict],params:Dict[str,List[str]]) -> List[Dict]:
    if params['work_mode']:
        job_data = [job for job in job_data if job['work_mode'].lower() == params['work_mode'].lower()]
    if params['salary_range[]']:
        job_data = [job for job in job_data if job['salary_range'] in params['salary_range[]'] or not params['salary_range[]']]
    if params['location[]']:
        job_data = [job for job in job_data if job['location'].lower() in [loc.lower() for loc in params['location[]']] or not params['location[]']]

    return sorted(job_data, key=lambda x: x['created_at'], reverse=True)

def get_filter_names(request) -> List[str]:
    filter_names = []

    if request.GET.get('search'):
        filter_names.append(f"Search: {request.GET.get('search')}")
    if request.GET.get('work-mode'):
        filter_names.append(f"Work Mode: {request.GET.get('work-mode')}")
    if request.GET.getlist('salary-range[]'):
        filter_names.append(f"Salary Range: {', '.join(request.GET.getlist('salary-range[]'))}")
    if request.GET.getlist('locations[]'):
        filter_names.append(f"Location: {', '.join(request.GET.getlist('locations[]'))}")
    if request.GET.get('role'):
         filter_names.append(f"Role: {request.GET.get('role')}")
    if request.GET.get('experience'):
        filter_names.append(f"Experience: {request.GET.get('experience')} years")
    if request.GET.get('time-range'):
        filter_names.append(f"Time Range: {request.GET.get('time-range')} days")

    return filter_names


@login_required
def dashboard_view(request):
    profile = get_user_profile(request.user)

    if not check_profile(profile):
        profile_type = 'applicant' if request.user.user_type == 'APPLICANT' else 'employer'
        messages.warning(request, f"Please complete your {profile_type} profile details to access dashboard")
        return redirect('job-home')

    params: Dict[str, List[str]] = {
        'search': request.GET.get('search', ''),
        'work_mode': request.GET.get('work-mode', ''),
        'salary_range[]': request.GET.getlist('salary-range[]', []),
        'location[]': request.GET.getlist('locations[]', []),
        'role': request.GET.get('role', ''),
        'experience': request.GET.get('experience', ''),
        'time_range': request.GET.get('time-range', 0),
    }

    job_data = get_job_data(params)
    job_data = filter_jobs(job_data, params)

    paginator = Paginator(job_data, 5)
    page_number = request.GET.get('page')
    try:
        page_data = paginator.get_page(page_number)
    except (EmptyPage, InvalidPage):
        page_data = paginator.get_page(1)

    start_index = (page_data.number - 1) * paginator.per_page + 1
    end_index = start_index + len(page_data) - 1
    total_jobs = paginator.count

    filter_names = get_filter_names(request)

    saved_job_id = SaveJobs.objects.filter(user=request.user).values_list('job', flat=True) if request.user.is_authenticated else []

    roles: List[str] = ['Software Development', 'Software Testing', 'Devops', 'Machine Learning', 'Business Development']
    locations: List[str] = ['all', 'chennai', 'bengaluru', 'coimbatore', 'madurai', 'delhi', 'hyderabad']
    salaries_data: List[tuple] = [('0-3', '0-3 Lakhs'), ('3-6', '3-6 Lakhs'), ('6-10', '6-10 Lakhs'), ('10-15', '10-15 Lakhs'), ('15-20', '15-20 Lakhs'), ('20+', '20+ Lakhs')]

    return render(request,'job/dashboard.html',{
            'title':'Dashboard',
            'roles':roles,
            'salaries':salaries_data,
            'locations':locations,
            'saved_job_id':saved_job_id,
            'jobs':page_data,
            'search_query':params['search'],
            'work_mode_query': params['work_mode'],
            'salary_query':params['salary_range[]'],
            'location_query':params['location[]'],
            'role_query': params['role'],
            'experience_query':params['experience'],
            'time_range_query':params['time_range'],
            'filter_names':filter_names,
            'start_index':start_index,
            'end_index':end_index,
            'total_job':total_jobs
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
    
    if not EmployerProfile.objects.filter(user=request.user).exists():
        messages.warning(request, "You need to create an employer profile before posting jobs.")
        return redirect('job-home')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            employer = EmployerProfile.objects.get(user=request.user)
            company_name = employer.company_name 
            company_logo = employer.company_logo
            job_data = form.cleaned_data
            job_data['employer'] = employer.id 
            employer_instance = EmployerProfile.objects.get(id=job_data['employer'])
            job_data['company_name'] = company_name
            job_data['company_logo'] = company_logo 
            
            payload = {
                'employer':employer_instance.id,
                'title':job_data['title'],
                'description': job_data['description'],
                'location': job_data['location'],
                'salary_range': job_data['salary_range'],
                'work_mode': job_data['work_mode'],
                'experience': job_data['experience'],
                'application_deadline': job_data['application_deadline'].strftime('%Y-%m-%d'),
                'role': job_data['role'],
                'number_of_openings': job_data['number_of_openings'],
                'status': job_data['status'],
                'posted_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'skills': job_data['job_skills'], 
                'company_name': company_name,  
                'company_logo': company_logo.url if company_logo else None  
            }

            url = 'http://127.0.0.1:8000/api/create/'
            session = requests.Session()
            session.cookies.update(requests.utils.cookiejar_from_dict(request.COOKIES))
            csrf_token = session.cookies.get('csrftoken')
            
            if not csrf_token:
                messages.error(request,'csrf token is missing/invalid')
                return redirect('dashboard')

            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            }

            response = session.post(url,json=payload,headers=headers)
            print(f"responsestatus: {response.status_code}")
            print(f"responsecontent: {response.content}")

            if response.status_code == 201:
                messages.success(request,'New Job has been created!')
                return redirect('dashboard')
            else:
                messages.error(request, f"There was an error creating the job: {response.content.decode()}")
        
            return redirect('dashboard')      
    else:
        form = JobForm()
    
    return render(request,'job/create_job.html',{'form':form,'title':'Job Form'})

@login_required
def update_job_view(request,id):
    if request.user.user_type == 'APPLICANT':
        return redirect('job-home')
    
    try:
        job = Jobs.objects.get(id=id)
    except Jobs.DoesNotExist:
        messages.error(request,'Job not found')
        return redirect('job-home')
    
    if request.user != job.employer.user:
        messages.error(request,'You are not allowed to update this job')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = JobForm(request.POST,instance=job)
        if form.is_valid():
            employer = EmployerProfile.objects.get(user=request.user)
            job_data = form.cleaned_data
            job_data['employer'] = employer.id 
            job_data['company_name'] = employer.company_name
            job_data['company_logo'] = employer.company_logo
            
            job = form.save()

            payload = {
                'employer': employer.id,
                'title': job.title,
                'description': job.description,
                'location': job.location,
                'salary_range': job.salary_range,
                'work_mode': job.work_mode,
                'experience': job.experience,
                'application_deadline': job.application_deadline.strftime('%Y-%m-%d'),
                'role': job.role,
                'number_of_openings': job.number_of_openings,
                'status': job.status,
                'posted_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'skills': job.job_skills,
                'company_name': employer.company_name,
                'company_logo': employer.company_logo.url if employer.company_logo else None
            }

            url = f'http://127.0.0.1:8000/api/update/{job.id}/'
            session = requests.Session()
            session.cookies.update(requests.utils.cookiejar_from_dict(request.COOKIES))
            csrf_token = session.cookies.get('csrftoken')
            
            if not csrf_token:
                messages.error(request,'csrf token is missing/invalid')
                return redirect('dashboard')

            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            }

            response = session.put(url,json=payload,headers=headers)
            if response.status_code == 200:
                messages.success(request,'Job has been updated!')
                return redirect('dashboard')
            else:
                messages.error(request,'There was an error updating job!')
            
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
    
    url = f'http://127.0.0.1:8000/api/delete/{job.id}/'
    session = requests.Session()
    session.cookies.update(requests.utils.cookiejar_from_dict(request.COOKIES))
    csrf_token = session.cookies.get('csrftoken')
            
    if not csrf_token:
        messages.error(request,'csrf token is missing/invalid')
        return redirect('dashboard')

    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token
    }

    try:
        response = session.delete(url,headers=headers)
        if response.status_code == 204:
            messages.success(request, "Job deleted successfully!")
        elif response.status_code == 403:
            messages.error(request,"You do not have permissions to delete this job!")
        elif response.status_code == 404:
            messages.error(request,"Job not found!")    
        else:
            messages.error(request, f"There was an error deleting the job: {response.text}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Request failed: {str(e)}")

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
