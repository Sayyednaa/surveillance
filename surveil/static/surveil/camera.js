const preview = document.getElementById('preview');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const statusEl = document.getElementById('status');
const motionCanvas = document.getElementById('motionCanvas');
const ctx = motionCanvas.getContext('2d');

let mediaStream = null;
let recorder = null;
let chunks = [];
let recording = false;
let lastImageData = null;
let pollTimer = null;
let heartbeatTimer = null;

function setStatus(t){ statusEl.textContent = t; }

async function initCamera() {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: true });
    preview.srcObject = mediaStream;
    setStatus('Camera ready');
  } catch (e) {
    setStatus('Camera failed: ' + e.message);
  }
}

function startRecording() {
  if (!mediaStream) return;
  chunks = [];
  recorder = new MediaRecorder(mediaStream, { mimeType: 'video/webm' });
  const startedAt = Date.now();
  recorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };
  recorder.onstop = async () => {
    const blob = new Blob(chunks, { type: 'video/webm' });
    const fd = new FormData();
    fd.append('video', blob, 'recording.webm');
    fd.append('duration_ms', String(Date.now() - startedAt));
    try {
      const res = await fetch(`/api/upload/${TOKEN}/`, { method:'POST', body: fd });
      const data = await res.json();
      console.log('Uploaded', data);
      if (Notification && Notification.permission === 'granted') new Notification('Upload complete');
    } catch (e) {
      console.error('Upload failed', e);
    }
  };
  recorder.start();
  recording = true;
  setStatus('Recording…');
}

function stopRecording() {
  if (recorder && recording) {
    recorder.stop();
    recording = false;
    setStatus('Idle');
  }
}

async function pollStatus() {
  try {
    const res = await fetch(`/api/device/${TOKEN}/status/`);
    const data = await res.json();
    if (data.recording_enabled && !recording) startRecording();
    if (!data.recording_enabled && recording) stopRecording();
  } catch(e) { /* ignore */ }
}

async function heartbeat() {
  try { await fetch(`/api/heartbeat/${TOKEN}/`); } catch(e) {}
}

function analyzeMotion() {
  if (!mediaStream) return;
  const vw = preview.videoWidth || 320;
  const vh = preview.videoHeight || 240;
  motionCanvas.width = 160; // downscale for speed
  motionCanvas.height = Math.round(160 * vh / vw);
  ctx.drawImage(preview, 0, 0, motionCanvas.width, motionCanvas.height);
  const current = ctx.getImageData(0,0,motionCanvas.width, motionCanvas.height);
  if (lastImageData) {
    let diff = 0;
    for (let i=0; i<current.data.length; i+=4) {
      const d = Math.abs(current.data[i] - lastImageData.data[i]) +
                Math.abs(current.data[i+1] - lastImageData.data[i+1]) +
                Math.abs(current.data[i+2] - lastImageData.data[i+2]);
      if (d > 60) diff++;
    }
    const magnitude = diff / (current.data.length/4);
    if (magnitude > 0.05) { // basic threshold
      notifyMotion(magnitude);
      if (!recording) startRecording();
    }
  }
  lastImageData = current;
  requestAnimationFrame(analyzeMotion);
}

async function notifyMotion(mag) {
  try {
    await fetch(`/api/motion/${TOKEN}/`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ magnitude: mag }) });
  } catch(e) {}
}

function trackLocation() {
  if (!navigator.geolocation) return;
  navigator.geolocation.watchPosition(async (pos) => {
    const { latitude, longitude } = pos.coords;
    try {
      await fetch(`/api/device/${TOKEN}/location/`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ lat: latitude, lon: longitude }) });
    } catch(e) {}
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  await initCamera();
  analyzeMotion();
  trackLocation();
  if (window.Notification && Notification.permission !== 'granted') Notification.requestPermission();
  startBtn.addEventListener('click', startRecording);
  stopBtn.addEventListener('click', stopRecording);
  pollTimer = setInterval(pollStatus, 2000);
  heartbeatTimer = setInterval(heartbeat, 5000);
});
