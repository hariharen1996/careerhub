from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Jobs 
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .serializer import JobSerializer 
from django.core.paginator import Paginator

@api_view(['GET'])
def dashboard_api_view(request):
    search_query = request.GET.get('search','')
    work_mode_query = request.GET.get('work-mode','')
    salary_query = request.GET.getlist('salary-range[]',[])
    location_query = request.GET.getlist('locations[]',[])
    role_query = request.GET.get('role','')
    experience_query = request.GET.get('experience','')
    time_range_query = request.GET.get('time-range',0)
    current_time = timezone.now()
    page_number = request.GET.get('page',None)


    jobs = Jobs.objects.all()

    if search_query:
        jobs = Jobs.objects.filter(
            Q(title__icontains=search_query) | 
            Q(location__icontains=search_query) | 
            Q(job_skills__icontains=search_query)
        ).distinct()

    if work_mode_query:
        jobs = jobs.filter(work_mode=work_mode_query)

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
            jobs = jobs.filter(salary)
    
    if location_query:
        location_filter = Q()

        if 'all' not in location_filter:
            for loc in location_query:
                location_filter |= Q(location__icontains=loc)
        jobs = jobs.filter(location_filter)

    if role_query:
        jobs = jobs.filter(role__icontains=role_query)

    if experience_query:
        experience = int(experience_query)
        if experience <= 1:
            jobs = jobs.filter(experience='0-1')
        elif experience <= 3:
            jobs = jobs.filter(experience='1-3')
        elif experience <= 5:
            jobs = jobs.filter(experience='3-5')
        elif experience <= 7:
            jobs = jobs.filter(experience='5-7')
        elif experience <= 10:
            jobs = jobs.filter(experience='7-10')
        else:
            jobs = jobs.filter(experience='10+')
    
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
            
            jobs = jobs.filter(posted_time__gte=time_limit)
        except ValueError:
            pass


    paginator = Paginator(jobs,5)
    page_data = paginator.get_page(page_number)        
    serializer = JobSerializer(page_data,many=True)
    return Response({
        'jobs': serializer.data,
        'start_index': page_data.start_index(),
        'end_index': page_data.end_index(),
        'page_number': page_number,
        'total_pages': paginator.num_pages,
    })

