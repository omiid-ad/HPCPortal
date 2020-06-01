from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from pardakht.admin import Payment as OnlinePayment
from axes.admin import AccessLog, AccessAttempt

from mainapp.utils import send_update_status_email, send_extend_date_email
from .models import *


class ProfileA(admin.ModelAdmin):
    date_hierarchy = 'user__date_joined'
    list_display = (
        'get_user_full_name', 'get_user_email', 'university', 'field', 'guidance_master_full_name', 'linked_to_user')
    list_filter = ('field', 'university')
    readonly_fields = ('user', 'university', 'field', 'guidance_master_full_name', 'guidance_master_email')
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    fieldsets = (
        ('اطلاعات دانشگاهی', {'fields': ('user', ('university', 'field'),)}),
        ('اطلاعات استاد راهنما', {'fields': (('guidance_master_full_name', 'guidance_master_email'),)}),
    )

    def has_add_permission(self, request, obj=None):
        return False

    actions = ['delete_selected', ]

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
        'days', 'date_requested', 'date_expired', 'serial_number', 'show_cost', 'show_cost_for_admin_only', 'user',
        'acceptance_status', 'renewal_status', 'user_description', 'date_expired_admin_only')
    list_display = (
        'serial_number', 'get_user_full_name', 'renewal_status', 'date_expired', 'acceptance_status',
        'linked_to_payment')
    list_filter = ('acceptance_status', 'renewal_status', 'os')
    search_fields = ['serial_number', 'user__user__first_name', 'user__user__last_name']
    fieldsets = (
        ('اطلاعات کاربر', {'fields': ('user',)}),
        ('جزئیات زمانی درخواست', {'fields': (('date_requested', 'date_expired'), ('days', 'date_expired_admin_only'))}),
        ('جزئیات فنی درخواست', {'fields': (('cpu', 'ram', 'disk'), 'app_name')}),
        ('جزئیات مالی درخواست', {'fields': (('show_cost', 'show_cost_for_admin_only'),)}),
        ('توضیحات', {'fields': (('user_description', 'description'),)}),
        ('وضعیت درخواست', {'fields': (('acceptance_status', 'renewal_status'),)}),
    )

    def extend_date(self, request, queryset):
        from django.shortcuts import render
        for q in queryset:
            if q.extend(1) is None:
                self.message_user(request, "امکان تمدید یک یا چند درخواست انتخاب شده، وجود ندارد",
                                  level=messages.ERROR)
                return HttpResponseRedirect(".")
        if 'apply' in request.POST:
            days = int(request.POST.get("days"))
            for obj in queryset:
                if obj.extend(days) is True:
                    obj.save()
                    send_extend_date_email(obj.user.user, obj)
                else:
                    self.message_user(request, "امکان تمدید یک یا چند درخواست انتخاب شده، وجود ندارد",
                                      level=messages.ERROR)
                    return HttpResponseRedirect(".")
            self.message_user(request, "با موفقیت تمدید شدند", level=messages.SUCCESS)
            return HttpResponseRedirect(".")
        return render(request, 'admin/mainapp/request/extend_confirm.html', {'orders': queryset})

    extend_date.short_description = "تمدید"

    def response_change(self, request, obj):
        if "_accept-request" in request.POST:
            if obj.acceptance_status == 'Pen':
                obj.acceptance_status = 'Paying'
                obj.renewal_status = 'Ok'
                obj.save()
                self.message_user(request, "با موفقیت تایید شد", level=messages.SUCCESS)
                send_update_status_email(request, obj.user.user)
                return HttpResponseRedirect(".")
            elif obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "این درخواست قبلا رد شده بود و نمیتوان آنرا تایید کرد", level=messages.ERROR)
                return HttpResponseRedirect(".")
            else:
                self.message_user(request,
                                  "این درخواست قبلا تایید شده بود", level=messages.ERROR)
                return HttpResponseRedirect(".")
        if "_reject-request" in request.POST:
            if obj.acceptance_status == 'Rej':
                self.message_user(request, "این درخواست قبلا رد شده بود", level=messages.ERROR)
                return HttpResponseRedirect(".")
            elif obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "این درخواست قبلا تایید شده بود و نمیتوان آنرا رد کرد", level=messages.ERROR)
                return HttpResponseRedirect(".")
            obj.date_expired = None
            obj.acceptance_status = 'Rej'
            obj.save()
            self.message_user(request, "با موفقیت رد شد", level=messages.SUCCESS)
            send_update_status_email(request, obj.user.user)
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def get_user_full_name(self, obj):
        return obj.user.user.get_full_name()

    get_user_full_name.short_description = 'نام و نام خانوادگی'
    get_user_full_name.admin_order_field = 'user__user__last_name'

    actions = ["accept", "reject", "normal", "suspend", "extend_date", "delete_selected"]

    def accept(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Pen':
                obj.acceptance_status = 'Paying'
                obj.renewal_status = 'Ok'
                obj.save()
                send_update_status_email(request, obj.user.user)
            elif obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، قبلا رد شده بود و نمیتوان آنرا تایید کرد",
                                  level=messages.ERROR)
                return
            else:
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل تایید شده بودند",
                                  level=messages.ERROR)
                return
        self.message_user(request, "با موفقیت تایید شدند", level=messages.SUCCESS)

    accept.short_description = "تایید درخواست ها"

    def reject(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل رد شده بودند و نمیتوانید دوباره آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            elif obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل تایید شده بودند و نمیتوانید دوباره آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            obj.date_expired = None
            obj.acceptance_status = 'Rej'
            obj.save()
            send_update_status_email(request, obj.user.user)
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
            send_update_status_email(request, obj.user.user)
        self.message_user(request, "با موفقیت تعلیق شدند", level=messages.SUCCESS)

    suspend.short_description = "تعلیق سرویس ها"


class ExtendRequestA(admin.ModelAdmin):
    readonly_fields = ('acceptance_status', 'days', 'show_cost', 'date_expired_admin_only', 'request', 'serial_number')
    list_display = (
        'serial_number', 'get_user_full_name', 'days', 'acceptance_status', 'show_cost', 'linked_to_request',
        'linked_to_payment')
    list_filter = ('acceptance_status',)
    search_fields = ['request__serial_number', 'serial_number']
    fieldsets = (
        ('اطلاعات سرویس', {'fields': ('request',)}),
        ('بیشتر',
         {'fields': (('serial_number', 'days', 'date_expired_admin_only'), ('show_cost', 'acceptance_status'))}),
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def get_user_full_name(self, obj):
        return obj.request.user.user.get_full_name()

    get_user_full_name.short_description = 'نام و نام خانوادگی'
    get_user_full_name.admin_order_field = 'user__last_name'

    actions = ["accept", "reject"]

    def response_change(self, request, obj):
        if "_accept-request" in request.POST:
            if obj.acceptance_status == 'Pen':
                obj.acceptance_status = 'Paying'
                obj.save()
                self.message_user(request, "با موفقیت تایید شد", level=messages.SUCCESS)
                send_update_status_email(request, obj.request.user.user)
                return HttpResponseRedirect(".")
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "درخواست انتخاب شده، از قبل رد شده بود و نمیتوان دوباره آنرا تایید کرد",
                                  level=messages.ERROR)
                return HttpResponseRedirect(".")
            else:
                self.message_user(request,
                                  "درخواست انتخاب شده، از قبل تایید شده بود",
                                  level=messages.ERROR)
                return HttpResponseRedirect(".")
        if "_reject-request" in request.POST:
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "درخواست انتخاب شده، از قبل رد شده بود و نمیتوان آنرا رد کنید",
                                  level=messages.ERROR)
                return HttpResponseRedirect(".")
            elif obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "درخواست انتخاب شده، از قبل تایید شده بود و نمیتوان آنرا رد کنید",
                                  level=messages.ERROR)
                return HttpResponseRedirect(".")
            obj.acceptance_status = 'Rej'
            obj.request.acceptance_status = 'Rej'
            obj.request.save()
            obj.save()
            self.message_user(request, "با موفقیت رد شدند", level=messages.SUCCESS)
            send_update_status_email(request, obj.request.user.user)
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def accept(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Pen':
                obj.acceptance_status = 'Paying'
                obj.save()
                send_update_status_email(request, obj.request.user.user)
            elif obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، قبلا رد شده بود و نمیتوان آنرا تایید کرد",
                                  level=messages.ERROR)
                return
            else:
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل تایید شده بودند",
                                  level=messages.ERROR)
                return
        self.message_user(request, "با موفقیت تایید شدند", level=messages.SUCCESS)

    accept.short_description = "تایید درخواست ها"

    def reject(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل رد شده بودند و نمیتوانید دوباره آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            elif obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل تایید شده بودند و نمیتوانید دوباره آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            obj.acceptance_status = 'Rej'
            obj.request.acceptance_status = 'Rej'
            obj.request.save()
            obj.save()
            send_update_status_email(request, obj.request.user.user)
        self.message_user(request, "با موفقیت رد شدند", level=messages.SUCCESS)

    reject.short_description = "رد درخواست ها"


class CancelRequestA(admin.ModelAdmin):
    readonly_fields = ('acceptance_status', 'request')
    list_display = ('request', 'get_user_full_name', 'acceptance_status', 'linked_to_request')
    list_filter = ('acceptance_status',)
    search_fields = ['request__serial_number', ]
    fieldsets = (
        ('اطلاعات سرویس', {'fields': ('request',)}),
        ('بیشتر', {'fields': ('acceptance_status',)}),
    )

    def has_add_permission(self, request, obj=None):
        return False

    def get_user_full_name(self, obj):
        return obj.request.user.user.get_full_name()

    def has_delete_permission(self, request, obj=None):
        return True

    get_user_full_name.short_description = 'نام و نام خانوادگی'
    get_user_full_name.admin_order_field = 'user__last_name'

    actions = ["accept", "reject"]

    def response_change(self, request, obj):
        if "_accept-request" in request.POST:
            if obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "درخواست انتخاب شده، از قبل تایید شده بود و نمیتوان دوباره آنرا تایید کرد",
                                  level=messages.ERROR)
                return HttpResponseRedirect(".")
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "درخواست انتخاب شده، از قبل رد شده بود و نمیتوان دوباره آنرا تایید کرد",
                                  level=messages.ERROR)
                return HttpResponseRedirect(".")
            obj.request.renewal_status = "Can"
            obj.request.acceptance_status = "Rej"
            obj.acceptance_status = 'Acc'
            obj.request.date_expired = None
            obj.request.save()
            obj.save()
            self.message_user(request, "درخواست با موفقیت لغو شد")
            send_update_status_email(request, obj.request.user.user)
            return HttpResponseRedirect(".")
        if "_reject-request" in request.POST:
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "درخواست انتخاب شده، از قبل رد شده بود و نمیتوان دوباره آنرا رد کرد",
                                  level=messages.ERROR)
                return HttpResponseRedirect(".")
            if obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "درخواست انتخاب شده، از قبل تایید شده بود و نمیتوان دوباره آنرا رد کرد",
                                  level=messages.ERROR)
                return HttpResponseRedirect(".")
            obj.acceptance_status = 'Rej'
            obj.request.acceptance_status = "Rej"
            obj.request.save()
            obj.save()
            self.message_user(request, "درخواست با موفقیت رد شد")
            send_update_status_email(request, obj.request.user.user)
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def accept(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل تایید شده بودند و نمیتوانید دوباره آنهارا تایید کنید",
                                  level=messages.ERROR)
                return
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل رد شده بودند و نمیتوانید دوباره آنهارا تایید کنید",
                                  level=messages.ERROR)
                return
            obj.request.renewal_status = "Can"
            obj.request.acceptance_status = "Rej"
            obj.acceptance_status = 'Acc'
            obj.request.date_expired = None
            obj.request.save()
            obj.save()
            send_update_status_email(request, obj.request.user.user)
        self.message_user(request, "با موفقیت لغو شدند", level=messages.SUCCESS)

    accept.short_description = "تایید درخواست های لغو"

    def reject(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل رد شده بودند و نمیتوانید دوباره آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            if obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "یک یا چند درخواست انتخاب شده، از قبل تایید شده بودند و نمیتوانید دوباره آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            obj.acceptance_status = 'Rej'
            obj.request.acceptance_status = "Rej"
            obj.request.save()
            obj.save()
            send_update_status_email(request, obj.request.user.user)
        self.message_user(request, "با موفقیت رد شدند", level=messages.SUCCESS)

    reject.short_description = "رد درخواست های لغو"


class PaymentA(admin.ModelAdmin):
    date_hierarchy = 'date_payed'
    readonly_fields = (
        'date_payed', 'acceptance_status', 'receipt', 'description', 'cost', 'request', 'extend', 'online_pay')
    list_display = (
        'get_user_full_name', 'request', 'cost', 'acceptance_status', 'linked_receipt_new_tab', 'linked_to_request',
        'linked_to_extend')
    list_filter = ('acceptance_status',)
    search_fields = ['request__user__user__first_name', 'request__user__user__last_name', 'request__serial_number']

    fieldsets = (
        ('اطلاعات پرداخت', {'fields': ('online_pay', 'date_payed', ('request', 'extend'), 'cost', 'receipt')}),
        ('بیشتر', {'fields': ('description', 'acceptance_status',)}),
    )

    def has_add_permission(self, request, obj=None):
        return False

    def get_user_full_name(self, obj):
        return obj.request.user.user.get_full_name()

    def has_delete_permission(self, request, obj=None):
        return True

    get_user_full_name.short_description = 'پرداخت کننده'
    get_user_full_name.admin_order_field = 'user__last_name'

    actions = ["accept", "reject"]

    def response_change(self, request, obj):
        if "_accept-request" in request.POST:
            if obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "پرداخت انتخاب شده، از قبل تایید شده بود و نمیتوانید دوباره آنرا تایید کنید",
                                  level=messages.ERROR)
                return HttpResponseRedirect(".")
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "پرداخت انتخاب شده، از قبل رد شده بود و نمیتوانید دوباره آنرا رد کنید",
                                  level=messages.ERROR)
                return HttpResponseRedirect(".")
            obj.acceptance_status = 'Acc'
            obj.request.acceptance_status = 'Acc'
            if obj.extend:
                obj.request.renewal_status = 'Ok'
                obj.extend.acceptance_status = 'Acc'
                if obj.request.date_expired is not None:
                    obj.request.date_expired = obj.request.date_expired + datetime.timedelta(days=obj.extend.days)
                else:
                    obj.request.date_expired = timezone.now() + datetime.timedelta(days=obj.extend.days)
                obj.extend.save()
            else:
                obj.request.date_expired = timezone.now() + datetime.timedelta(days=obj.request.days)
            obj.request.save()
            obj.save()
            self.message_user(request, "پرداخت با موفقیت تایید شد")
            send_update_status_email(request, obj.request.user.user)
            return HttpResponseRedirect(".")
        if "_reject-request" in request.POST:
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "پرداخت انتخاب شده، از قبل رد شده بود و نمیتوانید دوباره آنرا رد کنید",
                                  level=messages.ERROR)
                return
            if obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "پرداخت انتخاب شده، از قبل تایید شده بود و نمیتوانید دوباره آنرا رد کنید",
                                  level=messages.ERROR)
                return HttpResponseRedirect(".")
            obj.acceptance_status = 'Rej'
            if obj.extend:
                obj.extend.acceptance_status = 'Rej'
                obj.request.acceptance_status = 'Rej'
                obj.extend.save()
            else:
                obj.request.acceptance_status = 'Paying'
            obj.request.save()
            obj.save()
            self.message_user(request, "پرداخت با موفقیت رد شد")
            send_update_status_email(request, obj.request.user.user)
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def accept(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "یک یا چند پرداخت انتخاب شده، از قبل تایید شده بودند و نمیتوانید دوباره آنهارا تایید کنید",
                                  level=messages.ERROR)
                return
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "یک یا چند پرداخت انتخاب شده، از قبل رد شده بودند و نمیتوانید دوباره آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            obj.acceptance_status = 'Acc'
            obj.request.acceptance_status = 'Acc'
            if obj.extend:
                obj.request.renewal_status = 'Ok'
                obj.extend.acceptance_status = 'Acc'
                if obj.request.date_expired is not None:
                    obj.request.date_expired = obj.request.date_expired + datetime.timedelta(days=obj.extend.days)
                else:
                    obj.request.date_expired = timezone.now() + datetime.timedelta(days=obj.extend.days)
                obj.extend.save()
            else:
                obj.request.date_expired = timezone.now() + datetime.timedelta(days=obj.request.days)
            obj.request.save()
            obj.save()
            send_update_status_email(request, obj.request.user.user)

        self.message_user(request, "با موفقیت تایید شدند", level=messages.SUCCESS)

    accept.short_description = "تایید پرداخت ها"

    def reject(self, request, queryset):
        for obj in queryset:
            if obj.acceptance_status == 'Rej':
                self.message_user(request,
                                  "یک یا چند پرداخت انتخاب شده، از قبل رد شده بودند و نمیتوانید دوباره آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            if obj.acceptance_status == 'Acc':
                self.message_user(request,
                                  "یک یا چند پرداخت انتخاب شده، از قبل تایید شده بودند و نمیتوانید آنهارا رد کنید",
                                  level=messages.ERROR)
                return
            obj.acceptance_status = 'Rej'
            if obj.extend:
                obj.extend.acceptance_status = 'Paying'
                obj.request.acceptance_status = 'Rej'
                obj.extend.save()
            else:
                obj.request.acceptance_status = 'Paying'
            obj.request.save()
            obj.save()
            send_update_status_email(request, obj.request.user.user)
        self.message_user(request, "با موفقیت رد شدند", level=messages.SUCCESS)

    reject.short_description = "رد پرداخت ها"


# class OnlinePaymentA(admin.ModelAdmin):
#     list_display = ('user', 'price', 'gateway', 'state', 'payment_result')
#     date_hierarchy = 'created_at'
#     list_filter = ('state', 'payment_result')
#     readonly_fields = ('updated_at',)
#     fieldsets = (
#         ('پرداخت کننده', {'fields': ('user',)}),
#         ('جزئیات', {'fields': ('price', 'description', 'updated_at', 'verification_result', 'ref_number')}),
#     )
#
#     def has_add_permission(self, request, obj=None):
#         return False
#
#     def has_delete_permission(self, request, obj=None):
#         return False


class UserAdminA(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'is_active', 'linked_to_profile')
    exclude = ('groups', 'user_permissions', 'is_staff', 'is_superuser')
    fieldsets = (
        ('', {'fields': (('username',),)}),
        ('اطلاعات شخصی', {'fields': (('first_name', 'last_name', 'email'),)}),
        ('دسترسی ها', {'fields': ('is_active',)}),
        ('اطلاعات ورود', {'fields': (('last_login', 'date_joined'),)}),
    )
    list_filter = ('is_active',)

    readonly_fields = ('last_login', 'date_joined')

    def has_add_permission(self, request):
        return False

    def response_change(self, request, obj):
        if "_deactivate-user" in request.POST:
            obj.is_active = False
            obj.save()
            self.message_user(request, "حساب غیرفعال شد")
            return HttpResponseRedirect(".")
        if "_activate-user" in request.POST:
            obj.is_active = True
            obj.save()
            self.message_user(request, "حساب فعال شد")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)


class ResourceLimitA(admin.ModelAdmin):
    list_display = ('os',)
    fieldsets = (
        ('', {'fields': (('os',),)}),
        ('پردازنده', {'fields': (('cpu_min', 'cpu_max'),)}),
        ('رم', {'fields': (('ram_min', 'ram_max'),)}),
        ('دیسک', {'fields': (('disk_min', 'disk_max'),)}),
        ('روزها', {'fields': (('days_min', 'days_max'),)}),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('os',)
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        if ResourceLimit.objects.count() >= 2:
            return False
        return True


admin.site.unregister(User)
admin.site.register(CustomUser, UserAdminA)
admin.site.register(Profile, ProfileA)
admin.site.register(Request, RequestA)
admin.site.register(ExtendRequest, ExtendRequestA)
admin.site.register(CancelRequest, CancelRequestA)
admin.site.register(Payment, PaymentA)
admin.site.unregister(Group)
# admin.site.unregister(OnlinePayment)
admin.site.register(MyPayment)
admin.site.unregister(AccessLog)
admin.site.unregister(AccessAttempt)
admin.site.disable_action('delete_selected')
admin.site.register(ResourceLimit, ResourceLimitA)

admin.site.site_header = "پنل مدیریت پرتال"
admin.site.site_title = "پرتال مرکز پردازش های سریع دانشگاه شهید چمران اهواز"
admin.site.index_title = "پنل مدیریت"
