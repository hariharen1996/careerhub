from django.shortcuts import render,HttpResponse

# Create your views here.
def register_view(request):
    return HttpResponse("<h1>Register</h1>")