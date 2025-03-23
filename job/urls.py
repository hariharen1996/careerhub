from django.urls import path
from . import views 
from . import apiviews

urlpatterns = [
    path('',views.home_view,name='job-home'),
    path('dashboard/',views.dashboard_view,name='dashboard'),
    path('employer/',views.employer_view,name='employer'),
    path('create-job/',views.CreateJobsView.as_view(),name='create-job'),
    path('update-job/<int:id>/',views.UpdateJobView.as_view(),name='update-job'),
    path('delete-job/<int:pk>/',views.DeleteJobView.as_view(),name='delete-job'),
    path('save-job/<int:id>/',views.save_job,name='save-job'),
    path('save-jobs/',views.save_jobs,name='save-jobs'),
    path('job-details/<int:id>/',views.job_details,name='job-details'),
    path('apply-jobs/<int:id>/',views.apply_jobs,name='apply-jobs'),
    path('job-applications/',views.job_applications,name='job-applications'),
    path('update-application-skills/<int:id>/',views.update_application_skills,name='update-application-skills'),

    path('api/dashboard-api/',apiviews.DashboardApiView.as_view(),name='dashboard-api'),
    path('api/create/', apiviews.CreateJobView.as_view(), name='create-job-api'),
    path('api/update/<int:id>/', apiviews.UpdateJobView.as_view(), name='update-job-api'),
    path('api/delete/<int:id>/', apiviews.DeleteJobView.as_view(), name='delete-job-api'),
   
]
