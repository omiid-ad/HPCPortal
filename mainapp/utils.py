from math import trunc
from django.http import JsonResponse


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
    from .models import Request, OnlinePaymentProxy
    op = OnlinePaymentProxy.objects.create(payment_ptr=payment)
    if op.successful():
        req = Request.objects.get(serial_number="20200522-6758844")
        op.request = req
        op.description = "i was success"
        op.save()
        return op
    op.description = "i am not success"
    op.save()
    return op

