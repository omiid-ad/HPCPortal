import datetime

from random import randint
# from .models import *


def serial_generator():
    year = datetime.datetime.today().year.__str__()
    month = datetime.datetime.today().month.__str__()
    day = datetime.datetime.today().day.__str__()

    if int(month) < 10:
        month = "0" + month
    if int(day) < 10:
        day = "0" + day

    count = randint(1000000, 9999999)  # int
    serial = year + month + day + "-" + count.__str__()

    return serial


def call_back_payment(payment):
    pass
    # pay = Payment.objects.create(user=payment.user, acceptance_status="Acc", description=payment.description,
    #                              cost=payment.price)
    # pay.save()  # has bugs, need to set request payment and set it to Acc
