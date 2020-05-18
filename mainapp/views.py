import locale
import urllib
import json
import requests

from django.contrib import messages
from django.contrib.auth import login as django_login, authenticate, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from math import trunc
from django.contrib.auth.views import PasswordResetView as prw
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from HPCPortal import settings
from .models import *
from .forms import PasswordResetForm


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
            all_requests = profile.request_set.all().order_by('-date_requested')
            for req in all_requests:
                if req.is_expired() and req.renewal_status != 'Exp':
                    req.renewal_status = 'Exp'
                    req.date_expired = None
                    req.save()
            context = {
                'all_requests': all_requests,
            }
            return render(request, 'mainapp/index.html', context)


@login_required(login_url='/login')
def extend_requests(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, "ابتدا پروفایل خود را تکمیل کنید")
        return redirect('complete_profile')

    all_ext_reqs = ExtendRequest.objects.filter(request__user=profile).order_by("-id")
    context = {
        'all_ext_reqs': all_ext_reqs,
    }
    return render(request, 'mainapp/extend_requests.html', context)


def login(request):
    if request.method == "GET" and not request.user.is_authenticated:
        return render(request, 'mainapp/login.html')
    elif request.user.is_authenticated:
        return redirect('index')
    elif request.method == "POST":
        if request.POST['email'] != "" and request.POST['password'] != "":
            user = authenticate(request=request, username=request.POST['email'], password=request.POST['password'])
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
                # messages.success(request, 'با موفقیت وارد شدید')
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
        else:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('login')


def register(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            messages.error(request, "شما قبلا ثبت نام کرده اید")
            return redirect('index')
        else:
            return render(request, 'mainapp/register.html')
    elif request.method == "POST":
        if request.POST["first_name"] != "" and request.POST["last_name"] != "" and request.POST["email"] != "" and \
                request.POST["password1"] != "" and request.POST["password2"] != "":
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
            recaptcha_response = request.POST.get('g-recaptcha-response')
            url = 'https://www.google.com/recaptcha/api/siteverify'
            values = {
                'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                'response': recaptcha_response
            }
            data = urllib.parse.urlencode(values).encode()
            req = urllib.request.Request(url, data=data)
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode())
            if not result['success']:
                messages.error(request, "reCAPTCHA failed")
                return redirect('register')
            user = User.objects.create(username=request.POST['email'], first_name=request.POST['first_name'],
                                       last_name=request.POST['last_name'], email=request.POST['email'])
            user.set_password(request.POST['password1'])
            user.save()
            messages.success(request, 'حساب با موفقیت ایجاد شد')
            django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('complete_profile')
        else:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('register')


@login_required(login_url='/login')
def complete_profile(request):
    if request.method == "GET":
        return render(request, 'mainapp/complete_profile.html')
    elif request.method == "POST":
        if request.POST["master_name"] != "" and request.POST["email"] != "" and request.POST["uni"] != "" and \
                request.POST["field"] != "":
            profile = Profile.objects.create(user=request.user,
                                             guidance_master_full_name=request.POST["master_name"],
                                             guidance_master_email=request.POST["email"],
                                             university=request.POST["uni"], field=request.POST["field"])
            profile.save()
            messages.success(request, "پروفایل با موفقیت تکمیل شد")
            return redirect('index')
        else:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('complete_profile')


@login_required(login_url='/login')
def logout(request):
    django_logout(request)
    # messages.success(request, "با موفقیت خارج شدید")
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
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        cost = locale.atoi(request.POST["cost"])  # cost for non-chamran
        cost_disc = locale.atoi(request.POST["cost_disc"])  # cost for chamran

        if request.POST["os"] != "" and request.POST["ram"] != "" and int(request.POST["ram"]) >= 4 and int(
                request.POST["ram"]) <= 30 and request.POST["cpu"] != "" and int(request.POST["cpu"]) >= 1 and int(
            request.POST["cpu"]) <= 12 and request.POST["disk"] != "" and int(request.POST["disk"]) >= 30 and int(
            request.POST["disk"]) <= 140 and request.POST.getlist('app_name') and request.POST[
            "days"] != "" and int(request.POST["days"]) >= 15 and request.POST["cost"] != "" and int(cost) > 0 and \
                request.POST["cost_disc"] != "" and int(cost_disc) > 0:
            app_name_list = request.POST.getlist('app_name')
            app_name = ', '.join(app_name_list)

            if profile.university.__contains__("چمران") or profile.university.__contains__(
                    "chamran") or profile.university.__contains__("chamraan"):
                new_request = Request.objects.create(user=profile, os=request.POST["os"], ram=int(request.POST["ram"]),
                                                     cpu=int(request.POST["cpu"]), disk=int(request.POST["disk"]),
                                                     app_name=app_name, days=int(request.POST["days"]),
                                                     show_cost=int(cost_disc),
                                                     user_description=request.POST["user_desc"],
                                                     show_cost_for_admin_only=int(cost))
            else:
                new_request = Request.objects.create(user=profile, os=request.POST["os"], ram=int(request.POST["ram"]),
                                                     cpu=int(request.POST["cpu"]), disk=int(request.POST["disk"]),
                                                     app_name=app_name, days=int(request.POST["days"]),
                                                     show_cost=int(cost), user_description=request.POST["user_desc"],
                                                     show_cost_for_admin_only=int(cost_disc))
            new_request.save()
            # messages.success(request, "درخواست با موفقیت ارسال شد، برای پیگیری به بخش درخواست ها مراجعه کنید")
            return redirect('index')
        else:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('new_request')


def calc_cost(request):
    cpu = int(request.GET.get('cpu'))
    ram = int(request.GET.get('ram'))
    disk = int(request.GET.get('disk'))
    days = int(request.GET.get('days'))
    if cpu > 12 or ram > 30 or disk > 140 or days > 365:
        data = {
            'status': 400,
            'reason': "one or more of the inputs are out of range"
        }
        from django.http import JsonResponse
        return JsonResponse(data)

    total = ((cpu * 6600) + ((ram / 4) * 10000) + ((disk / 30) * 10000)) * (days / 30)
    total_disc = (70 * total) / 100

    total_disc = trunc(round(total_disc) / 1000) * 1000
    total_disc = f'{total_disc:,d}'

    total = trunc(round(total) / 1000) * 1000
    total = f'{total:,d}'

    data = {
        'total': total,
        'total_disc': total_disc,
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
        user = User.objects.get(pk=request.user.pk)
        try:
            profile = Profile.objects.get(user=request.user)
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
        if request.POST["first_name"] != "" and request.POST["last_name"] != "" and request.POST["email"] != "" and \
                request.POST["uni"] != "" and request.POST["field"] != "" and request.POST["master_email"] != "" and \
                request.POST["master_name"] != "":
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
        else:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('edit_profile')


@login_required(login_url='/login')
def extend(request, sn):
    extended_service = get_object_or_404(Request, serial_number=sn)
    if extended_service.acceptance_status != 'Acc':
        messages.error(request, "امکان ارسال درخواست تمدید برای سرویس موردنظر وجود ندارد")
        return redirect('index')
    if extended_service.renewal_status in ['Can', 'Sus']:
        messages.error(request, "امکان ارسال درخواست تمدید برای سرویس موردنظر وجود ندارد")
        return redirect('index')

    if request.method == "GET":
        context = {
            'extended_service': extended_service,
        }
        return render(request, "mainapp/extend.html", context)
    elif request.method == "POST":
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            messages.error(request, "ابتدا پروفایل خود را تکمیل کنید")
            return redirect('complete_profile')
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        cost = locale.atoi(request.POST["cost"])  # cost for non-chamran
        cost_disc = locale.atoi(request.POST["cost_disc"])  # cost for chamran
        if request.POST["days"] != "" and int(request.POST["days"]) >= 15 and request.POST["cost"] != "" and \
                int(cost) > 0 and request.POST["cost_disc"] != "" and int(cost_disc) > 0:
            # and "receipt" in request.FILES:
            # receipt = request.FILES["receipt"]
            # fs = FileSystemStorage()
            # filename = fs.save(receipt.name, receipt)
            if profile.university.__contains__("چمران") or profile.university.__contains__(
                    "chamran") or profile.university.__contains__("chamraan"):
                ext_req = ExtendRequest.objects.create(request=extended_service, days=int(request.POST["days"]),
                                                       show_cost=int(cost_disc))
            else:
                ext_req = ExtendRequest.objects.create(request=extended_service, days=int(request.POST["days"]),
                                                       show_cost=int(cost))
            ext_req.save()
            # pay = Payment.objects.create(request=extended_service, extend=ext_req, receipt=filename,
            #                              cost=int(ext_req.show_cost))
            # pay.save()
            extended_service.acceptance_status = 'Exting'
            extended_service.save()
            # messages.success(request,
            #                  "درخواست تمدید با موفقیت ارسال شد. برای پیگیری وضعیت، به بخش درخواست‌های تمدید مراجعه کنید")
            return redirect('index')
        else:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('extend')


def cancel(request):
    if 'pk' in request.GET:
        pk = int(request.GET.get('pk'))
        canceled_service = get_object_or_404(Request, pk=pk)
        if canceled_service.acceptance_status != 'Acc':
            messages.error(request, "امکان ارسال درخواست لغو برای سرویس موردنظر وجود ندارد")
            data = {
                'status': 201,
            }
            from django.http import JsonResponse
            return JsonResponse(data)
        if canceled_service.renewal_status in ['Can', 'Sus']:
            messages.error(request, "امکان ارسال درخواست لغو برای سرویس موردنظر وجود ندارد")
            data = {
                'status': 201,
            }
            from django.http import JsonResponse
            return JsonResponse(data)

        can_req = CancelRequest.objects.create(request=canceled_service)
        can_req.save()
        canceled_service.acceptance_status = 'Caning'
        canceled_service.save()
        # messages.success(request,
        #                  "درخواست لغو با موفقیت ارسال شد. درصورت تایید، وضعیت سرویس مورد نظر به روزرسانی میشود")

        data = {
            'status': 200,
        }
        from django.http import JsonResponse
        return JsonResponse(data)


@login_required(login_url='/login')
def pay(request, sn):
    found_request = get_object_or_404(Request, serial_number=sn)
    try:
        Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, "ابتدا پروفایل خود را تکمیل کنید")
        return redirect('complete_profile')
    if request.method == "GET":
        context = {
            'req': found_request,
        }
        return render(request, 'mainapp/payment.html', context)

    elif request.method == "POST":

        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        cost = locale.atoi(request.POST["cost"])

        if "receipt" in request.FILES and int(cost) == found_request.show_cost:
            receipt = request.FILES["receipt"]
            fs = FileSystemStorage()
            filename = fs.save(receipt.name, receipt)
            desc = request.POST["desc"]

            payment = Payment.objects.create(receipt=filename, cost=int(cost), description=desc, request=found_request)
            payment.save()
            found_request.acceptance_status = "AccPaying"
            found_request.save()
            # messages.success(request, "پرداخت با موفقیت ارسال شد و پس از تایید مدیر اعمال خواهد شد")
            return redirect('index')
        else:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('pay', sn=sn)


@login_required(login_url='/login')
def pay_extend(request, sn):
    found_extend = get_object_or_404(ExtendRequest, serial_number=sn)
    try:
        Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, "ابتدا پروفایل خود را تکمیل کنید")
        return redirect('complete_profile')
    if request.method == "GET":
        context = {
            'ext': found_extend,
        }
        return render(request, 'mainapp/payment_extend.html', context)

    elif request.method == "POST":

        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        cost = locale.atoi(request.POST["cost"])

        if "receipt" in request.FILES and int(cost) == found_extend.show_cost:
            receipt = request.FILES["receipt"]
            fs = FileSystemStorage()
            filename = fs.save(receipt.name, receipt)
            desc = request.POST["desc"]

            payment = Payment.objects.create(receipt=filename, cost=int(cost), description=desc, extend=found_extend,
                                             request=found_extend.request)
            payment.save()
            found_extend.acceptance_status = "AccPaying"
            found_extend.save()
            # messages.success(request, "پرداخت با موفقیت ارسال شد و پس از تایید مدیر اعمال خواهد شد")
            return redirect('extend_requests')
        else:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('pay_online', sn=sn)


@login_required(login_url='/login')
def pay_online(request):
    raise Http404
    """
    pk = int(request.POST.get('id'))
    try:
        found_req = Request.objects.get(pk=pk)
    except Request.DoesNotExist:
        raise Http404("request not found")

    url = "https://api.idpay.ir/v1.1/payment"
    headers = {
        "X-API-KEY": "foo/bar",
        "X-SANDBOX": "1",
        "Content-Type": "application/json",
    }
    params = {
        "order_id": found_req.serial_number,
        "name": request.user.profile.get_user_full_name,
        "mail": request.user.email,
        "desc": request.POST.get("desc"),
        "amount": int(found_req.show_cost) * 10,
        "callback": "http://127.0.0.1:8000/callback/",
    }
    result = requests.post(url, data=json.dumps(params), headers=headers)
    result = json.loads(result.text)
    return redirect(result["link"])
    """


# @csrf_exempt
def callback(request):
    raise Http404
    """
    if request.method == "POST":
        from django.http import HttpResponse
        return HttpResponse(request.POST.get("track_id"))
        """


class PasswordResetView(prw):
    form_class = PasswordResetForm
