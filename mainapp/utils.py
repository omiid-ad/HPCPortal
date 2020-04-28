import datetime
from random import randint


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
