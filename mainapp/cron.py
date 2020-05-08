import datetime

import kronos

from .models import Request


@kronos.register('58 23 * * *')
def expire_outdated_requests():
    for _ in Request.objects.all():
        if _.is_expired():
            _.renewal_status = 'Exp'
            _.date_expired = None
            _.save()


@kronos.register('55 23 * * *')
def reject_requests_not_response_by_3_days():
    req_list = Request.objects.filter(acceptance_status="Paying")
    for _ in req_list:
        days_between_requested = _.date_requested - datetime.date.today()
        days = abs(days_between_requested.days)
        if days >= 3:
            _.acceptance_status = "Rej"
            _.description = "درخواست شما بدلیل عدم پرداخت هزینه سرویس در مدت معین، رد شد"
            _.save()
