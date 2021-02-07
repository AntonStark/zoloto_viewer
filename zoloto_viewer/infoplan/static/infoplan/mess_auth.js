"use strict";

function buildMessBox(data) {
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

                let sideInput = document.createElement('textarea');
                sideInput.setAttribute('class', 'variables-container-side-input')
                sideInput.setAttribute('data-number', nSide);
                sideInput.setAttribute('rows', 6);

                // noinspection UnnecessaryLocalVariableJS
                const inputValue = ( sideVars ? sideVars.join(';\n') + ';' : '');
                sideInput.value = inputValue;
                sideInput.addEventListener('blur', variablesContainerBlur);

                sideBlock.append(sideLabel, sideInput);
                return sideBlock;
            }
            return buildSideBlock;
        }

        const sides = data.layer.kind.sides;

        let variablesLabel = document.createElement('span');
        variablesLabel.setAttribute('style', 'font-size: 10px;');
        variablesLabel.textContent = 'Инфоплан';

        let variablesDiv  = document.createElement('div');
        variablesDiv.setAttribute('class', `variables_container`);

        const sideNumbers = Array.from(Array(sides));
        variablesDiv.append(...sideNumbers.map((e, i) => buildSideNBlock(i + 1)(data)));

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
        const [markerUid, hasComment] = [data.marker, data.has_comment];

        let btnLink = document.createElement('a');
        if (!hasComment) return btnLink;

        btnLink.classList.add('fill-button', 'noselect')
        btnLink.setAttribute('style', 'width: fit-content; margin-bottom: 6px;')
        btnLink.textContent = 'Все учтены';
        btnLink.addEventListener('click', () => handlerResolveCommentsBtnClick(markerUid));
        return btnLink;
    }
    function buildSaveBtn(data) {
        const markerUid = data.marker;
        let btnLink = document.createElement('a');
        btnLink.setAttribute('class', 'message_confirm_btn');
        btnLink.textContent = 'Сохранить';
        btnLink.addEventListener('click', () => handlerConfirmBtnClick(markerUid));
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

function onSuccessLoadReview(markerData) {
    const markerUid = markerData.marker;
    messageBoxManager.hide(markerUid);
}

function onErrorLoadReview(rep) {
    console.log(rep);
    alert('Возникла ошибка при сохранении.\nПопробуйте чуть позже или обратитесь к администратору.');
}

function handlerMessBlur(marker_uid) {
    const box = messageBoxManager.get(marker_uid);
    if (box !== undefined) {
        if (box.dataset.btnClicked) {
            // todo why this dataset used? still needed?
            delete box.dataset.btnClicked;
            return;
        }
    }

    messageBoxManager.hide(marker_uid);
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
        },
        (rep) => {console.log(rep);},
        );
}

function handlerConfirmBtnClick(marker_uid) {
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

    const box = messageBoxManager.get(marker_uid);
    if (!box) return;
    console.debug('btnSave box', box);

    const sides = box.getElementsByClassName('variables-container-side-input');
    let sideObjects = [];
    for (const s of sides) {
        sideObjects.push({side: Number(s.dataset.number), variables: parseSideVariables(s.value)})
    }

    doApiCall('PUT', API_MARKER_PUT_VARS(marker_uid), {
        infoplan: sideObjects
    }, onSuccessLoadReview, onErrorLoadReview);
}
