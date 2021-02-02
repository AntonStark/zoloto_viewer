"use strict";
console.debug('projectForm.js loaded');

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
function addDeleteFileField(fileName) {
    let field = document.createElement('input');
    field.hidden = true;
    field.name = ['delete', 'file', projectForm.childElementCount].join('_');
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
    0: function (fileDesc) {
        let td = document.createElement('td');
        let icon = document.createElement('i');
        icon.classList.add('fas', 'fa-bars');     // <i class="fas fa-bars"></i>
        td.append(icon);
        return td;
    },
    1: function(fileDesc) {
        let td = document.createElement('td');
        let input = document.createElement('input');
        input.type = 'text';
        input.name = 'floor_caption_' + btoa(fileDesc.name);
        input.value = fileDesc.name.split('.').slice(0, -1).join('.');
        td.append(input);
        return td;
    },
    2: function(fileDesc) {
        let td = document.createElement('td');
        td.append(fileDesc.name);
        return td;
    },
    3: function(fileDesc) {
        let td = document.createElement('td');
        td.append(fileDesc.lastModifiedDate);
        return td;
    },
    4: function(fileDesc) {
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
    5: function (fileDesc, extra) {
        let td = document.createElement('td');
        let input = document.createElement('input');
        input.type = 'text';
        input.name = 'floor_offset_' + btoa(fileDesc.name);
        input.classList.add('plan-row-offset-input', 'disabled');
        input.setAttribute('style', 'visibility: hidden;');
        input.value = String(extra.totalRows + 1 || 1);
        td.append(input);
        return td;
    }
};
function buildRow(fileDesc, cols, extra={}) {
    let tr = document.createElement('tr');
    tr.draggable = true;
    tr.id = String(extra.totalRows || 1);

    const cells = cols.map((i) => cellInit[i](fileDesc, extra));
    tr.append(...cells);
    return tr;
}

function collectPlanFileNames(planTable) {
    return [].map.call(planTable.children, row => row.children[1].textContent);
}
function onPlanFilesChange() {
    const files = this.files;
    console.log('plan', files);

    const planTableElement = document.getElementById('plan_table');
    const existingPlanNames = collectPlanFileNames(planTableElement);
    let rows = [];
    for (let i = 0; i < files.length; ++i) {
        const file = files[i];
        if (existingPlanNames.includes(file.name)) {
            alert('Файл с именем ' + file.name + ' уже существует.\n' +
                'При сохранении он будет заменён выбранным.')
        }
        else {
            const tr = buildRow(file, [0, 1, 2, 4, 5], {
                totalRows: planTableElement.childElementCount
            });
            tr.id = planTableElement.childElementCount;
            rows.push(tr);
        }
    }
    planTableElement.append(...rows);

    const planInputLabel = document.getElementById('plan_input_label');
    addMoreFileInput(planInputLabel);
}
document.getElementById('plan_input_1')
    .addEventListener('change', onPlanFilesChange);


function loadProjectFormValidator(e) {
    const planSelected = document.getElementById('plan_table').childElementCount;
    if (planSelected === 0) {
        alert('Добавление проекта невозможно\n' +
            'без указания названия проекта и\n' +
            'добавления пространств');
        e.preventDefault();
    }
}
if (projectForm.dataset.mode !== 'edit')
    projectForm.addEventListener('submit', loadProjectFormValidator);

function deleteFileHandler(filename, tr) {
    addDeleteFileField(filename);
    tr.remove();
}
