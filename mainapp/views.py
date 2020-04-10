from django.contrib import messages
from django.contrib.auth import login as django_login, authenticate, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import *


def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            messages.error(request, "ابتدا پروفایل خود را تکمیل کنید")
            return redirect('complete_profile')
        else:
            all_requests = Request.objects.filter(user=profile).order_by('-date_requested')
            context = {
                'all_requests': all_requests,
            }
            return render(request, 'mainapp/index.html', context)


def login(request):
    if request.method == "GET" and not request.user.is_authenticated:
        return render(request, 'mainapp/login.html')
    elif request.user.is_authenticated:
        return redirect('index')
    elif request.method == "POST":
        user = authenticate(username=request.POST['email'], password=request.POST['password'])
        if user is not None:
            django_login(request, user)
            messages.success(request, 'با موفقیت وارد شدید')
            return redirect('index')
        else:
            messages.error(request, "ایمیل یا رمز عبور اشتباه است")
            return redirect('login')


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


@login_required(login_url='/login')
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


@login_required(login_url='/login')
def logout(request):
    django_logout(request)
    messages.success(request, "با موفقیت خارج شدید")
    return redirect('index')


@login_required(login_url='/login')
def new_request(request):
    if request.method == "GET":
        return render(request, 'mainapp/new_request.html')
    elif request.method == "POST":
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            messages.error(request, "ابتدا پروفایل خود را تکمیل کنید")
            return redirect('complete_profile')
        new_request = Request.objects.create(user=profile, os=request.POST["os"], ram=int(request.POST["ram"]),
                                             cpu=int(request.POST["cpu"]), disk=int(request.POST["disk"]),
                                             app_name=request.POST["app_name"], days=int(request.POST["days"]),
                                             show_cost=int(request.POST["cost"]),
                                             description=request.POST["description"])
        new_request.save()
        messages.success(request, "درخواست با موفقیت ارسال شد، برای پیگیری به بخش درخواست ها مراجعه کنید")
        return redirect('index')


def calc_cost(request):
    cpu = int(request.GET.get('cpu'))
    ram = int(request.GET.get('ram'))
    disk = int(request.GET.get('disk'))
    days = int(request.GET.get('days'))
    total = cpu + ram + disk + days
    expire_date = timezone.now() + datetime.timedelta(days=days)
    data = {
        'expire_date': expire_date,
        'total': total,
        'status': 200
    }
    from django.http import JsonResponse
    return JsonResponse(data)
