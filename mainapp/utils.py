from math import trunc

import datetime
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from HPCPortal import settings

from .calendar import jalali
from django.utils import timezone


def persian_numbers_converter(mystr):
    numbers = {
        "0": "۰",
        "1": "۱",
        "2": "۲",
        "3": "۳",
        "4": "۴",
        "5": "۵",
        "6": "۶",
        "7": "۷",
        "8": "۸",
        "9": "۹",
    }

    for e, p in numbers.items():
        mystr = mystr.replace(e, p)

    return mystr


def jalali_converter(time):
    jmonths = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند", ]

    time = timezone.localtime(time)

    time_to_str = "{},{},{}".format(time.year, time.month, time.day)
    time_to_tuple = jalali.Gregorian(time_to_str).persian_tuple()

    time_to_list = list(time_to_tuple)

    for index, month in enumerate(jmonths):
        if time_to_list[1] == index + 1:
            time_to_list[1] = month
            break

    output = "{} {} {}، ساعت {}:{}".format(
        time_to_list[2],
        time_to_list[1],
        time_to_list[0],
        time.hour,
        time.minute,
    )

    return persian_numbers_converter(output)


def calc_cost(os, cpu, ram, disk, days):
    from .models import ResourceLimit
    rm = ResourceLimit.objects.get(os__exact=os)
    if int(rm.cpu_min) <= cpu <= int(rm.cpu_max) and int(rm.ram_min) <= ram <= int(rm.ram_max) and int(
            rm.disk_min) <= disk <= int(rm.disk_max) and int(rm.days_min) <= days <= int(rm.days_max):
        if cpu < 8:
            cpu_price = 400
        else:
            cpu_price = 800
        if ram < 16:
            ram_price = 300
        elif 16 <= ram < 32:
            ram_price = 350
        else:
            ram_price = 400
        if disk < 30:
            disk_price = 65
        elif 30 <= disk < 70:
            disk_price = 80
        else:
            disk_price = 95

        total = ((cpu * cpu_price) + (ram * ram_price) + (disk * disk_price)) * (days / 30)
        total_disc = (75 * total) / 100

        total_disc = trunc(round(total_disc) / 1000) * 1000
        total_disc = f'{total_disc:,d}'

        total = trunc(round(total) / 1000) * 1000
        total = f'{total:,d}'

        data = {
            'total': total,
            'total_disc': total_disc,
            'status': 200
        }
        return JsonResponse(data)
    else:
        data = {
            'status': 400,
            'reason': "one or more of the inputs are out of range"
        }
        return JsonResponse(data)


def is_unique(sn):
    from .models import Request, ExtendRequest
    if Request.objects.filter(serial_number=sn).count() != 0:
        return False
    if ExtendRequest.objects.filter(serial_number=sn).count() != 0:
        return False
    return True


def call_back(payment):
    from .models import Request, MyPayment
    from django.utils import timezone
    my = MyPayment.objects.create(django_pardakht=payment)
    my.save()
    if my.django_pardakht.successful():
        try:
            req = Request.objects.get(serial_number=payment.description)
        except Request.DoesNotExist:
            from django.http import Http404
            raise Http404("service not found")
        my.request = req
        req.acceptance_status = "Acc"
        req.date_expired = timezone.now() + datetime.timedelta(days=req.days)
        req.save()
        payment.save()
        my.save()
        send_mail_to_admins("پرداخت جدید", payment.user, req, "mainapp/new_req_payment_email.html")


def call_back_extend(payment):
    from django.utils import timezone
    from .models import ExtendRequest, MyPayment
    my = MyPayment.objects.create(django_pardakht=payment)
    my.save()
    if my.django_pardakht.successful():
        try:
            ext = ExtendRequest.objects.get(serial_number=payment.description)
        except ExtendRequest.DoesNotExist:
            from django.http import Http404
            raise Http404("extend service not found")
        my.request = ext.request
        my.extend = ext
        ext.request.renewal_status = 'Ok'
        ext.request.acceptance_status = 'Acc'
        ext.acceptance_status = 'Acc'
        if ext.request.date_expired is not None:
            ext.request.date_expired = ext.request.date_expired + datetime.timedelta(days=ext.days)
        else:
            ext.request.date_expired = timezone.now() + datetime.timedelta(days=ext.days)
        ext.request.save()
        ext.save()
        payment.save()
        my.save()
        send_mail_to_admins("پرداخت جدید", payment.user, ext, "mainapp/new_ext_payment_email.html")


def send_update_status_email(request, user, email_template="mainapp/update_status_email.html"):
    current_site = get_current_site(request)
    site_name = current_site.name
    domain = current_site.domain
    protocol = request.scheme
    context = {
        'site_name': site_name,
        'domain': domain,
        'protocol': protocol,
        'name': user.get_full_name(),
        'date': datetime.date.today(),
        'time': datetime.datetime.now().strftime("%H:%M"),
    }
    html_message = render_to_string(email_template, context)
    plain_message = strip_tags(html_message)
    send_mail(
        "تغییر وضعیت سرویس",
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=True
    )


def send_before_expire_email(user, user_request, email_template="mainapp/before_expire_email.html"):
    context = {
        'name': user.get_full_name(),
        'user_request': user_request,
    }
    html_message = render_to_string(email_template, context)
    plain_message = strip_tags(html_message)
    send_mail(
        "یادآوری برای تمدید سرویس",
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=True
    )


def file_extension_validator(ext):
    valid_exts = ["jpeg", "jpg", "png", "bmp", "pdf", "rar", "zip"]
    if ext.upper() in (name.upper() for name in valid_exts):
        return True
    return False


def send_extend_date_email(user, user_request, email_template="mainapp/extend_date_email.html"):
    context = {
        'name': user.get_full_name(),
        'user_request': user_request,
        'date': datetime.date.today(),
        'time': datetime.datetime.now().strftime("%H:%M"),
    }
    html_message = render_to_string(email_template, context)
    plain_message = strip_tags(html_message)
    send_mail(
        "تمدید سرویس",
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=True
    )


def send_generic_email(user, user_request, subject, email_template):
    context = {
        'name': user.get_full_name(),
        'user_request': user_request,
        'date': datetime.date.today(),
        'time': datetime.datetime.now().strftime("%H:%M"),
    }
    html_message = render_to_string(email_template, context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=True
    )


def send_expire_notify_to_admins(expire_list, email_template):
    from .models import User
    admins = User.objects.filter(is_staff=True, is_superuser=True, is_active=True)
    email_list = list()
    for i in admins:
        if i.email:
            email_list.append(i.email)
    context = {
        'expire_list': expire_list,
        'date': datetime.date.today(),
    }
    html_message = render_to_string(email_template, context)
    plain_message = strip_tags(html_message)
    for email in email_list:
        send_mail(
            "یادآوری انقضای درخواست ها",
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message,
            fail_silently=True
        )


def send_mail_to_admins(subj, user, obj, email_template):
    from .models import User
    admins = User.objects.filter(is_staff=True, is_superuser=True, is_active=True)
    email_list = list()
    for i in admins:
        if i.email:
            email_list.append(i.email)
    context = {
        'user': user,
        'obj': obj,
        'date': datetime.date.today(),
        'time': datetime.datetime.now().strftime("%H:%M"),
    }
    html_message = render_to_string(email_template, context)
    plain_message = strip_tags(html_message)
    for email in email_list:
        send_mail(
            subj,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message,
            fail_silently=True
        )
