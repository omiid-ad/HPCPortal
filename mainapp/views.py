from django.contrib import messages
from django.contrib.auth import login as django_login
from django.shortcuts import render, redirect

from .models import *


def index(request):
    if not request.user.is_authenticated:
        redirect('login')
    return render(request, 'mainapp/index.html')


def login(request):
    return render(request, 'mainapp/login.html')


def register(request):
    if request.method == "GET":
        return render(request, 'mainapp/register.html')
    elif request.method == "POST":
        if request.POST['password1'] != request.POST['password2']:
            messages.error(request, "کلمه عبور و تکرار آن مطابقت ندارند")
            return render(request, 'mainapp/register.html')
        user = User.objects.create(username=request.POST['email'], first_name=request.POST['first_name'],
                                   last_name=request.POST['last_name'], email=request.POST['email'])
        user.set_password(request.POST['password1'])
        user.save()
        messages.success(request, 'حساب با موفقیت ایجاد شد')
        django_login(request, user)
        return redirect('complete_profile')


def complete_profile(request):
    if request.method == "GET":
        return render(request, 'mainapp/complete_profile.html')
    elif request.method == "POST":
        profile = Profile.objects.create(user=request.user, guidance_master_full_name=request.POST["master_name"],
                                         guidance_master_email=request.POST["email"],
                                         university=request.POST["uni"], field=request.POST["field"])
        profile.save()
        messages.success(request, "پروفایل با موفقیت تکمیل شد")
        return redirect('index')
