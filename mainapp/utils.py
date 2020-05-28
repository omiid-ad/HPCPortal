import datetime
from math import trunc

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from HPCPortal import settings


def calc_cost(cpu, ram, disk, days):
    if cpu > 16 or ram > 30 or disk > 140 or days > 365:
        data = {
            'status': 400,
            'reason': "one or more of the inputs are out of range"
        }
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
    my = MyPayment.objects.create(django_pardakht=payment)
    if my.django_pardakht.successful():
        req = Request.objects.get(serial_number=payment.description)
        my.request = req
        req.acceptance_status = "Acc"
        from django.utils import timezone
        import datetime
        req.date_expired = timezone.now() + datetime.timedelta(days=req.days)
        req.save()
        payment.save()
        my.save()


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
        'date': datetime.date.today().strftime("%Y/%m/%d"),
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
        'date': datetime.date.today().strftime("%Y/%m/%d"),
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
