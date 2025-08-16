from django.contrib import admin
from .models import Device, Recording, MotionEvent, UserProfile

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('id','name','owner','token','is_online','recording_enabled','last_seen')

@admin.register(Recording)
class RecAdmin(admin.ModelAdmin):
    list_display = ('id','device','owner','created_at','file')

@admin.register(MotionEvent)
class MotionAdmin(admin.ModelAdmin):
    list_display = ('id','device','owner','timestamp','magnitude')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user','role')
