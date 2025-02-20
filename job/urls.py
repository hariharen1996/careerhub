from django.urls import path
from . import views 

urlpatterns = [
    path('',views.home_view,name='job-home'),
    path('dashboard/',views.dashboard_view,name='dashboard'),
    path('employer/',views.employer_view,name='employer'),
    path('create-job/',views.create_jobs_view,name='create-job'),
    path('update-job/<int:id>/',views.update_job_view,name='update-job'),
    path('delete-job/<int:id>/',views.delete_job_view,name='delete-job'),
]
