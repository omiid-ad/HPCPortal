import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .serial_generator import serial_generator


class CustomUser(User):
    class Meta:
        proxy = True
        app_label = 'auth'
        verbose_name_plural = "کاربران"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="کاربر")
    field = models.CharField(max_length=100, verbose_name="رشته")
    university = models.CharField(max_length=100, verbose_name="دانشگاه")
    guidance_master_full_name = models.CharField(max_length=100, verbose_name="استاد راهنما")
    guidance_master_email = models.EmailField(max_length=200, verbose_name="ایمیل استاد راهنما")

    class Meta:
        verbose_name_plural = "پروفایل"

    def __str__(self):
        return self.user.get_full_name() + " - " + self.user.username

    @property
    def get_user_full_name(self):
        return self.user.get_full_name()


class Payment(models.Model):
    ACCEPTANCE_STATUS = [
        ('Pen', 'در انتظار تایید'),
        ('Acc', 'تایید شده'),
        ('Rej', 'رد شده'),
    ]
    date_payed = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ پرداخت")
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name="کاربر", null=True)
    acceptance_status = models.CharField(max_length=200, choices=ACCEPTANCE_STATUS, verbose_name="وضعیت تایید",
                                         default='Pen')
    receipt = models.ImageField(upload_to='receipts', verbose_name="عکس فیش‌واریزی")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    cost = models.IntegerField(default=0, verbose_name="هزینه پرداختی")

    def __str__(self):
        return str(self.pk) + " - " + str(self.user.user.get_full_name()) + " - " + str(self.cost)

    class Meta:
        verbose_name_plural = "پرداخت ها"


class Request(models.Model):
    OS = [
        ('Win', 'Windows'),
        ('Lin', 'Linux')
    ]
    ACCEPTANCE_STATUS = [
        ('Pen', 'در انتظار تایید'),
        ('Paying', 'در انتظار پرداخت'),
        ('Acc', 'تایید شده'),
        ('Rej', 'رد شده'),
        ('Exting', 'در انتظار تمدید'),
        ('Caning', 'در انتظار لغو'),
    ]
    RENEWAL_STATUS = [
        ('Exp', 'منقضی'),
        ('Ok', 'نرمال'),
        ('Sus', 'تعلیق شده'),
        ('Can', 'لغو شده')
    ]

    date_requested = models.DateField(default=timezone.now, verbose_name="تاریخ درخواست")
    date_expired = models.DateField(editable=False, verbose_name="تاریخ سررسید", null=True)
    date_expired_admin_only = models.DateField(editable=False, verbose_name="تاریخ سررسید بعد از تایید",
                                               null=True)  # just to show admin when date gonna expire
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name="کاربر", null=True)
    os = models.CharField(choices=OS, max_length=50, verbose_name="سیستم عامل")
    app_name = models.CharField(max_length=250, verbose_name="نام برنامه")
    cpu = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="پردازنده")
    ram = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="رم")
    disk = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="دیسک")
    days = models.IntegerField(default=0, verbose_name="تعداد روزها")
    show_cost = models.IntegerField(default=0, verbose_name="هزینه")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    user_description = models.TextField(blank=True, verbose_name="توضیحات کاربر")
    payment = models.ForeignKey(Payment, blank=True, on_delete=models.CASCADE, null=True, verbose_name="پرداخت")
    serial_number = models.CharField(max_length=16, editable=False, unique=True, verbose_name="شماره سریال")
    acceptance_status = models.CharField(max_length=200, choices=ACCEPTANCE_STATUS, verbose_name="وضعیت تایید",
                                         default='Pen')
    renewal_status = models.CharField(max_length=200, choices=RENEWAL_STATUS, verbose_name="وضعیت سرویس",
                                      default='Ok')

    def save(self, *args, **kwargs):
        if not self.id:  # occur just for creating object, not for Editing object
            self.serial_number = serial_generator()
            if self.date_expired is not None:
                self.date_expired_admin_only = None
            else:
                self.date_expired_admin_only = timezone.now() + datetime.timedelta(days=self.days)
        if self.date_expired is not None:
            self.date_expired_admin_only = None
        else:
            self.date_expired_admin_only = timezone.now() + datetime.timedelta(days=self.days)
        super().save()

    def __str__(self):
        return self.serial_number

    class Meta:
        verbose_name_plural = "درخواست سرویس"

    def is_expired(self):
        if self.date_expired is not None:
            if self.date_expired <= datetime.datetime.now().date():
                return True


class ExtendRequest(models.Model):
    ACCEPTANCE_STATUS = [
        ('Pen', 'در انتظار تایید'),
        ('Acc', 'تایید شده'),
        ('Rej', 'رد شده')
    ]

    request = models.ForeignKey(Request, on_delete=models.CASCADE, verbose_name="سرویس", null=True)
    days = models.IntegerField(default=0, verbose_name="تعداد روزها")
    date_expired_admin_only = models.DateField(editable=False, verbose_name="تاریخ سررسید بعد از تایید",
                                               null=True)  # just to show admin when date gonna expire
    receipt = models.ImageField(upload_to='receipts', verbose_name="عکس فیش‌واریزی")
    show_cost = models.IntegerField(default=0, verbose_name="هزینه")
    acceptance_status = models.CharField(max_length=200, choices=ACCEPTANCE_STATUS, verbose_name="وضعیت تایید",
                                         default='Pen')

    class Meta:
        verbose_name_plural = "درخواست های تمدید"

    def __str__(self):
        return self.request.serial_number

    def save(self, *args, **kwargs):
        if not self.id:  # occur just for creating object, not for Editing object
            if self.request.date_expired is not None:
                self.date_expired_admin_only = self.request.date_expired + datetime.timedelta(days=self.days)
            else:
                self.date_expired_admin_only = timezone.now() + datetime.timedelta(days=self.days)
        if self.request.date_expired is not None:
            self.date_expired_admin_only = self.request.date_expired + datetime.timedelta(days=self.days)
        else:
            self.date_expired_admin_only = timezone.now() + datetime.timedelta(days=self.days)
        super().save()


class CancelRequest(models.Model):
    ACCEPTANCE_STATUS = [
        ('Pen', 'در انتظار تایید'),
        ('Acc', 'تایید شده'),
        ('Rej', 'رد شده')
    ]

    request = models.ForeignKey(Request, on_delete=models.CASCADE, verbose_name="سرویس", null=True)
    acceptance_status = models.CharField(max_length=200, choices=ACCEPTANCE_STATUS, verbose_name="وضعیت تایید",
                                         default='Pen')

    class Meta:
        verbose_name_plural = "درخواست های لغو"

    def __str__(self):
        return self.request.serial_number
