document.getElementById('customFile').addEventListener("change", function() {
    var fileName = this.value.split("\\").pop();
    var label = this.nextElementSibling;
    if(label && label.classList.contains("custom-file-label")){
        label.classList.add("selected");
        label.innerHTML = fileName;
    }
});

    
document.getElementById('uploadForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const spinner = document.getElementById('spinner');
    spinner.classList.remove('d-none');

    const formData = new FormData(this);
    const modelSelect = document.getElementById('modelSelect').value;
    formData.append('modelSelect', modelSelect);

    const results = document.getElementById('results');
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(html => {
        results.innerHTML = html;
        spinner.classList.add('d-none');
    })
    .catch(error => {
        results.innerHTML = "Error: " + error;
        spinner.classList.add('d-none');
    });
    
});