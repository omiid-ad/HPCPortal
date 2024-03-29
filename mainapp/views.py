import locale
import urllib
import json
import requests

from django.contrib import messages
from django.contrib.auth import login as django_login, authenticate, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.password_validation import validate_password
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.html import strip_tags
from django.views.generic import FormView, RedirectView

from HPCPortal import settings
from .models import *
from . import utils
from .forms import FactorForm


class GetFactorView(LoginRequiredMixin, FormView):
    form_class = FactorForm
    template_name = 'mainapp/get_factor.html'
    success_url = reverse_lazy('factor')

    def get_form_kwargs(self):
        kwargs = super(GetFactorView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        file_path = form.generate_pdf()
        return redirect('/' + file_path)


class ExtendRequestRedirectView(RedirectView):
    url = reverse_lazy('index', kwargs=None)


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
            # for req in all_requests:
            #     if req.is_expired() and req.renewal_status != 'Exp':
            #         req.renewal_status = 'Exp'
            #         req.date_expired = None
            #         req.save()
            extend_req_notif = False
            for req in profile.request_set.all():
                for ext in req.extendrequest_set.all():
                    if ext.acceptance_status == 'Paying':
                        extend_req_notif = True

            context = {
                'all_requests': all_requests,
                'extend_req_notif': extend_req_notif,
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
            try:
                validate_password(request.POST['password1'])
            except ValidationError as val_err:
                for err_msg in val_err.messages:
                    messages.error(request, err_msg)
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
            subject = 'حساب کاربری شما ایجاد شد'
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
            protocol = request.scheme
            context = {
                'site_name': site_name,
                'domain': domain,
                'protocol': protocol,
                'name': user.get_full_name(),
            }
            html_message = render_to_string('mainapp/register_confirm_email.html', context)
            plain_message = strip_tags(html_message)
            to = request.POST['email']
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [to],
                html_message=html_message,
                fail_silently=True
            )
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
        try:
            real_cost = locale.atoi(request.POST["cost"])  # real cost
            final_cost = locale.atoi(request.POST["cost_disc"])  # final cost
        except ValueError:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('new_request')

        res = utils.calc_cost(request.POST.get("os"), int(request.POST["cpu"]), int(request.POST["ram"]),
                              int(request.POST["disk"]),
                              int(request.POST["days"]))
        res = json.loads(res.content)
        if res["status"] == 400:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('new_request')
        if res["status"] == 200:
            if real_cost != locale.atoi(res["total_real_cost"]) or final_cost != locale.atoi(res["total_final_cost"]):
                messages.error(request, "فرم را به درستی پر کنید")
                return redirect('new_request')

        rm = ResourceLimit.objects.get(os__exact=request.POST.get("os"))
        if int(request.POST["cpu"]) > int(rm.cpu_max) or int(request.POST["cpu"]) < int(rm.cpu_min) or int(
                request.POST["ram"]) > int(rm.ram_max) or int(request.POST["ram"]) < int(rm.ram_min) or int(
            request.POST["disk"]) > int(rm.disk_max) or int(request.POST["disk"]) < int(rm.disk_min) or int(
            request.POST["days"]) > int(rm.days_max) or int(request.POST["days"]) < int(rm.days_min):
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('new_request')

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
            return redirect('new_request')

        if request.POST["os"] != "" and request.POST["ram"] != "" and request.POST["cpu"] != "" and request.POST[
            "disk"] != "" and request.POST.getlist('app_name') and request.POST[
            "days"] != "" and request.POST["cost"] != "" and int(real_cost) >= 5000 and request.POST[
            "cost_disc"] != "" and int(
            final_cost) >= 1000:

            app_name_list = request.POST.getlist('app_name')
            app_name = ', '.join(app_name_list)

            new_request = Request.objects.create(user=profile, os=request.POST["os"], ram=int(request.POST["ram"]),
                                                 cpu=int(request.POST["cpu"]), disk=int(request.POST["disk"]),
                                                 app_name=app_name, days=int(request.POST["days"]),
                                                 show_cost=int(final_cost), user_description=request.POST["user_desc"],
                                                 show_cost_for_admin_only=int(real_cost))

            new_request.save()
            utils.send_mail_to_admins("درخواست جدید", new_request.user.user, new_request,
                                      "mainapp/new_request_email.html")
            # messages.success(request, "درخواست با موفقیت ارسال شد، برای پیگیری به بخش درخواست ها مراجعه کنید")
            return redirect('index')
        else:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('new_request')


def calc_cost(request):
    os = request.GET.get('os')
    cpu = int(request.GET.get('cpu'))
    ram = int(request.GET.get('ram'))
    disk = int(request.GET.get('disk'))
    days = int(request.GET.get('days'))

    res = utils.calc_cost(os, cpu, ram, disk, days)
    return res


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
    try:
        extended_service = request.user.profile.request_set.get(serial_number=sn)
    except Request.DoesNotExist:
        raise Http404
    rm = get_object_or_404(ResourceLimit, os__exact=extended_service.os)
    if extended_service.acceptance_status != 'Acc':
        messages.error(request, "امکان ارسال درخواست تمدید برای سرویس موردنظر وجود ندارد")
        return redirect('index')
    if extended_service.renewal_status in ['Can', 'Sus']:
        messages.error(request, "امکان ارسال درخواست تمدید برای سرویس موردنظر وجود ندارد")
        return redirect('index')

    if request.method == "GET":
        context = {
            'extended_service': extended_service,
            'rm': rm,
        }
        return render(request, "mainapp/extend.html", context)
    elif request.method == "POST":
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            messages.error(request, "ابتدا پروفایل خود را تکمیل کنید")
            return redirect('complete_profile')
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        try:
            real_cost = locale.atoi(request.POST["cost"])
            final_cost = locale.atoi(request.POST["cost_disc"])
        except ValueError:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('extend', sn=extended_service.serial_number)
        rm = ResourceLimit.objects.get(os__exact=extended_service.os)
        if request.POST["days"] != "" and int(rm.days_min) <= int(request.POST["days"]) <= int(rm.days_max) and \
                request.POST["cost"] != "" and \
                int(real_cost) >= 1000 and request.POST["cost_disc"] != "" and int(final_cost) >= 1000:

            ext_req = ExtendRequest.objects.create(request=extended_service, days=int(request.POST["days"]),
                                                   show_cost=int(final_cost))
            ext_req.save()
            extended_service.acceptance_status = 'Exting'
            extended_service.save()
            utils.send_mail_to_admins("تمدید جدید", ext_req.request.user.user, ext_req,
                                      "mainapp/new_extend_email.html")
            # messages.success(request,
            #                  "درخواست تمدید با موفقیت ارسال شد. برای پیگیری وضعیت، به بخش درخواست‌های تمدید مراجعه کنید")
            return redirect('extend_requests')
        else:
            messages.error(request, "فرم را به درستی پر کنید")
            return redirect('extend', sn=extended_service.serial_number)


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
    try:
        found_request = request.user.profile.request_set.get(serial_number=sn)
    except Request.DoesNotExist:
        raise Http404
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
            extension = receipt.name.split(".")
            extension = extension[1]
            if not utils.file_extension_validator(extension):
                messages.error(request, "فایل ارسالی مجاز نمی‌باشد")
                return redirect('pay', sn=sn)
            fs = FileSystemStorage()
            receipt.name = found_request.serial_number + "(" + datetime.date.today().strftime(
                "%Y-%m-%d") + ")" + "." + extension
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
    if found_extend.request.user.user != request.user:
        raise Http404
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
            extension = receipt.name.split(".")
            extension = extension[1]
            if not utils.file_extension_validator(extension):
                messages.error(request, "فایل ارسالی مجاز نمی‌باشد")
                return redirect('pay', sn=sn)

            fs = FileSystemStorage()
            receipt.name = found_extend.serial_number + "(" + datetime.date.today().strftime(
                "%Y-%m-%d") + ")" + "." + extension
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
    from pardakht import handler
    try:
        service = Request.objects.get(pk=int(request.POST.get('id')))
    except Request.DoesNotExist:
        raise Http404("service does not found")
    description = service.serial_number
    price = int(request.POST.get("cost"))
    if price != service.show_cost:
        messages.error(request, "خطایی رخ داد، دوباره امتحان کنید")
        return redirect('pay', sn=service.serial_number)
    result = handler.create_payment(
        price,
        description,
        utils.call_back,
        reverse('index'),
        login_required=True
    )
    return redirect(result['link'])


@login_required(login_url='/login')
def pay_online_extend(request):
    from pardakht import handler
    try:
        extended_service = ExtendRequest.objects.get(pk=int(request.POST.get('id')))
    except ExtendRequest.DoesNotExist:
        raise Http404("extend service does not found")
    description = extended_service.serial_number
    price = int(request.POST.get("cost"))
    if price != extended_service.show_cost:
        messages.error(request, "خطایی رخ داد، دوباره امتحان کنید")
        return redirect('pay_extend', sn=extended_service.serial_number)
    result = handler.create_payment(
        price,
        description,
        utils.call_back_extend,
        reverse('index'),
        login_required=True
    )
    return redirect(result['link'])


def get_limits_based_on_os(request):
    if request.method == "GET":
        rm = ResourceLimit.objects.get(os__exact=request.GET.get("os"))
        from django.core import serializers
        rm_json = serializers.serialize('json', [rm, ])
        from django.http import JsonResponse
        return JsonResponse(rm_json, safe=False)


@login_required(login_url='/login')
def software_list(request):
    softwares_win = Software.objects.filter(is_active=True, os='Win')
    softwares_lin = Software.objects.filter(is_active=True, os='Lin')
    obj_count = softwares_lin.count() + softwares_win.count()

    context = {
        'softwares_win': softwares_win,
        'softwares_lin': softwares_lin,
        'obj_count': obj_count,
    }

    return render(request, 'mainapp/softwares.html', context)
