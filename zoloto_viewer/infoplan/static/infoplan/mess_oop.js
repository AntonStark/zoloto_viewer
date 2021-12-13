const MessBuilder = () => {
    function buildHeader(data) {
        const markerNumber = data.number;
        let header = document.createElement('div');
        header.textContent = markerNumber;
        return header;
    }
    function buildCommentElem(commentObj) {
        const comment = commentObj.content;
        let commentBlock = document.createElement('div');
        commentBlock.textContent = comment;
        if (commentObj.resolved) commentBlock.setAttribute('style', 'color: lightgrey;');
        return commentBlock;
    }
    function buildCommentBlock(data) {
        const [hasComment, comments] = [data.has_comment, data.comments];
        const label = ( hasComment ? 'Комментарии' : 'Комментариев нет');
        const placeholder = ( hasComment ? 'Добавить комментарий' : 'Можно не заполнять');

        let commentLabel = document.createElement('span');
        commentLabel.setAttribute('style', 'font-size: 10px;');
        commentLabel.textContent = label;

        let commentsBlock = document.createElement('div');
        commentsBlock.append(...comments.map(c => this._buildCommentElem(c)))

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
                    variableItem.innerHTML = varData;
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
        variablesDiv.style.gridTemplateColumns = `repeat(${sides}, 1fr)`;

        if (isInfoplanSet) {
            const sideNumbers = Array.from(Array(sides));
            variablesDiv.append(...sideNumbers.map((e, i) => buildSideNBlock(i + 1)(data)));
        }

        let infoplanDiv  = document.createElement('div');
        infoplanDiv.append(variablesLabel, variablesDiv);

        return infoplanDiv;
    }

    function render(data) {
        const boxDiv = document.createElement('div');
        boxDiv.setAttribute('class', 'message_box');
        boxDiv.append(
            this._buildHeader(data),
            this._buildInfoplanBlock(data),
            this._buildCommentBlock(data),
            this._buildConfirmBtn(data)
        );
        return boxDiv;
    }

    return {
        _buildHeader: buildHeader,
        _buildCommentElem: buildCommentElem,
        _buildCommentBlock: buildCommentBlock,
        _buildConfirmBtn: buildConfirmBtn,
        _buildInfoplanBlock: buildInfoplanBlock,
        render: render,
    }
}

const MessAuthBuilder = () => {
    let builderBase = MessBuilder()

    builderBase._buildConfirmBtn = function () {

    }

    return builderBase
}
