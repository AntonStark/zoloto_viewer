// API
const API_POST_REPLACE_VAR = `${BASE_URL}/viewer/project/${projectId}/docs/edit_names_api/`

function doApiCall(method, url, data, onResponse, onError=undefined) {
    let req = new XMLHttpRequest();
    req.open(method, url);

    req.onreadystatechange = function() {
        if (req.readyState === XMLHttpRequest.DONE) {
            if (req.status === 200) {
                const rep = JSON.parse(req.responseText);
                if (onResponse) {
                    onResponse(rep);
                }
            } else if (onError) {
                onError(req);
            }
            else {
                console.error(method, url, 'status=', req.status, req);
            }
        }
    };

    req.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    req.send(JSON.stringify(data));
}

function postApiCallVarReplace(ruPair, enPair, varIdsHint, confirmations, onSuccess, onError=undefined) {
    const payload = {
        replace_ru: {
            name_old: ruPair[0],
            name_new: ruPair[1],
        },
        replace_en: {
            name_old: enPair[0],
            name_new: enPair[1],
        },
        var_ids_hint: varIdsHint,
        confirmations
    }
    return doApiCall('POST', API_POST_REPLACE_VAR, payload, onSuccess, onError);
}

// UI

function nameEditHandler(e) {
    const inputElem = e.currentTarget;
    const oldName = inputElem.dataset.name;
    const newName = inputElem.value;

    const tableRow = inputElem.parentNode.parentNode;
    const siblingInput = Array.from(tableRow.getElementsByClassName('name-edit-input'))
        .filter((elem) => elem !== inputElem)[0];
    const otherLangElem = siblingInput;
    const otherLangName = siblingInput.value;
    const isRussianName = inputElem.classList.contains('name-ru');
    const newNameRu = (isRussianName ? newName : otherLangName);
    const varIdsHint = tableRow.dataset.varIds;

    function isRowSameRu(row) {
        const inputLangRu = row.getElementsByClassName('name-ru')[0];
        return inputLangRu.value === newNameRu;
    }
    const rowsSameRu = Array.from(document.getElementsByClassName('name-edit-input-row'))
        .filter((row) => isRowSameRu(row));

    otherLangElem.disabled = inputElem.disabled = true;
    function withRelease() {
        otherLangElem.disabled = inputElem.disabled = false;
    }

    function onSuccess(rep) {
        // случай обычной замены
        if (rep.status === 'success') {
            if (rep.mode === 'replace') {
                const resultName = ( isRussianName ? rep.result.ru : rep.result.en );
                inputElem.dataset.name = resultName;
                inputElem.value = resultName;
                return withRelease();
            }
        // в случая объединения и удаления оставляем строку disabled
        }
        else {
            alert('Возникла ошибка\n' + rep.msg);
        }
    }

    if (newName.length === 0) {
        if (otherLangName.length !== 0) {
            return withRelease();   // do nothing for now
        }
        else {
            const origRuName = ( isRussianName ? inputElem : otherLangElem ).dataset.name;
            const deleteConfirmation = confirm(`Удалить «${origRuName}»?`);
            console.log('deleteConfirmation', deleteConfirmation);
            if (!deleteConfirmation) {
                inputElem.value = inputElem.dataset.name;
                otherLangElem.value = otherLangElem.dataset.name;
                return withRelease();
            }
            const origEnName = ( isRussianName ? otherLangElem : inputElem ).dataset.name;

            // api call with deleteConfirmation (delete mode)
            postApiCallVarReplace([origRuName, ''], [origEnName, ''], varIdsHint,
                {delete: true}, onSuccess);
        }
    } else if (isRussianName && rowsSameRu.length > 0) {
        if (newName === oldName) {
            return withRelease();
        }

        const unionConfirmation = confirm(`Заменить «${oldName}» на «${newName}»?`);
        console.log('unionConfirmation', unionConfirmation);
        if (!unionConfirmation) {
            return withRelease();
        }

        const origEnName = otherLangElem.dataset.name;
        const newEnglishFromExisting = rowsSameRu[0].getElementsByClassName('name-en')[0].value;
        // api call with unionConfirmation (union mode)
        postApiCallVarReplace([oldName, newName], [origEnName, newEnglishFromExisting], varIdsHint,
            {union: true}, onSuccess);
    } else {
        if (newName === oldName) {
            return withRelease();
        }

        // api call (simple replace)
        const oneLangPair = [oldName, newName];
        const otherLangPair = [otherLangElem.dataset.name, otherLangElem.value];
        const [ruPair, enPair] = (isRussianName ? [oneLangPair, otherLangPair] : [otherLangPair, oneLangPair]);
        postApiCallVarReplace(ruPair, enPair, varIdsHint, {}, onSuccess);
    }
}

function keyPressHandler(e) {
    if (e.key === 'Escape' || e.key === 'Enter') {
        e.stopPropagation();
        e.currentTarget.blur();
    }
}

for (inputElem of document.getElementsByClassName('name-edit-input')) {
    inputElem.addEventListener('blur', nameEditHandler);
    inputElem.addEventListener('keyup', keyPressHandler);
}
