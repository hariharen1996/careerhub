from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import EmployerProfileForm, JobForm, UpdateJobApplicationForm
from django.contrib import messages
from .models import EmployerProfile, Jobs, SaveJobs, JobApplications
from django.utils import timezone
from django.http import Http404, HttpRequest, HttpResponse
from users.models import ApplicantProfile
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
import mimetypes
from django.core.exceptions import ObjectDoesNotExist
import requests
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from typing import List, Optional, Dict, Any, Union
import logging
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.db.models import QuerySet

logger = logging.getLogger(__name__)

class Job:
    
    API_URL = 'http://127.0.0.1:8000/api/'
    
    @staticmethod
    def _get_session(request: HttpRequest) -> requests.Session:
        session = requests.Session()
        session.cookies.update(requests.utils.cookiejar_from_dict(request.COOKIES))
        return session
    
    @staticmethod
    def _get_headers(request: HttpRequest) -> Dict[str, str]:
        session = Job._get_session(request)
        csrf_token = session.cookies.get('csrftoken')
        if not csrf_token:
            raise ValueError("CSRF token is missing/invalid")
        
        return {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        }
    
    @classmethod
    def fetch_jobs(cls, params: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        url = f"{cls.API_URL}dashboard-api/"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json().get('jobs', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from API: {e}")
            return []
        except ValueError as e:
            logger.error(f"Invalid data received from API: {e}")
            return []
    
    @classmethod
    def create_job(cls, request: HttpRequest, payload: Dict[str, Any]) -> bool:
        url = f"{cls.API_URL}create/"
        try:
            headers = cls._get_headers(request)
            session = cls._get_session(request)
            response = session.post(url, json=payload, headers=headers)
            return response.status_code == 201
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return False
    
    @classmethod
    def update_job(cls, request: HttpRequest, job_id: int, payload: Dict[str, Any]) -> bool:
        url = f"{cls.API_URL}update/{job_id}/"
        try:
            headers = cls._get_headers(request)
            session = cls._get_session(request)
            response = session.put(url, json=payload, headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error updating job: {e}")
            return False
    
    @classmethod
    def delete_job(cls, request: HttpRequest, job_id: int) -> bool:
        url = f"{cls.API_URL}delete/{job_id}/"
        try:
            headers = cls._get_headers(request)
            session = cls._get_session(request)
            response = session.delete(url, headers=headers)
            return response.status_code == 204
        except Exception as e:
            logger.error(f"Error deleting job: {e}")
            return False


class JobFilter:

    @staticmethod
    def filter_jobs(job_data: List[Dict[str, Any]], params: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        filtered_data = job_data
        
        if params['work_mode']:
            filtered_data = [job for job in filtered_data if job['work_mode'].lower() == params['work_mode'].lower()]
        
        if params['salary_range[]']:
            filtered_data = [job for job in filtered_data if job['salary_range'] in params['salary_range[]']]
        
        if params['location[]']:
            filtered_data = [job for job in filtered_data if job['location'].lower() in [loc.lower() for loc in params['location[]']]]
        
        return sorted(filtered_data, key=lambda x: x['created_at'], reverse=True)
    
    @staticmethod
    def get_filter_names(request: HttpRequest) -> List[str]:
        filter_names = []
        queries = {
            'search': lambda q: f"Search: {q}",
            'work-mode': lambda q: f"Work Mode: {q}",
            'salary-range[]': lambda q: f"Salary Range: {', '.join(q)}",
            'locations[]': lambda q: f"Location: {', '.join(q)}",
            'role': lambda q: f"Role: {q}",
            'experience': lambda q: f"Experience: {q} years",
            'time-range': lambda q: f"Time Range: {q} days"
        }
        
        for param, formatter in queries.items():
            print(param,formatter)
            value = request.GET.get(param) if not param.endswith('[]') else request.GET.getlist(param)
            if value:
                filter_names.append(formatter(value))
        
        return filter_names


class Profile:
   
    @staticmethod
    def get_user_profile(user) -> Optional[Union[ApplicantProfile, EmployerProfile]]:
        if user.user_type == 'APPLICANT' and hasattr(user, 'applicantprofile'):
            return user.applicantprofile
        elif user.user_type == 'EMPLOYER' and hasattr(user, 'employerprofile'):
            return user.employerprofile
        return None
    
    @staticmethod
    def check_profile_completion(profile: Optional[object]) -> bool:
        return bool(profile and profile.is_allfields_completed())


class JobApplication:

    @staticmethod
    def send_application_emails(request: HttpRequest, job: Jobs, profile: ApplicantProfile) -> bool:
        employer = job.employer
        
        subject_applicant = f"Job Application Confirmation for {job.title}"
        message_applicant = (
            f"Dear {request.user.username},\n\n"
            f"Your application for the job '{job.title}' at {employer.company_name} "
            f"has been successfully submitted.\n"
            f"Best of luck with your application!\n\n"
            f"Regards,\nCareerHub Team"
        )
        
        subject_employer = f"New Job Application for {job.title}"
        message_employer = (
            f"Dear {employer.user.username},\n\n"
            f"New application has been received for the job '{job.title}' from {request.user.username}.\n"
            f"Applicant's email: {request.user.email}\n"
            f"Profile details: {profile}\n\n"
            f"Regards,\nCareerHub Team"
        )
        
        try:
            send_mail(
                subject_applicant, 
                message_applicant, 
                settings.DEFAULT_FROM_EMAIL, 
                [request.user.email]
            )
            
            email = EmailMessage(
                subject_employer,
                message_employer,
                settings.DEFAULT_FROM_EMAIL,
                [employer.employer_email]
            )
            
            if profile.user_resume:
                resume = profile.user_resume
                mime_type, _ = mimetypes.guess_type(resume.name)
                email.attach(
                    resume.name, 
                    resume.read(), 
                    mime_type or 'application/octet-stream'
                )
            
            email.send()
            return True
        except Exception as e:
            logger.error(f"Error sending application emails: {e}")
            return False


@login_required
def home_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'job/home.html', {'title': 'Home'})


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    profile = Profile.get_user_profile(request.user)
    
    if not Profile.check_profile_completion(profile):
        profile_type = 'applicant' if request.user.user_type == 'APPLICANT' else 'employer'
        messages.warning(request, f"Please complete your {profile_type} profile details to access dashboard")
        return redirect('job-home')
    
    params: Dict[str, Union[str, List[str]]] = {
        'search': request.GET.get('search', ''),
        'work_mode': request.GET.get('work-mode', ''),
        'salary_range[]': request.GET.getlist('salary-range[]', []),
        'location[]': request.GET.getlist('locations[]', []),
        'role': request.GET.get('role', ''),
        'experience': request.GET.get('experience', ''),
        'time_range': request.GET.get('time-range', 0),
    }
    
    job_data = Job.fetch_jobs(params)
    job_data = JobFilter.filter_jobs(job_data, params)
    
    paginator = Paginator(job_data, 5)
    page_number = request.GET.get('page')
    try:
        page_data = paginator.get_page(page_number)
    except (EmptyPage, InvalidPage):
        page_data = paginator.get_page(1)
    
    context = {
        'title': 'Dashboard',
        'roles': ['Software Development', 'Software Testing', 'Devops','Machine Learning', 'Business Development'],
        'salaries': [('0-3', '0-3 Lakhs'), ('3-6', '3-6 Lakhs'), ('6-10', '6-10 Lakhs'), ('10-15', '10-15 Lakhs'),('15-20', '15-20 Lakhs'), ('20+', '20+ Lakhs')],
        'locations': ['all', 'chennai', 'bengaluru', 'coimbatore', 'madurai', 'delhi', 'hyderabad'],
        'saved_job_id': SaveJobs.objects.filter(user=request.user).values_list('job', flat=True),
        'jobs': page_data,
        'filter_names': JobFilter.get_filter_names(request),
        'start_index': (page_data.number - 1) * paginator.per_page + 1,
        'end_index': (page_data.number - 1) * paginator.per_page + len(page_data),
        'total_job': paginator.count,
    }
    
    for key in params:
        context[f"{key.replace('[]', '')}_query"] = params[key]
    
    return render(request, 'job/dashboard.html', context)


@login_required
def employer_view(request: HttpRequest) -> HttpResponse:
    if request.user.user_type == 'APPLICANT':
        return redirect('job-home')
    
    try:
        employer_profile = EmployerProfile.objects.get(user=request.user)
    except EmployerProfile.DoesNotExist:
        employer_profile = None
    
    if request.method == 'POST':
        form = EmployerProfileForm(request.POST, request.FILES, instance=employer_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employer profile details has been updated!')
            return redirect('dashboard')
    else:
        form = EmployerProfileForm(instance=employer_profile)
    
    return render(request, 'job/employer.html', {'form': form,'title': 'EmployerProfileForm'})


class CreateJobsView(LoginRequiredMixin, CreateView):
    model = Jobs
    form_class = JobForm
    template_name = 'job/create_job.html'
    context_object_name = 'form'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['title'] = 'Job Form'
        return context
    
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.user_type != 'EMPLOYER':
            messages.warning(request, "You must be an employer to create a job.")
            return redirect('job-home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form) -> HttpResponse:
        if self.request.user.user_type == 'APPLICANT':
            return redirect('job-home')
        
        try:
            employer = EmployerProfile.objects.get(user=self.request.user)
        except EmployerProfile.DoesNotExist:
            messages.warning(self.request, "You need to create an employer profile before posting jobs.")
            return redirect('job-home')
        
        job_data = form.cleaned_data
        payload = {
            'employer': employer.id,
            'title': job_data['title'],
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
            'job_skills': job_data['job_skills'],
            'company_name': employer.company_name,
            'company_logo': employer.company_logo.url if employer.company_logo else None
        }
        
        if Job.create_job(self.request, payload):
            messages.success(self.request, 'New Job has been created!')
            return redirect('dashboard')
        
        messages.error(self.request, "There was an error creating the job.")
        return redirect('dashboard')
    
    def form_invalid(self, form) -> HttpResponse:
        messages.error(self.request, "There was an error submitting the form. Please try again.")
        return super().form_invalid(form)


class UpdateJobView(LoginRequiredMixin, UpdateView):
    model = Jobs
    form_class = JobForm
    template_name = 'job/create_job.html'
    context_object_name = 'form'
    
    def get_object(self, queryset: Optional[QuerySet] = None) -> Jobs:
        try:
            return Jobs.objects.get(id=self.kwargs['id'])
        except Jobs.DoesNotExist:
            messages.error(self.request, 'Job not found')
            raise Http404('Job not found')
    
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        job_id = kwargs.get('id')
        try:
            job = Jobs.objects.get(id=job_id)
            if request.user != job.employer.user:
                messages.error(request, 'You are not allowed to update this job')
                return redirect('dashboard')
        except Jobs.DoesNotExist:
            messages.error(request, 'Job not found')
            return redirect('job-home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Job Form'
        return context
    
    def form_valid(self, form) -> HttpResponse:
        job = form.save(commit=False)
        employer = EmployerProfile.objects.get(user=self.request.user)
        
        if self.request.user != job.employer.user:
            messages.error(self.request, 'You are not allowed to update this job')
            return redirect('dashboard')
        
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
            'job_skills': job.job_skills,
            'company_name': employer.company_name,
            'company_logo': employer.company_logo.url if employer.company_logo else None
        }
        
        if Job.update_job(self.request, job.id, payload):
            messages.success(self.request, 'Job has been updated!')
            return redirect('dashboard')
        
        messages.error(self.request, 'There was an error updating job!')
        return redirect('dashboard')
    
    def form_invalid(self, form) -> HttpResponse:
        messages.error(self.request, 'There was an error with the form. Please try again.')
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
class DeleteJobView(DeleteView):
    model = Jobs
    context_object_name = 'jobs'
    success_url = reverse_lazy('dashboard')
    
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        job = self.get_object()
        if request.user != job.employer.user:
            messages.error(request, 'You are not allowed to delete this job')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        job = self.get_object()
        
        if Job.delete_job(request, job.id):
            messages.success(request, "Job deleted successfully!")
        else:
            messages.error(request, "There was an error deleting the job!")
        
        return redirect(self.success_url)


@login_required
def save_job(request: HttpRequest, id: int) -> HttpResponse:
    try:
        job = Jobs.objects.get(id=id)
    except Jobs.DoesNotExist:
        raise Http404('Job not found')
    
    is_job_saved = SaveJobs.objects.filter(user=request.user, job=job).first()
    
    if is_job_saved:
        is_job_saved.delete()
        message = 'Job removed from saved jobs'
    else:
        SaveJobs.objects.create(user=request.user, job=job)
        message = 'Job saved successfully'
    
    messages.info(request, message)
    return redirect('dashboard')


@login_required
def save_jobs(request: HttpRequest) -> HttpResponse:
    saved_jobs = SaveJobs.objects.filter(user=request.user)
    return render(request, 'job/save_jobs.html', {'saved_jobs': saved_jobs,'title': 'Saved Jobs'})


@login_required
def job_details(request: HttpRequest, id: int) -> HttpResponse:
    job = get_object_or_404(Jobs, id=id)
    http_url = request.META.get('HTTP_REFERER', 'dashboard')
    return render(request, 'job/job_details.html', {'title': 'Job Details','job': job,'http_url': http_url})


@login_required
def apply_jobs(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        messages.error(request, "You need to be logged in to apply for job")
        return redirect('job-home')
    
    job = get_object_or_404(Jobs, id=id)
    profile = get_object_or_404(ApplicantProfile, user=request.user)
    employer = job.employer
    
    if job.application_deadline <= timezone.now().date():
        messages.warning(request, f'Application deadline for this job {job.title} has passed')
        return redirect('dashboard')
    
    if JobApplications.objects.filter(applicant=request.user, job__employer=employer).exists():
        messages.warning(request, f"You have already applied for a job at {employer.company_name} company")
        return redirect('dashboard')
    
    if JobApplications.objects.filter(applicant=request.user, job=job).exists():
        messages.warning(request, "You can't apply multiple times for same specific job")
        return redirect('dashboard')
    
    JobApplications.objects.create(applicant=request.user, job=job, profile=profile)
    
    if not JobApplication.send_application_emails(request, job, profile):
        messages.error(request, "There was an error sending your application. Please try again.")
        return redirect('dashboard')
    
    messages.success(request, f"Your application for {job.title} has been submitted successfully")
    return redirect('dashboard')


@login_required
def job_applications(request: HttpRequest) -> HttpResponse:
    jobs = JobApplications.objects.all()
    return render(request, 'job/job_applications.html', {'applications': jobs})


@login_required
def update_application_skills(request: HttpRequest, id: int) -> HttpResponse:
    if request.user.user_type == 'EMPLOYER':
        return redirect('dashboard')
    
    job_application = get_object_or_404(JobApplications, id=id, applicant=request.user)
    
    if request.method == 'POST':
        form = UpdateJobApplicationForm(request.POST, instance=job_application)
        if form.is_valid():
            form.save()
            messages.success(request, "Your skills have been updated successfully")
            return redirect('job-applications')
    else:
        form = UpdateJobApplicationForm(instance=job_application)
    
    return render(request, 'job/update_application_skills.html', {'form': form,'job_application': job_application})
