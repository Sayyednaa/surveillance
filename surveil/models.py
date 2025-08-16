from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN','Admin'),
        ('VIEWER','Viewer'),
        ('OWNER','Device Owner'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='OWNER')

    def __str__(self):
        return f"{self.user.username} ({self.role})"

def video_upload_path(instance, filename):
    base, ext = os.path.splitext(filename)
    return f"videos/device_{instance.device_id}/{timezone.now().strftime('%Y%m%d_%H%M%S')}{ext}"

class Device(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=100, default='My Phone')
    token = models.CharField(max_length=32, unique=True)
    is_online = models.BooleanField(default=False)
    recording_enabled = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} (owner={self.owner.username})"

class Recording(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recordings')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='recordings')
    file = models.FileField(upload_to=video_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)
    duration_ms = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Recording {self.id} from {self.device} at {self.created_at}"

class MotionEvent(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='motion_events')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='motion_events')
    timestamp = models.DateTimeField(default=timezone.now)
    magnitude = models.FloatField(default=0.0)
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Motion {self.magnitude:.2f} on {self.device} at {self.timestamp}"
