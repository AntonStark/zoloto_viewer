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

function buildMessBox(data) {
    function buildHeader(data) {
        const markerNumber = data.number;
        let header = document.createElement('div');
        header.textContent = markerNumber;
        return header;
    }
    function buildInfoplanBlock(data) {
        function buildSideNBlock(nSide) {
            const sideLabels = {
                1: 'Сторона A',
                2: 'Сторона B',
                3: 'Сторона C',
                4: 'Сторона D',
            }
            function buildSideBlock(data) {
                const infoplanBySide = Object.fromEntries(
                    data.infoplan.map(sideObj => [sideObj.side, sideObj.variables])
                )
                const sideVars = infoplanBySide[nSide];

                let sideBlock = document.createElement('div');
                sideBlock.setAttribute('class', 'variables-container-side-block')

                let sideLabel = document.createElement('div');
                sideLabel.setAttribute('style', 'font-size: 10px;');
                sideLabel.textContent = sideLabels[nSide];

                let sideList = document.createElement('ul');
                sideList.setAttribute('data-number', nSide);

                sideList.append(...sideVars.map(varData => {
                    let variableItem = document.createElement('li');
                    // variableItem.setAttribute('data-variable-key', varData.key);
                    // variableItem.textContent = varData.value;
                    const lines = varData.split('\n')
                        .reduce( (item, seq) => [item, document.createElement('br')].concat(seq) );
                    if (lines instanceof Array)
                        variableItem.append.apply(variableItem, lines);
                    else
                        variableItem.textContent = varData;
                    // variableItem.textContent = varData.replaceAll('\n', '<br/>');
                    // variableItem.addEventListener('click', () => handleToggleWrong(data.marker, varData.key));
                    // varWrongnessManager.register(data.marker, varData.key, variableItem, varData.wrong);
                    return variableItem;
                }));

                sideBlock.append(sideLabel, sideList);
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
            variablesDiv.append(...sideNumbers.map((e, i) => buildSideNBlock(i + 1)(data)));
        }

        let infoplanDiv  = document.createElement('div');
        infoplanDiv.append(variablesLabel, variablesDiv);

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
        const label = ( hasComment ? 'Комментарии' : 'Комментариев нет');
        const placeholder = ( hasComment ? 'Добавить комментарий' : 'Можно не заполнять');

        let commentLabel = document.createElement('span');
        commentLabel.setAttribute('style', 'font-size: 10px;');
        commentLabel.textContent = label;

        let commentsBlock = document.createElement('div');
        commentsBlock.append(...comments.map(c => buildCommentBlock(c)))

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
    const box = messageBoxManager.get(marker_uid);
    if (box !== undefined) {
        if (box.dataset.btnClicked) {
            delete box.dataset.btnClicked;
            return;
        }
    }

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
    const box = messageBoxManager.get(marker_uid);
    if (box !== undefined) {    // to distinguish click form blur in blur handler
        box.dataset.btnClicked = 'true';
    }

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
