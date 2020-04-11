from django.contrib import admin
from django.contrib.auth.models import Group
from .models import *


class ProfileA(admin.ModelAdmin):
    date_hierarchy = 'user__date_joined'
    list_display = ('get_user_full_name', 'university', 'field', 'guidance_master_full_name')
    list_filter = ('field', 'university')
    search_fields = ['user__first_name', 'user__last_name']
    fieldsets = (
        ('اطلاعات دانشگاهی', {'fields': ('user', 'university', 'field')}),
        ('اطلاعات استاد راهنما', {'fields': ('guidance_master_full_name', 'guidance_master_email')}),
    )

    def get_user_full_name(self, obj):
        return obj.user.get_full_name()

    get_user_full_name.short_description = 'نام و نام خانوادگی'
    get_user_full_name.admin_order_field = 'user__last_name'


class RequestA(admin.ModelAdmin):
    date_hierarchy = 'date_requested'
    readonly_fields = ('date_requested', 'date_expired', 'serial_number', 'show_cost', 'user')
    list_display = ('get_user_full_name', 'serial_number', 'acceptance_status', 'renewal_status')
    list_filter = ('date_expired', 'acceptance_status', 'renewal_status', 'os')
    search_fields = ['serial_number', 'user__user__first_name', 'user__user__last_name']
    fieldsets = (
        ('اطلاعات کاربر', {'fields': ('user',)}),
        ('جزئیات زمانی درخواست', {'fields': ('date_requested', 'date_expired', 'days')}),
        ('جزئیات فنی درخواست', {'fields': ('cpu', 'ram', 'disk', 'app_name')}),
        ('جزئیات مالی درخواست', {'fields': ('show_cost',)}),
        ('توضیحات', {'fields': ('description',)}),
        ('وضعیت درخواست', {'fields': ('acceptance_status', 'renewal_status')}),
    )

    def get_user_full_name(self, obj):
        return obj.user.user.get_full_name()

    get_user_full_name.short_description = 'نام و نام خانوادگی'
    get_user_full_name.admin_order_field = 'user__last_name'

    actions = ["accept", "reject", "normal", "cancel", "suspend"]

    def accept(self, request, queryset):
        queryset.update(acceptance_status='Acc')

    def reject(self, request, queryset):
        queryset.update(acceptance_status='Rej')

    def normal(self, request, queryset):
        queryset.update(renewal_status='Ok')

    def cancel(self, request, queryset):
        queryset.update(renewal_status='Can')

    def suspend(self, request, queryset):
        queryset.update(renewal_status='Sus')


admin.site.register(Profile, ProfileA)
admin.site.register(Request, RequestA)
admin.site.unregister(Group)

admin.site.site_header = "پنل مدیریت پرتال"
admin.site.site_title = "پرتال درخواست مرکز پردازش های سریع دانشگاه شهید چمران اهواز"
admin.site.index_title = "پنل مدیریت"
