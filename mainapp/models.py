import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .utils import serial_generator


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="")
    field = models.CharField(max_length=100, verbose_name="")
    university = models.CharField(max_length=100, verbose_name="")
    guidance_master_full_name = models.CharField(max_length=100, verbose_name="")
    guidance_master_email = models.EmailField(max_length=200, verbose_name="")


class Request(models.Model):
    OS = [
        ('Win', 'Windows'),
        ('Lin', 'Linux')
    ]
    ACCEPTANCE_STATUS = [
        ('Pen', 'Pending'),
        ('Acc', 'Accepted'),
        ('Rej', 'Rejected')
    ]
    RENEWAL_STATUS = [
        ('Exp', 'Expired'),
        ('Ok', 'Okay'),
        ('Sus', 'Suspended'),
        ('Can', 'Canceled')
    ]

    date_requested = models.DateField(default=timezone.now)
    date_expired = models.DateField(editable=False, verbose_name="", null=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name="", null=True)
    os = models.CharField(choices=OS, max_length=50, verbose_name="")
    app_name = models.CharField(max_length=250, verbose_name="")
    cpu = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="")
    ram = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="")
    disk = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="")
    days = models.IntegerField(default=0, verbose_name="")
    show_cost = models.IntegerField(default=0, verbose_name="")
    description = models.TextField(blank=True, verbose_name="")
    serial_number = models.CharField(max_length=16, editable=False, unique=True, verbose_name="")
    acceptance_status = models.CharField(max_length=20, choices=ACCEPTANCE_STATUS, verbose_name="",
                                         default=ACCEPTANCE_STATUS[0])
    renewal_status = models.CharField(max_length=20, choices=RENEWAL_STATUS, verbose_name="", default=RENEWAL_STATUS[1])

    def save(self, *args, **kwargs):
        if not self.id:  # occur just for creating object, not for Editing object
            self.serial_number = serial_generator()
        self.date_expired = self.date_requested + datetime.timedelta(days=self.days)
        super().save()

    def __str__(self):
        return str(self.date_expired)
