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
            return commentBlock;
        }
        const [hasComment, comments] = [data.has_comment, data.comments];

        let commentLabel = document.createElement('span');
        commentLabel.setAttribute('style', 'font-size: 10px;');
        commentLabel.textContent = ( hasComment ? 'Комментарий' : 'Комментариев нет');

        let commentsBlock = document.createElement('div');
        commentsBlock.setAttribute('class', 'comment_field');
        commentsBlock.append(...comments.map(c => buildCommentBlock(c)))

        let commentDiv = document.createElement('div');
        commentDiv.append(commentLabel, commentsBlock);
        return commentDiv;
    }
    function buildSaveBtn(data) {
        const markerUid = data.marker;
        let btnLink = document.createElement('a');
        btnLink.setAttribute('class', 'message_confirm_btn');
        btnLink.textContent = 'Сохранить';
        btnLink.addEventListener('click', () => handlerConfirmBtmClick(markerUid));
        return btnLink;
    }

    const boxDiv = document.createElement('div');
    boxDiv.setAttribute('class', 'message_box');
    boxDiv.addEventListener('keyup', function (e) {e.stopPropagation();})
    boxDiv.append(buildInfoplanBlock(data), buildCommentBlock(data), buildSaveBtn(data));
    return boxDiv;
}

function variablesContainerBlur(e) {
    let v = e.target.value;
    if (v.length > 0
        && !( v.endsWith(';') || v.endsWith('\n') )
    ) {
        v = v + ';\n';
        e.target.value = v;
    }
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
    // doApiCall('POST', API_MARKER_LOAD_REVIEW(marker_uid), data,
    //     (rep) => markerCirclesManager.sync(rep));

    // todo refactor these handlers with onSuccess and onError, .hide call below inappropriate
    messageBoxManager.hide(marker_uid);
}

function handlerConfirmBtmClick(marker_uid) {
    function parseSideVariables(sideInputValue) {
        if (sideInputValue.endsWith(';\n')) {
            sideInputValue = sideInputValue.slice(0, -2);
        } else if (sideInputValue.endsWith(';')) {
            sideInputValue = sideInputValue.slice(0, -1);
        }

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

    const req = {
        infoplan: sideObjects
    }
    doApiCall('PUT', API_MARKER_PUT_VARS(marker_uid), req,
        function (rep) {
        messageBoxManager.hide(marker_uid);
    }, function (rep) {
        console.log(rep);
    });

}
