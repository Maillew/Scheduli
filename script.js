// script.js
const dropArea = document.getElementById('drop-area');
const fileInput = document.getElementById('fileInput');
const result = document.getElementById('result');

dropArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropArea.classList.add('highlight');
});

dropArea.addEventListener('dragleave', () => {
    dropArea.classList.remove('highlight');
});

dropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    dropArea.classList.remove('highlight');

    const file = e.dataTransfer.files[0];
    fileInput.files = e.dataTransfer.files;

    // Submit the form to the Flask server
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Redirect to the upload.html page
        window.location.href = data.url;
    });
});

fileInput.addEventListener('change', () => {
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        window.location.href = data.url;
    });
});
///////////////////////

