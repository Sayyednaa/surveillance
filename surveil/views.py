import io, random, string
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.conf import settings
import qrcode
from .models import Device, Recording, MotionEvent, UserProfile
from .forms import RegisterForm, ProfileForm

def _gen_token(n=24):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # default profile
            UserProfile.objects.create(user=user, role='OWNER')
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    # Simple role check: viewers can view, owners can control their devices
    devices = Device.objects.filter(owner=request.user)
    recents = Recording.objects.filter(owner=request.user).order_by('-created_at')[:10]
    motions = MotionEvent.objects.filter(owner=request.user).order_by('-timestamp')[:10]
    return render(request, 'dashboard.html', {
        'devices': devices,
        'recents': recents,
        'motions': motions,
    })

def camera_mode(request, token):
    device = get_object_or_404(Device, token=token)
    # Anyone with the token URL (paired) can open camera on that phone.
    return render(request, 'camera.html', {'device': device})

@login_required
def video_gallery(request):
    recordings = Recording.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'videos.html', {'recordings': recordings})

@login_required
def device_pair(request):
    # Create or reuse a device token
    if request.method == 'POST':
        name = request.POST.get('name') or 'My Phone'
        token = _gen_token()
        device = Device.objects.create(owner=request.user, name=name, token=token)
    else:
        # show a QR for an existing or new token placeholder (not creating DB row yet)
        token = _gen_token()
        device = None

    # QR encodes the camera URL
    url = request.build_absolute_uri(f"/camera/{token}/")
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    # If we didn't create the device yet, store token in session to claim on first visit
    request.session['pair_token'] = token
    return HttpResponse(buf.getvalue(), content_type='image/png')

# ---------- APIs used by mobile page ----------

@csrf_exempt
def api_heartbeat(request, token):
    try:
        device = Device.objects.get(token=token)
    except Device.DoesNotExist:
        # First-time visit with session token -> create device on the fly
        session_token = request.session.get('pair_token')
        if session_token == token and request.user.is_authenticated:
            device = Device.objects.create(owner=request.user, name='My Phone', token=token)
        else:
            return JsonResponse({'error':'Unknown device'}, status=404)
    device.is_online = True
    device.last_seen = timezone.now()
    device.save(update_fields=['is_online','last_seen'])
    return JsonResponse({'ok': True})

@csrf_exempt
def api_device_status(request, token):
    device = get_object_or_404(Device, token=token)
    return JsonResponse({'recording_enabled': device.recording_enabled})

@csrf_exempt
def api_device_location(request, token):
    device = get_object_or_404(Device, token=token)
    if request.method == 'POST':
        import json
        data = json.loads(request.body or '{}')
        device.latitude = data.get('lat')
        device.longitude = data.get('lon')
        device.save(update_fields=['latitude','longitude'])
        return JsonResponse({'ok': True})
    return JsonResponse({'lat': device.latitude, 'lon': device.longitude})

@csrf_exempt
def api_upload(request, token):
    device = get_object_or_404(Device, token=token)
    if request.method == 'POST':
        f = request.FILES.get('video')
        duration = int(request.POST.get('duration_ms','0') or 0)
        if not f:
            return JsonResponse({'error':'no file'}, status=400)
        rec = Recording.objects.create(owner=device.owner, device=device, file=f, duration_ms=duration)
        return JsonResponse({'ok': True, 'id': rec.id, 'url': rec.file.url})
    return JsonResponse({'error':'POST required'}, status=405)

@csrf_exempt
def api_motion_event(request, token):
    device = get_object_or_404(Device, token=token)
    if request.method == 'POST':
        import json
        data = json.loads(request.body or '{}')
        magnitude = float(data.get('magnitude', 0))
        MotionEvent.objects.create(owner=device.owner, device=device, magnitude=magnitude, note=data.get('note',''))
        # email alert
        try:
            send_mail(
                subject='Motion detected',
                message=f'Motion {magnitude:.2f} detected on device {device.name} at {timezone.now()}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[device.owner.email] if device.owner.email else [],
                fail_silently=True
            )
        except Exception:
            pass
        return JsonResponse({'ok': True})
    return JsonResponse({'error':'POST required'}, status=405)

@login_required
def api_toggle_recording(request, device_id):
    device = get_object_or_404(Device, id=device_id, owner=request.user)
    device.recording_enabled = not device.recording_enabled
    device.save(update_fields=['recording_enabled'])
    return JsonResponse({'recording_enabled': device.recording_enabled})
