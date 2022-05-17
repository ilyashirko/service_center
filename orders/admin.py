from django.contrib import admin

from .models import (Customer, Device, DeviceType, Feedback, Master, Message, Order, Request, Support,
                     TelegramId)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    raw_id_fields = ("devices",)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    pass


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    pass


@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'patronymic', 'phonenumber')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(TelegramId)
class TelegramIdAdmin(admin.ModelAdmin):
    pass

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'first_name', 'user_name', 'phone', 'created_at', 'processed', 'request')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('request', 'is_master', 'text')

@admin.register(Support)
class SupportAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'telegram_id', 'processed', 'request', 'response')