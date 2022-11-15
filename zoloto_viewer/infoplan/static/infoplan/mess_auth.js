'use strict';

// RENDER

const INFOPLAN_SIDE_LABELS_USUAL = {
    1: 'Сторона A',
    2: 'Сторона B',
    3: 'Сторона C',
    4: 'Сторона D',
}

const INFOPLAN_SIDE_LABELS_FINGERPOST = {
    1: 'Лопасть 1',
    2: 'Лопасть 2',
    3: 'Лопасть 3',
    4: 'Лопасть 4',
    5: 'Лопасть 5',
    6: 'Лопасть 6',
    7: 'Лопасть 7',
    8: 'Лопасть 8',
}

function buildMessBox(data) {
    function buildInfoplanBlock(data) {
        const isFingerPostMarker = data.layer.kind.name === 'фингерпост';
        const markerElem = messageBoxManager.getMarker(data.marker);
        if (isFingerPostMarker && !markerElem) {
            alert('Ошибка при отображении инфоплана.\n' +
                'Попробуйте обновить страницу или обратитесь к администратору.');
        }
        function paneEnabled(paneN)
        { return markerElem.classList.contains(`pane-${paneN}`); }

        function buildSideNBlock(nSide, totalSideCount) {
            function buildSideHeaderUsual(data) {
                const sideLabels = INFOPLAN_SIDE_LABELS_USUAL;

                let sideLabel = document.createElement('div');

                let span = document.createElement('span');
                span.setAttribute('style', 'font-size: 10px;');
                if (totalSideCount !== 1) {
                    span.textContent = sideLabels[nSide];
                }

                sideLabel.append(span);
                return sideLabel;
            }
            function buildSideHeaderFingerpost(data) {
                const sideLabels = INFOPLAN_SIDE_LABELS_FINGERPOST;

                let sideLabel = document.createElement('div');

                let checkbox = document.createElement('input');
                checkbox.setAttribute('type', 'checkbox');
                checkbox.setAttribute('class', 'side_label__checkbox');
                checkbox.dataset['pane_number'] = nSide;
                checkbox.dataset['marker'] = data.marker;
                checkbox.checked = paneEnabled(nSide);
                checkbox.addEventListener('change', fingerpostPaneCheckboxChange);

                const text = document.createTextNode(sideLabels[nSide]);

                let label = document.createElement('label');
                label.setAttribute('style', 'font-size: 12px;');
                label.append(checkbox, text);
                sideLabel.append(label);
                return sideLabel;
            }
            function buildSideBlock(data) {
                const infoplanBySide = Object.fromEntries(
                    data.infoplan.map(sideObj => [sideObj.side, sideObj.variables])
                )
                const sideVars = infoplanBySide[nSide];

                let sideBlock = document.createElement('div');
                sideBlock.setAttribute('class', 'variables-container-side-block')

                let sideHeader = ( isFingerPostMarker
                    ? buildSideHeaderFingerpost(data) : buildSideHeaderUsual(data));

                let sideInput = document.createElement('textarea');
                sideInput.setAttribute('class', 'variables-container-side-input')
                sideInput.setAttribute('data-number', nSide);
                sideInput.setAttribute('rows', 8);

                function htmlDecode(input) {
                    var doc = new DOMParser().parseFromString(input, 'text/html');
                    return doc.documentElement.textContent;
                }

                // noinspection UnnecessaryLocalVariableJS
                const inputValue = ( sideVars ? sideVars.join(';\n') + ';' : '');
                sideInput.value = htmlDecode(inputValue);
                sideInput.addEventListener('blur', variablesContainerBlur);

                sideBlock.append(sideHeader, sideInput);
                return sideBlock;
            }
            return buildSideBlock;
        }

        const sides = data.layer.kind.sides;

        let infoplanHeader = document.createElement('div');
        let variablesLabel = document.createElement('span');
        variablesLabel.setAttribute('style', 'font-size: 10px;');
        variablesLabel.textContent = ( data.marker ? 'Инфоплан' : 'Инфоплан нескольких');
        let numberLabel = document.createElement('span');
        // numberLabel.style.float = 'right';
        numberLabel.style.marginLeft = '10px';
        numberLabel.style.fontSize = '10px';
        numberLabel.style.fontWeight = 'bold';
        numberLabel.textContent = data.number;
        let closeBtn = document.createElement('span');
        closeBtn.style.float = 'right';
        closeBtn.textContent = 'x';
        closeBtn.addEventListener('click', function () {
            const markersUidArray = data.markers || data.marker;
            messageBoxManager.drop(markersUidArray);
        })
        infoplanHeader.append(variablesLabel, numberLabel, closeBtn);

        let variablesDiv  = document.createElement('div');
        variablesDiv.setAttribute('class', `variables_container`);
        variablesDiv.style.gridTemplateColumns = ( isFingerPostMarker
            ? `repeat(4, 1fr)`
            : `repeat(${sides}, 1fr)`
        );

        const sideNumbers = Array.from(Array(sides));
        variablesDiv.append(...sideNumbers.map((e, i) => buildSideNBlock(i + 1, sides)(data)));

        let infoplanDiv  = document.createElement('div');
        infoplanDiv.append(infoplanHeader, variablesDiv);

        return infoplanDiv;
    }
    function buildCommentBlock(data) {
        function buildCommentBlock(cObj) {
            const comment = cObj.content;
            let commentBlock = document.createElement('div');
            commentBlock.textContent = comment;
            if (cObj.resolved) commentBlock.setAttribute('style', 'color: lightgrey;');
            return commentBlock;
        }
        const [hasComment, comments] = [data.has_comment, data.comments];

        let commentLabel = document.createElement('span');
        commentLabel.setAttribute('style', 'font-size: 10px;');
        commentLabel.textContent = ( hasComment ? 'Комментарии' : 'Комментариев нет');

        let commentsBlock = document.createElement('div');
        commentsBlock.setAttribute('class', 'comment_field');
        commentsBlock.append(...comments.map(c => buildCommentBlock(c)))

        let commentDiv = document.createElement('div');
        commentDiv.append(commentLabel, commentsBlock);
        return commentDiv;
    }
    function buildResolveBtn(data) {
        const markerUid = data.marker;
        const hasComment = data.has_comment;
        const comments_resolved = data.comments_resolved;

        let btnLink = document.createElement('a');
        if (!hasComment || comments_resolved) return btnLink;

        btnLink.classList.add('fill-button', 'noselect')
        btnLink.setAttribute('style', 'width: fit-content; margin-bottom: 6px;')
        btnLink.textContent = 'Все учтены';
        btnLink.addEventListener('click', () => handlerResolveCommentsBtnClick(markerUid));
        return btnLink;
    }
    function buildSaveBtn(data) {
        const markerUid = data.marker;
        const markersUidArray = data.markers;

        let btnLink = document.createElement('a');
        btnLink.setAttribute('class', 'message_confirm_btn');
        if (markerUid) {
            btnLink.textContent = 'Сохранить';
            btnLink.addEventListener('click', () => handlerConfirmBtnClick(markerUid));
        } else if (markersUidArray) {
            btnLink.textContent = 'Сохранить несколько';
            btnLink.addEventListener('click', () => handleConfirmBtnManyClick(markersUidArray));
        }
        return btnLink;
    }

    const boxDiv = document.createElement('div');
    boxDiv.setAttribute('class', 'message_box');
    boxDiv.addEventListener('keyup', function (e) {e.stopPropagation();})
    boxDiv.append(
        buildInfoplanBlock(data),
        buildCommentBlock(data),
        buildResolveBtn(data),
        buildSaveBtn(data)
    );
    return boxDiv;
}

// HANDLERS

function variablesContainerBlur(e) {
    let v = e.target.value;
    if (v.length > 0
        && !( v.endsWith(';') || v.endsWith('\n') )
    ) {
        v = v + ';\n';
        e.target.value = v;
    }
}

function fingerpostPaneCheckboxChange(e) {
    const {marker, pane_number} = e.currentTarget.dataset
    const checked = e.currentTarget.checked

    const markerElem = messageBoxManager.getMarker(marker);
    if (markerElem) {
        markerElem.classList.toggle(`pane-${pane_number}`, checked);
    }
}

function handlerResolveCommentsBtnClick(marker_uid) {
    doApiCall(
        'POST',
        API_MARKER_RESOLVE_CMS(marker_uid),
        null,
        (markerData) => {
            const markerUid = markerData.marker;
            markerCirclesManager.sync(markerData);
            messageBoxManager.deleteMessage(markerUid);
            refreshMarkerElement(markerData);
        },
        (rep) => {console.log(rep);},
    );
}

function parseSideVariables(sideInputValue) {
    if (sideInputValue.endsWith(';\n')) {
        sideInputValue = sideInputValue.slice(0, -2);
    } else if (sideInputValue.endsWith(';')) {
        sideInputValue = sideInputValue.slice(0, -1);
    }

    // noinspection UnnecessaryLocalVariableJS
    const sideVars = sideInputValue.split(';\n');
    return sideVars;
}
function parseFingerpostMetadata(messContainer) {
    if (!messContainer) {
        return null;
    }
    const paneCheckboxElements = messContainer.getElementsByClassName('side_label__checkbox');
    if (paneCheckboxElements.length === 0) {
        return null;
    }

    return {
        'panes': Array.from(paneCheckboxElements).map((elem) => ({
            'pane_number': elem.dataset['pane_number'],
            'enabled': elem.checked,
        }))
    }
}

function handlerConfirmBtnClick(marker_uid) {
    const box = messageBoxManager.get(marker_uid);
    if (!box) return;
    console.debug('btnSave box', box);

    const sides = box.getElementsByClassName('variables-container-side-input');
    let sideObjects = [];
    for (const s of sides) {
        sideObjects.push({
            side: Number(s.dataset.number),
            variables: parseSideVariables(s.value)
        })
    }

    const payload = {
        infoplan: sideObjects,
        fingerpost_metadata: parseFingerpostMetadata(box)
    }
    doApiCall('PUT',
        API_MARKER_PUT_VARS(marker_uid),
        payload,
        function onSuccessLoadReview(markerData) {
            const markerUid = markerData.marker;
            messageBoxManager.drop(markerUid);
            refreshMarkerElement(markerData);
        },
        function onErrorLoadReview(rep) {
            console.log(rep);
            alert('Возникла ошибка при сохранении.\nПопробуйте чуть позже или обратитесь к администратору.');
        }
    );
}

function handleConfirmBtnManyClick(markersUidArray) {
    const box = messageBoxManager.get(markersUidArray);
    if (!box) return;
    console.debug('btnSave box', box);

    const sides = box.getElementsByClassName('variables-container-side-input');
    let sideObjects = [];
    for (const s of sides) {
        sideObjects.push({
            side: Number(s.dataset.number),
            variables: parseSideVariables(s.value)
        })
    }

    const payload = {
        infoplan: sideObjects,
        markers: markersUidArray,
    }
    doApiCall('POST', API_MARKER_SUBMIT_DATA_MANY, payload,
        function (markersData) {
            messageBoxManager.drop(markersUidArray);
        },
        function onErrorLoadReview(rep) {
            console.log(rep);
            alert('Возникла ошибка при сохранении.\nПопробуйте чуть позже или обратитесь к администратору.');
        }
    );
}

const handlerMessBlur = handlerConfirmBtnClick;
