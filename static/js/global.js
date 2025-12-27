document.getElementById('customFile').addEventListener("change", function() {
    var fileName = this.value.split("\\").pop();
    var label = this.nextElementSibling;
    if(label && label.classList.contains("custom-file-label")){
        label.classList.add("selected");
        label.innerHTML = fileName;
    }
});

    
document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const spinner = document.getElementById('spinner');
    const tableBody = document.getElementById('tableBody');
    const formData = new FormData(this);
    const modelSelect = document.getElementById('modelSelect').value;
    
    spinner.classList.remove('d-none');

    formData.append('modelSelect', modelSelect);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                spinner.classList.add('d-none');
                break;
            }
            const textChunk = decoder.decode(value, { stream: true });
            try {
                const textChunkJson = JSON.parse(textChunk);

                if ('error' in textChunkJson) {
                    const tr = createError(textChunkJson.error);
                    tableBody.appendChild(tr);
                    spinner.classList.add('d-none');
                    break;
                }
                

                for (const i in textChunkJson) {
                    const data = textChunkJson[i];
                    document.getElementById("extra-num-pages").textContent = data.others.total_pages;
                    document.getElementById("extra-width").textContent = data.others.width;
                    document.getElementById("extra-height").textContent = data.others.height;
                    document.getElementById("extra-unit").textContent = data.others.unit;
                    const tr = document.createElement('tr');
                    tr.classList.add('d-flex');
    
                    // Page Number
                    createTd(tr, data.page, 'col-1');
    
                    // Summary
                    createTd(tr, data.summary, 'col-4');

                    // Timeline
                    createTdTimeline(tr, data.timeline, 'col-4');
    
                    // low confidence words
                    createTdArray(tr, data.others.confidence, 'col-3');

                    tableBody.appendChild(tr);
                }
                window.scrollTo(0, document.body.scrollHeight);
            } catch (e) {
                const tr = createError(textChunk);
                tableBody.appendChild(tr);
                spinner.classList.add('d-none');
            }
        }
    } catch (error) {
        const tr = createError(error.message || error);
        tableBody.appendChild(tr);
        spinner.classList.add('d-none');
    }
});

function createTd(tr, data, col){
    const td = document.createElement('td');
    td.classList.add(col, 'text-justify');
    td.textContent = data;
    tr.appendChild(td);
}

function createTdArray(tr, data, col){
    const td = document.createElement('td');
    td.classList.add(col, 'text-justify');
    const ul = document.createElement('ul');
    data.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        ul.appendChild(li);
    });
    td.appendChild(ul);
    tr.appendChild(td);
}

function createTdTimeline(tr, data, col){
    const td = document.createElement('td');
    td.classList.add(col, 'text-justify');
    const ul = document.createElement('ul');
    for (const [key, value] of Object.entries(data)) {
        const li = document.createElement('li');
        li.textContent = `${key} - ${value}`;
        ul.appendChild(li);
    }
    td.appendChild(ul);
    tr.appendChild(td);
}

function createError(error){
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.className = 'col-12';
    td.appendChild(getErrorHtml(error));
    tr.appendChild(td);
    return tr;
}

function getErrorHtml(error) {
    const row = document.createElement('div');
    row.classList.add('row', 'justify-content-center');

    const col = document.createElement('div');
    col.classList.add('col-md-8');

    const alert = document.createElement('div');
    alert.classList.add('alert', 'alert-danger');
    alert.setAttribute('role', 'alert');

    const h4 = document.createElement('h4');
    h4.classList.add('alert-heading');
    h4.textContent = 'An error occurred!';

    const pError = document.createElement('p');
    pError.textContent = error;

    const hr = document.createElement('hr');

    const pFooter = document.createElement('p');
    pFooter.classList.add('mb-0');
    pFooter.textContent = 'Please try again or contact support if the problem persists.';

    alert.appendChild(h4);
    alert.appendChild(pError);
    alert.appendChild(hr);
    alert.appendChild(pFooter);

    col.appendChild(alert);
    row.appendChild(col);

    return row;
}