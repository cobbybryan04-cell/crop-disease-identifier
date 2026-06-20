// Image Preview for upload tab
const fileInput = document.getElementById('fileInput');
const previewImage = document.getElementById('previewImage');
const uploadText = document.getElementById('uploadText');
const form = document.getElementById('uploadForm');

if (fileInput) {
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewImage.style.display = 'block';
                uploadText.style.display = 'none';
            }
            reader.readAsDataURL(file);
        }
    });
}

if (form) {
    form.addEventListener('submit', function() {
        document.getElementById('loadingSpinner').style.display = 'flex';
    });
}

// Tab switching
function showTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    if (tab === 'upload') {
        document.getElementById('uploadTab').style.display = 'block';
        document.getElementById('cameraTab').style.display = 'none';
        document.querySelectorAll('.tab-btn')[0].classList.add('active');
    } else {
        document.getElementById('uploadTab').style.display = 'none';
        document.getElementById('cameraTab').style.display = 'block';
        document.querySelectorAll('.tab-btn')[1].classList.add('active');
    }
}

// Camera
let stream = null;
let capturedBlob = null;

async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        document.getElementById('video').srcObject = stream;
        document.getElementById('video').style.display = 'block';
        document.getElementById('captureBtn').style.display = 'inline-block';
        document.getElementById('startCameraBtn').style.display = 'none';
        document.getElementById('capturedImage').style.display = 'none';
    } catch(err) {
        alert('Camera not accessible: ' + err.message);
    }
}

function capturePhoto() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    canvas.toBlob(function(blob) {
        capturedBlob = blob;
        const url = URL.createObjectURL(blob);
        document.getElementById('capturedImage').src = url;
        document.getElementById('capturedImage').style.display = 'block';
        document.getElementById('video').style.display = 'none';
        document.getElementById('captureBtn').style.display = 'none';
        document.getElementById('retakeBtn').style.display = 'inline-block';

        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    }, 'image/jpeg');
}

function retakePhoto() {
    capturedBlob = null;
    document.getElementById('capturedImage').style.display = 'none';
    document.getElementById('retakeBtn').style.display = 'none';
    document.getElementById('startCameraBtn').style.display = 'inline-block';
    startCamera();
}

// Override form submit to handle camera blob
if (form) {
    form.addEventListener('submit', function(e) {
        const cameraTab = document.getElementById('cameraTab');
        if (cameraTab && cameraTab.style.display !== 'none' && capturedBlob) {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('file', capturedBlob, 'camera_capture.jpg');

            document.getElementById('loadingSpinner').style.display = 'flex';

            fetch('/upload', {
                method: 'POST',
                body: formData
            }).then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    return response.text().then(html => {
                        document.open();
                        document.write(html);
                        document.close();
                    });
                }
            }).catch(err => {
                alert('Upload failed: ' + err.message);
                document.getElementById('loadingSpinner').style.display = 'none';
            });
        } else {
            document.getElementById('loadingSpinner').style.display = 'flex';
        }
    });
}