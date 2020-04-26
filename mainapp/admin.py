from django.contrib.auth.admin import UserAdmin
from django.contrib import admin, messages
from django.contrib.auth.models import Group
from .models import *


class ProfileA(admin.ModelAdmin):
    date_hierarchy = 'user__date_joined'
    list_display = ('get_user_full_name', 'get_user_email', 'university', 'field', 'guidance_master_full_name')
    list_filter = ('field', 'university')
    readonly_fields = ('user', 'university', 'field', 'guidance_master_full_name', 'guidance_master_email')
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    fieldsets = (
        ('اطلاعات دانشگاهی', {'fields': ('user', 'university', 'field')}),
        ('اطلاعات استاد راهنما', {'fields': ('guidance_master_full_name', 'guidance_master_email')}),
    )

    def get_user_full_name(self, obj):
        return obj.user.get_full_name()

    get_user_full_name.short_description = 'نام و نام خانوادگی'
    get_user_full_name.admin_order_field = 'user__last_name'

    def get_user_email(self, obj):
        return obj.user.email

    get_user_email.short_description = 'ایمیل'


class RequestA(admin.ModelAdmin):
    date_hierarchy = 'date_requested'
    readonly_fields = (
        'days', 'date_requested', 'date_expired', 'serial_number', 'show_cost', 'user', 'acceptance_status',
        'renewal_status', 'user_description', 'date_expired_admin_only')
    list_display = ('get_user_full_name', 'serial_number', 'acceptance_status', 'renewal_status', 'date_expired',)
    list_filter = ('acceptance_status', 'renewal_status', 'os')
    search_fields = ['serial_number', 'user__user__first_name', 'user__user__last_name']
    fieldsets = (
        ('اطلاعات کاربر', {'fields': ('user',)}),
        ('جزئیات زمانی درخواست', {'fields': ('date_requested', 'date_expired', 'days', 'date_expired_admin_only')}),
        ('جزئیات فنی درخواست', {'fields': ('cpu', 'ram', 'disk', 'app_name')}),
        ('جزئیات مالی درخواست', {'fields': ('show_cost', 'payment')}),
        ('توضیحات', {'fields': ('user_description', 'description',)}),
        ('وضعیت درخواست', {'fields': ('acceptance_status', 'renewal_status')}),
    )

    def get_user_full_name(self, obj):
        return obj.user.user.get_full_name()

    get_user_full_name.short_description = 'نام و نام خانوادگی'
    get_user_full_name.admin_order_field = 'user__last_name'

    actions = ["accept", "reject", "normal", "suspend"]

    def accept(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Paying':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل تایید شده بودند و در انتظار تایید پرداخت هستند",
                                  level=messages.ERROR)
                return
            obj.acceptance_status = 'Paying'
            obj.renewal_status = 'Ok'
            obj.save()
        self.message_user(request, "با موفقیت تایید شدند", level=messages.SUCCESS)

    accept.short_description = "تایید درخواست ها"

    def reject(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل رد شده بودند و نمیتوانید دوباره آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            obj.date_expired = None
            obj.acceptance_status = 'Rej'
            obj.save()
        self.message_user(request, "با موفقیت رد شدند", level=messages.SUCCESS)

    reject.short_description = "رد درخواست ها"

    def normal(self, request, queryset):
        queryset.update(renewal_status='Ok')
        self.message_user(request, "وضعیت درخواست(ها) با موفقیت نرمال شد", level=messages.SUCCESS)

    normal.short_description = "سرویس نرمال"

    def suspend(self, request, queryset):
        for obj in queryset:
            if obj.renewal_status == 'Sus':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل تعلیق شده بودند و نمیتوانید دوباره آنهارا تعلیق کنید",
                                  level=messages.ERROR)
                return
            obj.date_expired = None
            obj.acceptance_status = "Rej"
            obj.renewal_status = 'Sus'
            obj.save()
        self.message_user(request, "با موفقیت تعلیق شدند", level=messages.SUCCESS)

    suspend.short_description = "تعلیق سرویس ها"


class ExtendRequestA(admin.ModelAdmin):
    readonly_fields = ('acceptance_status', 'days', 'show_cost', 'receipt', 'date_expired_admin_only')
    list_display = ('request', 'days', 'acceptance_status', 'show_cost', 'receipt')
    list_filter = ('acceptance_status',)
    search_fields = ['request__serial_number', ]
    fieldsets = (
        ('اطلاعات سرویس', {'fields': ('request',)}),
        ('بیشتر', {'fields': ('days', 'date_expired_admin_only', 'acceptance_status', 'show_cost', 'receipt')}),
    )

    actions = ["accept", "reject"]

    def accept(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل تایید شده بودند و نمیتوانید دوباره آنهارا تایید کنید",
                                  level=messages.ERROR)
                return
            if obj.request.date_expired is not None:
                obj.request.date_expired = obj.request.date_expired + datetime.timedelta(days=obj.days)
            else:
                obj.request.date_expired = timezone.now() + datetime.timedelta(days=obj.days)
            obj.acceptance_status = 'Acc'
            obj.request.acceptance_status = 'Acc'
            obj.request.renewal_status = 'Ok'
            obj.request.save()
            obj.save()
        self.message_user(request, "با موفقیت تمدید شدند", level=messages.SUCCESS)

    accept.short_description = "تایید درخواست های تمدید"

    def reject(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل رد شده بودند و نمیتوانید دوباره آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            obj.acceptance_status = 'Rej'
            obj.request.acceptance_status = "Rej"
            obj.request.save()
            obj.save()
        self.message_user(request, "با موفقیت لغو شدند", level=messages.SUCCESS)

    reject.short_description = "رد درخواست های تمدید"


class CancelRequestA(admin.ModelAdmin):
    readonly_fields = ('acceptance_status',)
    list_display = ('request', 'acceptance_status')
    list_filter = ('acceptance_status',)
    search_fields = ['request__serial_number', ]
    fieldsets = (
        ('اطلاعات سرویس', {'fields': ('request',)}),
        ('بیشتر', {'fields': ('acceptance_status',)}),
    )

    actions = ["accept", "reject"]

    def accept(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل تایید شده بودند و نمیتوانید دوباره آنهارا تایید کنید",
                                  level=messages.ERROR)
                return
            obj.request.renewal_status = "Can"
            obj.request.acceptance_status = "Acc"
            obj.acceptance_status = 'Acc'
            obj.request.date_expired = None
            obj.request.save()
            obj.save()
        self.message_user(request, "با موفقیت لغو شدند", level=messages.SUCCESS)

    accept.short_description = "تایید درخواست های لغو"

    def reject(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل رد شده بودند و نمیتوانید دوباره آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            obj.acceptance_status = 'Rej'
            obj.request.acceptance_status = "Rej"
            obj.request.save()
            obj.save()
        self.message_user(request, "با موفقیت رد شدند", level=messages.SUCCESS)

    reject.short_description = "رد درخواست های لغو"


class PaymentA(admin.ModelAdmin):
    date_hierarchy = 'date_payed'
    readonly_fields = ('date_payed', 'acceptance_status', 'receipt', 'description', 'cost')
    list_display = ('get_payed_req', 'cost', 'acceptance_status', 'receipt')
    list_filter = ('acceptance_status',)

    fieldsets = (
        ('اطلاعات پرداخت', {'fields': ('date_payed', 'cost', 'receipt')}),
        ('بیشتر', {'fields': ('description', 'acceptance_status',)}),
    )

    def get_payed_req(self, obj):
        req = Request.objects.get(payment=obj)
        return req

    get_payed_req.short_description = 'سرویس مربوطه'

    actions = ["accept", "reject"]

    def accept(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "یک یا چند پرداخت انتخاب شده، از قبل تایید شده بودند و نمیتوانید دوباره آنهارا تایید کنید",
                                  level=messages.ERROR)
                return
            req = Request.objects.get(payment=obj)
            req.renewal_status = "Ok"
            req.acceptance_status = "Acc"
            req.payment = obj
            obj.acceptance_status = 'Acc'
            req.date_expired = timezone.now() + datetime.timedelta(days=req.days)
            req.save()
            obj.save()
        self.message_user(request, "با موفقیت تایید شدند", level=messages.SUCCESS)

    accept.short_description = "تایید پرداخت ها"

    def reject(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "یک یا چند پرداخت انتخاب شده، از قبل رد شده بودند و نمیتوانید دوباره آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            req = Request.objects.get(payment=obj)
            req.payment = None
            req.acceptance_status = "Paying"
            obj.acceptance_status = 'Rej'
            obj.save()
            req.save()
        self.message_user(request, "با موفقیت رد شدند", level=messages.SUCCESS)

    reject.short_description = "رد پرداخت ها"


UserAdmin.list_display = ('username', 'first_name', 'last_name', 'is_staff')
UserAdmin.fieldsets = (
    ('None', {'fields': ('username', 'password')}),
    ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email')}),
    ('دسترسی ها', {'fields': (('is_active', 'is_staff', 'is_superuser'), ('last_login', 'date_joined'))}),
)
UserAdmin.list_filter = ('is_superuser', 'is_active')
UserAdmin.readonly_fields = ('last_login', 'date_joined')

admin.site.unregister(User)
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Profile, ProfileA)
admin.site.register(Request, RequestA)
admin.site.register(ExtendRequest, ExtendRequestA)
admin.site.register(CancelRequest, CancelRequestA)
admin.site.register(Payment, PaymentA)
admin.site.unregister(Group)

admin.site.site_header = "پنل مدیریت پرتال"
admin.site.site_title = "پرتال درخواست مرکز پردازش های سریع دانشگاه شهید چمران اهواز"
admin.site.index_title = "پنل مدیریت"
