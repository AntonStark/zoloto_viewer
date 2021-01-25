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
                let sideBlock = document.createElement('div');
                sideBlock.setAttribute('class', 'variables-container-side-block')

                let sideLabel = document.createElement('div');
                sideLabel.setAttribute('style', 'font-size: 10px;');
                sideLabel.textContent = sideLabels[nSide];

                let sideInput = document.createElement('textarea');
                sideInput.addEventListener('blur', variablesContainerBlur);

                sideBlock.append(sideLabel, sideInput);
                return sideBlock;
            }
            return buildSideBlock;
        }

        const sides = data.layer.kind.sides;
        console.log(data);

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
        function buildCommentBlock(comment) {
            let commentBlock = document.createElement('div');
            commentBlock.textContent = comment;
            return commentBlock;
        }
        const [hasComment, comments] = [data.has_comment, data.comments.map(cObj => cObj.content)];

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
        btnLink.addEventListener('click', () => handlerInfoplanMessSaveBtn(markerUid));
        return btnLink;
    }

    const boxDiv = document.createElement('div');
    boxDiv.setAttribute('class', 'message_box');
    boxDiv.addEventListener('onkeyup', function (e) {e.stopPropagation();})
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
