import datetime

from . import models


def serial_generator():
    year = datetime.datetime.today().year.__str__()
    month = datetime.datetime.today().month.__str__()
    day = datetime.datetime.today().day.__str__()

    if int(month) < 10:
        month = "0" + month
    if int(day) < 10:
        day = "0" + day

    count = 1000000 + models.Request.objects.all().count()  # int
    serial = year + month + day + "-" + count.__str__()
    return serial
