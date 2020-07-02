import datetime

from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from pardakht.models import Payment as OnlinePayment

from .serial_generator import serial_generator


class CustomUser(User):
    class Meta:
        proxy = True
        app_label = 'auth'
        verbose_name_plural = "کاربران"
        verbose_name = "کاربر"

    def __str__(self):
        return self.get_full_name()

    def linked_to_profile(self):
        if self.profile:
            return format_html(
                '<a href="{}">مشاهده پروفایل</a>',
                reverse("admin:mainapp_profile_change", args=(self.profile.id,)),
            )
        else:
            return format_html(
                '<a href="#">ندارد</a>',
            )

    linked_to_profile.short_description = "پروفایل"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="کاربر")
    field = models.CharField(max_length=100, verbose_name="رشته")
    university = models.CharField(max_length=100, verbose_name="دانشگاه")
    guidance_master_full_name = models.CharField(max_length=100, verbose_name="استاد راهنما")
    guidance_master_email = models.EmailField(max_length=200, verbose_name="ایمیل استاد راهنما")

    class Meta:
        verbose_name_plural = "پروفایل‌ها"
        verbose_name = "پروفایل"

    def __str__(self):
        return self.user.get_full_name() + " - " + self.user.username

    def linked_to_user(self):
        if self.user:
            return format_html(
                '<a href="{}">مشاهده کاربر</a>',
                reverse("admin:auth_customuser_change", args=(self.user.id,)),
            )
        else:
            return format_html(
                '<a href="#">ندارد</a>',
            )

    linked_to_user.short_description = "اطلاعات کاربری"

    @property
    def get_user_full_name(self):
        return self.user.get_full_name()


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
        ('AccPaying', 'در انتظار تایید پرداخت'),
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
    show_cost = models.IntegerField(default=0, verbose_name="هزینه‌ی قابل پرداخت")
    show_cost_for_admin_only = models.IntegerField(default=0, verbose_name="هزینه‌ی با/بی تخفیف", null=True)
    description = models.TextField(blank=True, verbose_name="توضیحات")
    user_description = models.TextField(blank=True, verbose_name="توضیحات کاربر")
    serial_number = models.CharField(max_length=16, editable=False, unique=True, verbose_name="شماره سریال")
    acceptance_status = models.CharField(max_length=200, choices=ACCEPTANCE_STATUS, verbose_name="وضعیت تایید",
                                         default='Pen')
    renewal_status = models.CharField(max_length=200, choices=RENEWAL_STATUS, verbose_name="وضعیت سرویس",
                                      default='Ok')

    def __init__(self, *args, **kwargs):
        super(Request, self).__init__(*args, **kwargs)
        self.__description__ = self.description  # to store old desc

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
        if self.description != self.__description__:  # description changed
            self.__description__ = self.description  # update old desc
            from .utils import send_generic_email
            send_generic_email(self.user.user, self, "به‌روز شدن توضیحات",
                               email_template="mainapp/changed_description_email.html")
        super().save()

    def __str__(self):
        return self.serial_number

    class Meta:
        verbose_name_plural = "درخواست سرویس‌ها"
        verbose_name = "درخواست سرویس"
        ordering = ('-date_requested',)

    def extend(self, days):
        if days > 0:
            if self.acceptance_status == "Acc":
                if self.renewal_status == "Ok":
                    if self.date_expired is not None:
                        self.date_expired = self.date_expired + datetime.timedelta(days=days)
                        return True

    def gonna_expire_today(self):
        return self.date_expired == datetime.datetime.now().date()

    def is_expired(self):
        if self.date_expired is not None:
            if self.date_expired <= datetime.datetime.now().date():
                return True

    def linked_to_payment(self):
        pay = Payment.objects.filter(request=self, extend=None)
        if pay is not None and pay.count() == 1:
            return format_html(
                '<a href="{}">مشاهده پرداخت</a>',
                reverse("admin:mainapp_payment_change", args=(pay.first().id,)),
            )
        else:
            return None

    linked_to_payment.short_description = "پرداخت"

    def is_request_n_days_to_expire(self, n_days):
        future = datetime.date.today() + datetime.timedelta(days=n_days)
        if future >= self.date_expired:
            return True
        return False


class ExtendRequest(models.Model):
    ACCEPTANCE_STATUS = [
        ('Pen', 'در انتظار تایید'),
        ('Acc', 'تایید شده'),
        ('Rej', 'رد شده'),
        ('Paying', 'در انتظار پرداخت'),
        ('AccPaying', 'در انتظار تایید پرداخت'),
    ]

    date_requested = models.DateField(null=True, default=timezone.now, verbose_name="تاریخ درخواست")
    request = models.ForeignKey(Request, on_delete=models.CASCADE, verbose_name="سرویس", null=True)
    days = models.IntegerField(default=0, verbose_name="تعداد روزها")
    date_expired_admin_only = models.DateField(editable=False, verbose_name="تاریخ سررسید بعد از تایید",
                                               null=True)  # just to show admin when date gonna expire
    show_cost = models.IntegerField(default=0, verbose_name="هزینه")
    acceptance_status = models.CharField(max_length=200, choices=ACCEPTANCE_STATUS, verbose_name="وضعیت تایید",
                                         default='Pen')
    serial_number = models.CharField(max_length=16, null=True, editable=False, unique=True, verbose_name="شماره سریال")

    class Meta:
        verbose_name_plural = "درخواست های تمدید"
        verbose_name = "درخواست تمدید"
        ordering = ('-date_requested',)

    def __str__(self):
        if self.serial_number:
            return self.serial_number
        return str(self.id)

    def save(self, *args, **kwargs):
        if not self.id:  # occur just for creating object, not for Editing object
            self.serial_number = serial_generator()
            if self.request.date_expired is not None:
                self.date_expired_admin_only = self.request.date_expired + datetime.timedelta(days=self.days)
                super().save()
                return
            else:
                self.date_expired_admin_only = timezone.now() + datetime.timedelta(days=self.days)
                super().save()
                return
        if self.acceptance_status == "Acc" and self.request.date_expired is not None:
            self.date_expired_admin_only = self.request.date_expired
            super().save()
            return
        if self.request.date_expired is not None:
            self.date_expired_admin_only = self.request.date_expired + datetime.timedelta(days=self.days)
            super().save()
            return
        else:
            self.date_expired_admin_only = timezone.now() + datetime.timedelta(days=self.days)
            super().save()
            return

    def linked_to_request(self):
        if self.request:
            return format_html(
                '<a href="{}">مشاهده سرویس</a>',
                reverse("admin:mainapp_request_change", args=(self.request.id,)),
            )
        else:
            return None

    linked_to_request.short_description = "سرویس"

    def linked_to_payment(self):
        pay = Payment.objects.get(extend=self)
        if pay:
            return format_html(
                '<a href="{}">مشاهده پرداخت</a>',
                reverse("admin:mainapp_payment_change", args=(pay.id,)),
            )
        else:
            return None

    linked_to_payment.short_description = "پرداخت"


class MyPayment(models.Model):
    django_pardakht = models.OneToOneField(OnlinePayment, on_delete=models.CASCADE)
    request = models.ForeignKey(Request, on_delete=models.CASCADE, null=True, blank=True, verbose_name="سرویس")
    extend = models.OneToOneField(ExtendRequest, on_delete=models.CASCADE, null=True, blank=True, verbose_name="تمدید")

    class Meta:
        verbose_name_plural = "پرداخت های آنلاین"
        verbose_name = "پرداخت آنلاین"

    def __str__(self):
        if self.extend:
            return "مبلغ " + str(
                self.django_pardakht.price) + " توسط " + self.request.user.get_user_full_name + " برای تمدید " + \
                   self.extend.serial_number
        elif self.request:
            return "مبلغ " + str(
                self.django_pardakht.price) + " توسط " + self.request.user.get_user_full_name + " برای سرویس " + \
                   self.request.serial_number
        else:
            return "Invalid payment"


class Payment(models.Model):
    ACCEPTANCE_STATUS = [
        ('Pen', 'در انتظار تایید'),
        ('Acc', 'تایید شده'),
        ('Rej', 'رد شده'),
    ]
    request = models.ForeignKey(Request, on_delete=models.CASCADE, null=True, blank=True, verbose_name="سرویس")
    extend = models.OneToOneField(ExtendRequest, on_delete=models.CASCADE, null=True, blank=True, verbose_name="تمدید")
    online_pay = models.OneToOneField(OnlinePayment, on_delete=models.CASCADE, null=True, blank=True,
                                      verbose_name="پرداخت آنلاین")
    date_payed = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ پرداخت")
    acceptance_status = models.CharField(max_length=200, choices=ACCEPTANCE_STATUS, verbose_name="وضعیت تایید",
                                         default='Pen')
    receipt = models.ImageField(upload_to='receipts', verbose_name="عکس فیش‌واریزی", blank=True, null=True)
    description = models.TextField(blank=True, verbose_name="توضیحات")
    cost = models.IntegerField(default=0, verbose_name="هزینه پرداختی")

    def linked_receipt_new_tab(self):
        if self.receipt:
            return format_html(
                '<a href="/media/{}" target="_blank">مشاهده رسید</a>',
                self.receipt.name,
            )
        else:
            return None

    linked_receipt_new_tab.short_description = "رسید"

    def __str__(self):
        return "مبلغ " + str(
            self.cost) + " توسط " + self.request.user.get_user_full_name + " برای سرویس " + self.request.serial_number

    class Meta:
        verbose_name_plural = "پرداخت ها"
        verbose_name = "پرداخت"

    def linked_to_request(self):
        if self.request:
            return format_html(
                '<a href="{}">مشاهده سرویس</a>',
                reverse("admin:mainapp_request_change", args=(self.request.id,)),
            )
        else:
            return None

    linked_to_request.short_description = "سرویس"

    def linked_to_extend(self):
        if self.extend:
            return format_html(
                '<a href="{}">مشاهده تمدید</a>',
                reverse("admin:mainapp_extendrequest_change", args=(self.extend.id,)),
            )
        else:
            return None

    linked_to_extend.short_description = "تمدید"


class CancelRequest(models.Model):
    ACCEPTANCE_STATUS = [
        ('Pen', 'در انتظار تایید'),
        ('Acc', 'تایید شده'),
        ('Rej', 'رد شده')
    ]

    request = models.OneToOneField(Request, on_delete=models.CASCADE, verbose_name="سرویس", null=True)
    acceptance_status = models.CharField(max_length=200, choices=ACCEPTANCE_STATUS, verbose_name="وضعیت تایید",
                                         default='Pen')

    class Meta:
        verbose_name_plural = "درخواست های لغو"
        verbose_name = "درخواست لغو"

    def __str__(self):
        return self.request.serial_number

    def linked_to_request(self):
        if self.request:
            return format_html(
                '<a href="{}">مشاهده سرویس</a>',
                reverse("admin:mainapp_request_change", args=(self.request.id,)),
            )
        else:
            return None

    linked_to_request.short_description = "سرویس"


req = Request()  # to access OS variable


class ResourceLimit(models.Model):
    os = models.CharField(choices=req.OS, max_length=50, verbose_name="برای سیستم عامل")
    cpu_min = models.IntegerField(default=0, verbose_name="حداقل پردازنده")
    cpu_max = models.IntegerField(default=0, verbose_name="حداکثر پردازنده")
    ram_min = models.IntegerField(default=0, verbose_name="حداقل رم")
    ram_max = models.IntegerField(default=0, verbose_name="حداکثر رم")
    disk_min = models.IntegerField(default=0, verbose_name="حداقل دیسک")
    disk_max = models.IntegerField(default=0, verbose_name="حداکثر دیسک")
    days_min = models.IntegerField(default=0, verbose_name="حداقل تعداد روزها")
    days_max = models.IntegerField(default=0, verbose_name="حداکثر تعداد روزها")

    def save(self, *args, **kwargs):
        if not self.pk and ResourceLimit.objects.count() >= 2:
            raise ValidationError("Can only create 2 instances")
        return super(ResourceLimit, self).save(*args, **kwargs)

    def __str__(self):
        return self.os

    class Meta:
        verbose_name_plural = "محدودیت های منابع"
        verbose_name = "محدودیت منابع"


class OnlinePaymentProxy(OnlinePayment):
    class Meta:
        proxy = True
        app_label = 'mainapp'
        verbose_name_plural = "پرداخت های آنلاین"
        verbose_name = "پرداخت آنلاین"

    def __str__(self):
        if self.user:
            return "مبلغ " + str(
                self.price) + " توسط " + self.user.get_full_name()
        return ""

    def linked_to_request(self):
        try:
            mp = MyPayment.objects.get(django_pardakht=self)
        except MyPayment.DoesNotExist:
            return None
        if mp.request:
            return format_html(
                '<a href="{}">مشاهده سرویس</a>',
                reverse("admin:mainapp_request_change", args=(mp.request.id,)),
            )

    linked_to_request.short_description = "سرویس"

    def linked_to_extend(self):
        try:
            mp = MyPayment.objects.get(django_pardakht=self)
        except MyPayment.DoesNotExist:
            return None
        if mp.extend:
            return format_html(
                '<a href="{}">مشاهده تمدید</a>',
                reverse("admin:mainapp_extendrequest_change", args=(mp.extend.id,)),
            )

    linked_to_extend.short_description = "تمدید"


class Software(models.Model):
    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    updated_at = models.DateTimeField(_('آخرین تغییر'), auto_now=True)
    title = models.CharField(max_length=150, verbose_name=_("عنوان"))
    uploaded_file = models.FileField(upload_to="softwares", verbose_name=_("فایل"))
    os = models.CharField(choices=req.OS, max_length=50, verbose_name=_("برای سیستم عامل"))
    description = models.TextField(blank=True, null=True, verbose_name=_("راهنما/توضیحات"),
                                   help_text=_('اختیاری، کوتاه در حد یک خط'))
    is_active = models.BooleanField(default=True, verbose_name=_("فعال"),
                                    help_text=_('مشخص میکند این نرم‌افزار در سایت اصلی نمایش داده شود یا خیر.'
                                                'بجای پاک کردن نرم افزار، تیک آنرا بردارید.'))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "نرم افزار موردنیاز"
        verbose_name_plural = "نرم افزارهای موردنیاز"
