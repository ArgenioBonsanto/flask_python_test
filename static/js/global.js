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
    if (document.getElementById("uploadFile").classList.contains("disabled")) {
        return;
    }
    document.getElementById("spinner").classList.remove("d-none");
    document.getElementById("documents").innerHTML = "";
    document.getElementById("results").innerHTML = "";
    document.getElementById("uploadFile").classList.add("disabled");

    const formData = new FormData(this);
    const modelSelect = document.getElementById('modelSelect').value;

    formData.append('modelSelect', modelSelect);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        doc_id = ""
        first = true;
        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                document.getElementById("uploadFile").classList.remove("disabled");
                document.getElementById("spinner").classList.add("d-none");
                break;
            }
            const textChunk = decoder.decode(value, { stream: true });
            try {
                const textChunkJson = JSON.parse(textChunk);

                if ('error' in textChunkJson) {
                    putError(textChunkJson.error);
                    document.getElementById("uploadFile").classList.remove("disabled");
                    document.getElementById("spinner").classList.add("d-none");
                    break;
                }
                
                for (const i in textChunkJson) {
                    const data = textChunkJson[i];

                    if (data.doc_id != doc_id) {

                        doc_id = data.doc_id;
                        const card = createTableDetails(data.others.total_pages, data.others.name, doc_id);
                        document.getElementById("documents").appendChild(card);
                        originalTable = document.getElementById("tableResults");
                        tableResults = originalTable.cloneNode(true);
                        tableResults.id = "tableResults_" + doc_id;
                        
                        document.getElementById("results").appendChild(tableResults);
                        if(first){
                            tableResults.classList.remove("d-none");
                            card.click();
                            first = false;
                        }
                    }
                    
                    const tr = document.createElement('tr');

                    if(data.analysis_context.length > 0) {
                        tr.classList.add('table-warning', 'd-flex');
                    } else {
                        tr.classList.add('d-flex');
                    }

                    // Page Number
                    createTd(tr, data.page, 'col-1');
                    // Summary
                    createTd(tr, data.summary, 'col-4');
                    // Timeline
                    createTdTimeline(tr, data.timeline, 'col-4');
                    // low confidence words
                    createTd(tr, data.analysis_context, 'col-3');
                    document.getElementById("tableResults_" + doc_id).querySelector("#tableBody").appendChild(tr);
                }
            } catch (e) {
                putError(textChunk);
            }
        }
    } catch (error) {
         putError(error);
    }
});

$(document).on("click",".card-documents",function (){
    id = $(this).attr("id")
    $(".tables").addClass("d-none")
    $("#tableResults_" + id).removeClass("d-none")
})

function putError(textChunk){
    const tr = createError(textChunk);
    originalTable = document.getElementById("tableResults");
    tableError = originalTable.cloneNode(true);
    tableError.classList.remove("d-none");
    tableError.querySelector("#tableBody").appendChild(tr);
    document.getElementById("results").appendChild(tableError);
}

function createTableDetails(totalPages, name, doc_id) {
    const table = document.createElement('table');
    table.className = 'table table-sm table-bordered mt-2 card-documents';
    table.style.cursor = 'pointer';
    table.id = doc_id;
    table.onclick = function() {
        document.querySelectorAll('#documents table').forEach(t => t.classList.remove('selected-table'));
        this.classList.add('selected-table');
    };
    
    trPage = createTrDetails("extra-num-pages", totalPages, "Total Pages:")
    trName = createTrDetails("extra-name", name, "ID:")
    const tbody = document.createElement('tbody');
    tbody.appendChild(trName);
    tbody.appendChild(trPage);
    table.appendChild(tbody);
    
    return table;
}

function createTrDetails(id, name, title){
    const tr = document.createElement('tr');
    tr.className = 'd-flex';
    const th = document.createElement('th');
    th.className = 'col-6';
    th.textContent = title;
    const td = document.createElement('td');
    td.className = 'col-6';
    td.id = id;
    td.textContent = name;
    tr.appendChild(th);
    tr.appendChild(td);
    return tr;
}

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