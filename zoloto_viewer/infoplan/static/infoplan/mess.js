"use strict";

// STARTER

function makeDataRequest(markerUid, onResponse, onError=undefined) {
    doApiCall('GET',
        API_MARKER_GET_DATA_PRETTY(markerUid),
        undefined,
        onResponse,
        onError
    );
}

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
    function buildHeader(data) {
        const markerNumber = data.number;
        let header = document.createElement('div');
        header.textContent = markerNumber;
        return header;
    }
    function buildInfoplanBlock(data) {
        const isFingerPostMarker = data.layer.kind.name === 'фингерпост';
        const markerElem = messageBoxManager.getMarker(data.marker);
        if (!markerElem) {
            alert('Ошибка при отображении инфоплана.\n' +
                'Поробуйте обновить страницу или обратитесь к администратору.');
        }
        const markerClassList = markerElem.classList;
        function paneEnabled(paneN)
        { return markerClassList.contains(`pane-${paneN}`); }

        function buildSideNBlock(nSide) {
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

                let span = document.createElement('span');
                span.setAttribute('style', 'font-size: 10px;');
                span.textContent = sideLabels[nSide];

                sideLabel.append(span);
                return sideLabel;
            }
            function buildSideBlock(data) {
                if (!paneEnabled(nSide)) {
                    return null;
                }

                const infoplanBySide = Object.fromEntries(
                    data.infoplan.map(sideObj => [sideObj.side, sideObj.variables])
                )
                const sideVars = infoplanBySide[nSide];

                let sideBlock = document.createElement('div');
                sideBlock.setAttribute('class', 'variables-container-side-block')

                const sideLabel = (isFingerPostMarker
                    ? buildSideHeaderFingerpost(data) : buildSideHeaderUsual(data));

                let sideList = document.createElement('ul');
                sideList.dataset['number'] = nSide;

                sideList.append(...sideVars.map(varData => {
                    let variableItem = document.createElement('li');
                    variableItem.innerHTML = varData;
                    // variableItem.addEventListener('click', () => handleToggleWrong(data.marker, varData.key));
                    // varWrongnessManager.register(data.marker, varData.key, variableItem, varData.wrong);
                    return variableItem;
                }));

                sideBlock.append(sideLabel, sideList);
                sideBlock.dataset['number'] = nSide;
                return sideBlock;
            }

            return buildSideBlock;
        }

        const sides = data.layer.kind.sides;
        const isInfoplanSet = (data.infoplan
            .map(sideObj => sideObj.variables.length)
            .reduce((a, b) => a + b, 0)
            > 0);

        let variablesLabel = document.createElement('span');
        variablesLabel.setAttribute('style', 'font-size: 10px;');
        variablesLabel.textContent = (isInfoplanSet ? 'Инфоплан' : 'У объекта не заполнен инфоплан');

        let variablesDiv  = document.createElement('div');
        variablesDiv.setAttribute('class', `variables_container`);

        if (isInfoplanSet) {
            const sideNumbers = Array.from(Array(sides));
            variablesDiv.append(...sideNumbers
                .map((e, i) => buildSideNBlock(i + 1)(data))
                .filter((elem) => elem !== null)
            );
        }
        const actualSideCount = variablesDiv.children.length;

        if (isFingerPostMarker) {
            for (const sideBlock of Array.from(variablesDiv.children)) {
                // insert br only before list of 5th pane
                if (sideBlock.dataset['number'] === '5') {
                    variablesDiv.insertBefore(document.createElement('br'), sideBlock);
                }
            }
        }

        if (isFingerPostMarker) {
            const oneRowSides = Math.min(actualSideCount, 4);
            variablesDiv.style.gridTemplateColumns = `repeat(${oneRowSides}, 1fr)`;
        }
        else {
            variablesDiv.style.gridTemplateColumns = `repeat(${actualSideCount}, 1fr)`;
        }

        let infoplanDiv  = document.createElement('div');
        infoplanDiv.append(variablesLabel, variablesDiv);

        return infoplanDiv;
    }
    function buildCommentBlock(data) {
        function buildCommentElem(cObj) {
            const comment = cObj.content;
            let commentBlock = document.createElement('div');
            commentBlock.textContent = comment;
            if (cObj.resolved) commentBlock.setAttribute('style', 'color: lightgrey;');
            return commentBlock;
        }
        const [hasComment, comments] = [data.has_comment, data.comments];
        const label = ( hasComment ? 'Комментарии' : 'Комментариев нет');
        const placeholder = ( hasComment ? 'Добавить комментарий' : 'Можно не заполнять');

        let commentLabel = document.createElement('span');
        commentLabel.setAttribute('style', 'font-size: 10px;');
        commentLabel.textContent = label;

        let commentsBlock = document.createElement('div');
        commentsBlock.append(...comments.map(c => buildCommentElem(c)))

        let commentInput = document.createElement('textarea');
        commentInput.setAttribute('class', 'comment_field');
        commentInput.setAttribute('placeholder', placeholder);
        commentInput.setAttribute('onkeyup', 'event.stopPropagation()');

        let commentDiv = document.createElement('div');
        commentDiv.append(
            commentLabel,
            commentsBlock,
            commentInput
        );
        return commentDiv;
    }
    function buildConfirmBtn(data) {
        let btnLink = document.createElement('a');
        btnLink.setAttribute('class', 'message_confirm_btn');
        btnLink.textContent = 'Проверено';
        btnLink.addEventListener('click',
            () => handlerConfirmBtnClick(data.marker));
        return btnLink;
    }

    const boxDiv = document.createElement('div');
    boxDiv.setAttribute('class', 'message_box');
    boxDiv.append(
        buildHeader(data),
        buildInfoplanBlock(data),
        buildCommentBlock(data),
        buildConfirmBtn(data)
    );
    return boxDiv;
}

// HANDLERS

function onSuccessLoadReview(markerData) {
    const markerUid = markerData.marker;
    markerCirclesManager.sync(markerData);
    messageBoxManager.deleteMessage(markerUid);
    refreshMarkerElement(markerData);
}

function handlerMessBlur(marker_uid) {
    const variables = varWrongnessManager.data(marker_uid);
    let comment = messageBoxManager.read(marker_uid);
    if (comment === undefined) {
        console.error('method for comment returned undefined', marker_uid);
        comment = '';
    }

    const data = {
        variables: variables,
        comment: comment,
        exit_type: 'blur',
    };
    doApiCall('POST', API_MARKER_LOAD_REVIEW(marker_uid), data,
        onSuccessLoadReview);

    messageBoxManager.hide(marker_uid);
}

function handlerConfirmBtnClick(marker_uid) {
    const variables = varWrongnessManager.data(marker_uid);
    let comment = messageBoxManager.read(marker_uid);
    if (comment === undefined) {
        console.error('method for comment returned undefined', marker_uid);
        comment = '';
    }

    const data = {
        variables: variables,
        comment: comment,
        exit_type: 'button',
    };
    doApiCall('POST', API_MARKER_LOAD_REVIEW(marker_uid), data,
        onSuccessLoadReview);

    messageBoxManager.hide(marker_uid);
}
