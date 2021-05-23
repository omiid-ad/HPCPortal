import datetime
import kronos
import glob
import os

from HPCPortal import settings
from mainapp.utils import send_before_expire_email, send_generic_email, send_expire_notify_to_admins
from .models import Request, ExtendRequest


@kronos.register('5 0 * * *')  # must occur before any changes, because we need date_expire of requests
def notify_admins_how_many_requests_expire_today():
    expire_list = list()
    for _ in Request.objects.all():
        if _.gonna_expire_today():
            expire_list.append(_)
    if len(expire_list) > 0:
        send_expire_notify_to_admins(expire_list, email_template="mainapp/notify_admins_expire_requests_email.html")


@kronos.register('10 0 * * *')
def remember_email_to_extend_expire_requests():
    for _ in Request.objects.filter(acceptance_status="Acc", renewal_status="Ok"):
        if _.is_request_n_days_to_expire(3):
            send_before_expire_email(_.user.user, _)


@kronos.register('15 0 * * *')
def expire_outdated_requests():
    for _ in Request.objects.all():
        if _.is_expired():
            _.renewal_status = 'Exp'
            _.date_expired = None
            _.save()
            send_generic_email(_.user.user, _, "انقضای سرویس", email_template="mainapp/request_expired_email.html")


@kronos.register('30 0 * * *')  # every day at 00:30 AM
def remove_generated_factors():
    files = glob.glob(settings.MEDIA_ROOT + '/factors/' + '*.pdf')
    for f in files:
        os.remove(f)

# @kronos.register('55 23 * * *')
# def reject_requests_not_payed_by_3_days():
#     req_list = Request.objects.filter(acceptance_status="Paying")
#     for _ in req_list:
#         days_between_requested = _.date_requested - datetime.date.today()
#         days = abs(days_between_requested.days)
#         if days >= 3:
#             _.acceptance_status = "Rej"
#             _.date_expired = None
#             _.description += "| درخواست شما بدلیل عدم پرداخت هزینه سرویس در مدت معین، رد شد"
#             _.save()
#
#
# @kronos.register('52 23 * * *')
# def reject_extends_not_payed_by_3_days():
#     ext_list = ExtendRequest.objects.filter(acceptance_status="Paying")
#     for _ in ext_list:
#         days_between_requested = _.date_requested - datetime.date.today()
#         days = abs(days_between_requested.days)
#         if days >= 3:
#             _.acceptance_status = "Rej"
#             _.request.acceptance_status = "Rej"
#             _.request.description += "| تمدید شما بدلیل عدم پرداخت هزینه در مدت معین، رد شد"
#             _.save()
#             _.request.save()
