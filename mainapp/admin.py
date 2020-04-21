import datetime

from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
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
        'renewal_status', 'user_description')
    list_display = ('get_user_full_name', 'serial_number', 'acceptance_status', 'renewal_status')
    list_filter = ('acceptance_status', 'renewal_status', 'os')
    search_fields = ['serial_number', 'user__user__first_name', 'user__user__last_name']
    fieldsets = (
        ('اطلاعات کاربر', {'fields': ('user',)}),
        ('جزئیات زمانی درخواست', {'fields': ('date_requested', 'date_expired', 'days')}),
        ('جزئیات فنی درخواست', {'fields': ('cpu', 'ram', 'disk', 'app_name')}),
        ('جزئیات مالی درخواست', {'fields': ('show_cost',)}),
        ('توضیحات', {'fields': ('user_description', 'description',)}),
        ('وضعیت درخواست', {'fields': ('acceptance_status', 'renewal_status')}),
    )

    def get_user_full_name(self, obj):
        return obj.user.user.get_full_name()

    get_user_full_name.short_description = 'نام و نام خانوادگی'
    get_user_full_name.admin_order_field = 'user__last_name'

    actions = ["accept", "reject", "normal", "cancel", "suspend"]

    def accept(self, request, queryset):
        for obj in queryset:
            obj.date_expired = timezone.now() + datetime.timedelta(days=obj.days)
            obj.acceptance_status = 'Acc'
            obj.save()

    accept.short_description = "تایید درخواست ها"

    def reject(self, request, queryset):
        for obj in queryset:
            obj.date_expired = None
            obj.acceptance_status = 'Rej'
            obj.save()

    reject.short_description = "رد درخواست ها"

    def normal(self, request, queryset):
        queryset.update(renewal_status='Ok')

    normal.short_description = "سرویس نرمال"

    def cancel(self, request, queryset):
        for obj in queryset:
            obj.date_expired = None
            obj.renewal_status = 'Can'
            obj.save()

    cancel.short_description = "لغو سرویس ها"

    def suspend(self, request, queryset):
        for obj in queryset:
            obj.date_expired = None
            obj.renewal_status = 'Sus'
            obj.save()

    suspend.short_description = "تعلیق سرویس ها"


class ExtendRequestA(admin.ModelAdmin):
    readonly_fields = ('acceptance_status', 'days')
    list_display = ('request', 'days', 'acceptance_status')
    list_filter = ('acceptance_status',)
    search_fields = ['request__serial_number', ]
    fieldsets = (
        ('اطلاعات سرویس', {'fields': ('request',)}),
        ('بیشتر', {'fields': ('days', 'acceptance_status')}),
    )

    actions = ["accept", "reject"]

    def accept(self, request, queryset):
        for obj in queryset:
            if obj.request.date_expired is not None:
                obj.request.date_expired = obj.request.date_expired + datetime.timedelta(days=obj.days)
            else:
                obj.request.date_expired = timezone.now() + datetime.timedelta(days=obj.days)
            obj.acceptance_status = 'Acc'
            obj.request.acceptance_status = 'Acc'
            obj.request.save()
            obj.save()

    accept.short_description = "تایید درخواست های تمدید"

    def reject(self, request, queryset):
        for obj in queryset:
            obj.acceptance_status = 'Rej'
            obj.request.acceptance_status = "Rej"
            obj.request.save()
            obj.save()

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
            obj.request.renewal_status = "Can"
            obj.request.acceptance_status = "Acc"
            obj.acceptance_status = 'Acc'
            obj.request.date_expired = None
            obj.request.save()
            obj.save()

    accept.short_description = "تایید درخواست های لغو"

    def reject(self, request, queryset):
        for obj in queryset:
            obj.acceptance_status = 'Rej'
            obj.request.acceptance_status = "Rej"
            obj.request.save()
            obj.save()

    reject.short_description = "رد درخواست های لغو"


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
admin.site.unregister(Group)

admin.site.site_header = "پنل مدیریت پرتال"
admin.site.site_title = "پرتال درخواست مرکز پردازش های سریع دانشگاه شهید چمران اهواز"
admin.site.index_title = "پنل مدیریت"
