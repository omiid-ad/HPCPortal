import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .utils import serial_generator


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="کاربر")
    field = models.CharField(max_length=100, verbose_name="رشته")
    university = models.CharField(max_length=100, verbose_name="دانشگاه")
    guidance_master_full_name = models.CharField(max_length=100, verbose_name="استاد راهنما")
    guidance_master_email = models.EmailField(max_length=200, verbose_name="ایمیل استاد راهنما")


class Request(models.Model):
    OS = [
        ('Win', 'Windows'),
        ('Lin', 'Linux')
    ]
    ACCEPTANCE_STATUS = [
        ('Pen', 'در انتظار تایید'),
        ('Acc', 'تایید شده'),
        ('Rej', 'رد شده')
    ]
    RENEWAL_STATUS = [
        ('Exp', 'منقضی'),
        ('Ok', 'نرمال'),
        ('Sus', 'تعلیق شده'),
        ('Can', 'لغو شده')
    ]

    date_requested = models.DateField(default=timezone.now)
    date_expired = models.DateField(editable=False, verbose_name="تاریخ سررسید", null=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name="کاربر", null=True)
    os = models.CharField(choices=OS, max_length=50, verbose_name="سیستم عامل")
    app_name = models.CharField(max_length=250, verbose_name="نام برنامه")
    cpu = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="پردازنده")
    ram = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="رم")
    disk = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="دیسک")
    days = models.IntegerField(default=0, verbose_name="تعداد روزها")
    show_cost = models.IntegerField(default=0, verbose_name="هزینه")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    serial_number = models.CharField(max_length=16, editable=False, unique=True, verbose_name="شماره سریال")
    acceptance_status = models.CharField(max_length=200, choices=ACCEPTANCE_STATUS, verbose_name="وضعیت تایید",
                                         default='Pen')
    renewal_status = models.CharField(max_length=200, choices=RENEWAL_STATUS, verbose_name="وضعیت سرویس",
                                      default='Ok')

    def save(self, *args, **kwargs):
        if not self.id:  # occur just for creating object, not for Editing object
            self.serial_number = serial_generator()
        self.date_expired = self.date_requested + datetime.timedelta(days=self.days)
        super().save()

    def __str__(self):
        return str(self.date_expired)
