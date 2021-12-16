function nameEditHandler(e) {
    const inputElem = e.currentTarget;
    const oldName = inputElem.dataset.name;
    const newName = inputElem.value;
    // if (newName === oldName) {
    //     return;
    // }

    const tableRow = inputElem.parentNode.parentNode;
    const siblingInput = Array.from(tableRow.getElementsByClassName('name-edit-input'))
        .filter((elem) => elem !== inputElem)[0];
    const otherLangElem = siblingInput;
    const otherLangName = siblingInput.value;
    const isRussianName = inputElem.classList.contains('name-ru');

    inputElem.disabled = true;

    if (newName.length === 0 && otherLangName.length !== 0) {
        inputElem.disabled = false;
        return;     // do nothing for now
    }
    else {
        const origRuName = ( isRussianName ? inputElem : otherLangElem ).dataset.name;
        const deleteConfirmation = confirm(`Удалить «${origRuName}»?`);
        console.log('deleteConfirmation', deleteConfirmation);
        if (!deleteConfirmation) {
            inputElem.value = inputElem.dataset.name;
            otherLangElem.value = otherLangElem.dataset.name;
            inputElem.disabled = false;
            return;
        }
        //   todo api call with deleteConfirmation (delete mode)
    }

    const newNameAlreadyUsed = Array.from(document.getElementsByClassName('name-edit-input'))
        .filter((elem) => elem !== inputElem).map((elem) => elem.value).includes(newName);

    if (isRussianName && newNameAlreadyUsed) {
        const unionConfirmation = confirm(`Заменить «${oldName}» на «${newName}»?`);
        console.log('unionConfirmation', unionConfirmation);
        if (!unionConfirmation) {
            inputElem.disabled = false;
        }
        //    todo api call with unionConfirmation (union mode)
    }
    //    todo api call (simple replace)

    // todo success handler: update inputElem.dataset.name and value and inputElem.disabled = false
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
