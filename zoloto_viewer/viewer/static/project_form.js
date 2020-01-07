"use strict";
console.debug('project_form.js loaded');

const projectNameInput = document.getElementById('project_name_input');
projectNameInput.addEventListener('input', function () {
    if (projectNameInput.validity.patternMismatch)
        projectNameInput.setCustomValidity('Bad character: a-zA-Z0-9_А-я- expected');
    else
        projectNameInput.setCustomValidity('');
});

const projectForm = document.getElementById('load_project_form');
function addIgnoreFileField(fileName) {
    let field = document.createElement('input');
    field.hidden = true;
    field.name = ['ignore', 'file', projectForm.childElementCount].join('_');
    field.type = 'text';
    field.value = fileName;
    projectForm.appendChild(field);
}

function addMoreFileInput(labelTag, options = {}) {
    let input = document.createElement('input');
    //  <input name="plan_files_1" id="plan_input_1" type="file" accept="image/*" multiple style="display: none">
    const kind = options.kind || 'plan';
    input.name = [kind, 'files', labelTag.childElementCount + 1].join('_');
    labelTag.htmlFor = input.id = [kind, 'input', labelTag.childElementCount + 1].join('_');
    input.type = options.type || 'file';
    input.accept = options.accept || 'image/*';
    input.multiple = (options.multiple !== undefined ? options.multiple : true);
    input.style = options.style || 'display: none';
    input.addEventListener('change', options.handler || onPlanFilesChange);
    labelTag.appendChild(input);
}

const cellInit = {
    0: function(fileDesc) {
        let td = document.createElement('td');
        let input = document.createElement('input');
        input.type = 'text';
        input.name = 'floor_caption_' + btoa(fileDesc.name);
        input.value = fileDesc.name.split('.').slice(0, -1).join('.');
        td.append(input);
        return td;
    },
    1: function(fileDesc) {
        let td = document.createElement('td');
        td.append(fileDesc.name);
        return td;
    },
    2: function(fileDesc) {
        let td = document.createElement('td');
        td.append(fileDesc.lastModifiedDate);
        return td;
    },
    3: function(fileDesc) {
        let td = document.createElement('td');
        let a = document.createElement('a');
        a.innerHTML = '&#x2A09';
        a.className = 'mark-delete';
        a.onclick = function() {
            const tr = td.parentNode;
            addIgnoreFileField(fileDesc.name);
            tr.remove();
        };
        td.append(a);
        return td;
    },
};
function buildRow(fileDesc, short= false) {
    let tr = document.createElement('tr');
    const cols = (short ? [1, 2, 3] : [0, 1, 3]);
    const cells = cols.map((i) => cellInit[i](fileDesc));
    tr.append(...cells);
    return tr;
}

function onPlanFilesChange() {
    const files = this.files;
    console.log('plan', files);

    let rows = [];
    for (let i = 0; i < files.length; ++i) {
        const tr = buildRow(files[i]);
        rows.push(tr);
    }
    const planTableElement = document.getElementById('plan_table');
    planTableElement.append(...rows);

    const planInputLabel = document.getElementById('plan_input_label');
    addMoreFileInput(planInputLabel);
}
document.getElementById('plan_input_1')
    .addEventListener('change', onPlanFilesChange);


function onCsvFilesChange() {
    const files = this.files;
    console.log('csv', files);

    let rows = [];
    for (let i = 0; i < files.length; ++i) {
        const tr = buildRow(files[i], true);
        rows.push(tr);
    }
    const csvTableElement = document.getElementById('csv_table');
    csvTableElement.append(...rows);

    const csvInputLabel = document.getElementById('csv_input_label');
    addMoreFileInput(csvInputLabel, {
        kind: 'csv',
        accept: 'text/csv',
        handler: onCsvFilesChange
    });
}
document.getElementById('csv_input_1')
    .addEventListener('change', onCsvFilesChange);

function loadProjectFormValidator(e) {
    const planSelected = document.getElementById('plan_table').childElementCount;
    const csvSelected = document.getElementById('csv_table').childElementCount;
    if (planSelected === 0 || csvSelected === 0) {
        alert('Добавление проекта невозможно\n' +
            'без указания названия проекта,\n' +
            'добавления пространств и таблиц');
        e.preventDefault();
    }
}
if (projectForm.dataset.mode !== 'edit')
    projectForm.addEventListener('submit', loadProjectFormValidator);
