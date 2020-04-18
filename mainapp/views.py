import urllib
import json

from django.contrib import messages
from django.contrib.auth import login as django_login, authenticate, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect

from .models import *
from HPCPortal import settings


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
            for req in all_requests:
                if req.is_expired() and req.renewal_status != 'Exp':
                    req.renewal_status = 'Exp'
                    req.save()
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
        # recaptcha_response = request.POST.get('g-recaptcha-response')
        # url = 'https://www.google.com/recaptcha/api/siteverify'
        # values = {
        #     'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
        #     'response': recaptcha_response
        # }
        # data = urllib.parse.urlencode(values).encode()
        # req = urllib.request.Request(url, data=data)
        # response = urllib.request.urlopen(req)
        # result = json.loads(response.read().decode())
        if user is not None and user.is_active:  # and result['success']:
            django_login(request, user)
            messages.success(request, 'با موفقیت وارد شدید')
            return redirect('index')
        elif user is None:
            messages.error(request, "ایمیل یا رمز عبور اشتباه است")
            return redirect('login')
        elif not user.is_active:
            messages.error(request, "حساب شما توسط مدیر غیرفعال شده است")
            return redirect('login')
        # elif not result['success']:
        #     messages.error(request, "reCAPTCHA failed")
        #     return redirect('login')


def register(request):
    if request.method == "GET":
        return render(request, 'mainapp/register.html')
    elif request.method == "POST":
        if request.POST['password1'] != request.POST['password2']:
            messages.error(request, "کلمه عبور و تکرار آن مطابقت ندارند")
            return render(request, 'mainapp/register.html')
        if len(request.POST['password1']) < 8:
            messages.error(request, "رمز عبور باید حداقل ۸ کاراکتر باشد")
            return render(request, 'mainapp/register.html')
        try:
            dup_email = User.objects.get(email=request.POST['email'])
        except User.DoesNotExist:
            dup_email = None
        if dup_email is not None:
            messages.error(request, "ایمیل وارد شده تکراری میباشد")
            return redirect('register')
        # recaptcha_response = request.POST.get('g-recaptcha-response')
        # url = 'https://www.google.com/recaptcha/api/siteverify'
        # values = {
        #     'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
        #     'response': recaptcha_response
        # }
        # data = urllib.parse.urlencode(values).encode()
        # req = urllib.request.Request(url, data=data)
        # response = urllib.request.urlopen(req)
        # result = json.loads(response.read().decode())
        # if not result['success']:
        #     messages.error(request, "reCAPTCHA failed")
        #     return redirect('register')
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
                                             show_cost=int(request.POST["cost"]))
        new_request.save()
        messages.success(request, "درخواست با موفقیت ارسال شد، برای پیگیری به بخش درخواست ها مراجعه کنید")
        return redirect('index')


def calc_cost(request):
    cpu = int(request.GET.get('cpu'))
    ram = int(request.GET.get('ram'))
    disk = int(request.GET.get('disk'))
    days = int(request.GET.get('days'))
    total = cpu + ram + disk + days

    data = {
        'total': total,
        'status': 200
    }
    from django.http import JsonResponse
    return JsonResponse(data)


@login_required(login_url='/login')
def edit_profile(request):
    if request.method == "GET":
        try:
            profile = Profile.objects.get(user=request.user)
            user = User.objects.get(pk=request.user.pk)
        except Profile.DoesNotExist:
            messages.error(request, "ابتدا پروفایل خود را تکمیل کنید")
            return redirect('complete_profile')
        context = {
            'profile': profile,
            'user': user,
        }
        return render(request, 'mainapp/edit_profile.html', context)
    elif request.method == "POST":
        try:
            profile = Profile.objects.get(user=request.user)
            user = User.objects.get(pk=request.user.pk)
        except Profile.DoesNotExist:
            messages.error(request, "ابتدا پروفایل خود را تکمیل کنید")
            return redirect('complete_profile')
        if request.user.email != request.POST["email"]:
            try:
                dup_email = User.objects.get(email=request.POST['email'])
            except User.DoesNotExist:
                dup_email = None
            if dup_email is not None:
                messages.error(request, "ایمیل وارد شده تکراری میباشد")
                return redirect('edit_profile')

        user.first_name = request.POST["first_name"]
        user.last_name = request.POST["last_name"]
        user.email = request.POST["email"]
        user.username = request.POST["email"]

        profile.university = request.POST["uni"]
        profile.field = request.POST["field"]
        profile.guidance_master_email = request.POST["master_email"]
        profile.guidance_master_full_name = request.POST["master_name"]
        profile.save()
        user.save()

        messages.success(request, "ویرایش با موفقیت انجام شد")
        return redirect('index')


def extend(request, pk):
    try:
        extended_service = Request.objects.get(pk=pk)
    except Request.DoesNotExist:
        raise Http404("Not found")
    if extended_service.acceptance_status != 'Acc':
        messages.error(request, "امکان ارسال درخواست تمدید برای سرویس موردنظر وجود ندارد")
        return redirect('index')
    if extended_service.renewal_status == 'Can' or extended_service.renewal_status == 'Sus':
        messages.error(request, "امکان ارسال درخواست تمدید برای سرویس موردنظر وجود ندارد")
        return redirect('index')

    if request.method == "GET":
        context = {
            'extended_service': extended_service,
        }
        return render(request, "mainapp/extend.html", context)
    elif request.method == "POST":
        ext_req = ExtendRequest.objects.create(request=extended_service, days=int(request.POST["days"]))
        ext_req.save()
        messages.success(request,
                         "درخواست تمدید با موفقیت ارسال شد. درصورت تایید، تاریخ سررسید سرویس مورد نظر به روزرسانی میشود")
        return redirect('index')


def cancel(request):
    if 'pk' in request.GET:
        pk = int(request.GET.get('pk'))
        try:
            canceled_service = Request.objects.get(pk=pk)
        except Request.DoesNotExist:
            raise Http404("Not found")
        if canceled_service.acceptance_status != 'Acc':
            messages.error(request, "امکان ارسال درخواست لغو برای سرویس موردنظر وجود ندارد")
            data = {
                'status': 201,
            }
            from django.http import JsonResponse
            return JsonResponse(data)
        if canceled_service.renewal_status == 'Can' or canceled_service.renewal_status == 'Sus':
            messages.error(request, "امکان ارسال درخواست لغو برای سرویس موردنظر وجود ندارد")
            data = {
                'status': 201,
            }
            from django.http import JsonResponse
            return JsonResponse(data)

        can_req = CancelRequest.objects.create(request=canceled_service)
        can_req.save()
        messages.success(request,
                         "درخواست لغو با موفقیت ارسال شد. درصورت تایید، وضعیت سرویس مورد نظر به روزرسانی میشود")

        data = {
            'status': 200,
        }
        from django.http import JsonResponse
        return JsonResponse(data)
