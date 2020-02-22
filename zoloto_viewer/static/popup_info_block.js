"use strict";

const position = [300, 200];
const size = [160, 260];

const markerData = {
    'marker': '47735e8f-9c07-4df6-81e0-991b8c70fd65',
    'correct': null,
    'variables': [
        {'key': '1', 'value': 'первый!', 'wrong': false},
        {'key': '2', 'value': 'и второй', 'wrong': true},
    ],
    'has_comment': true,
    'comment': 'Lorem ipsum ...',
};
const layerColor = '#70153f';

function buildMessBox(data) {
    function buildVariablesBlock(data) {
        let variablesList = document.createElement('ul');
        variablesList.setAttribute('class', 'variables_list');
        variablesList.setAttribute('style', `color: white; background: ${layerColor}`);
        variablesList.append(...data.variables.map(varData => {
            let variableItem = document.createElement('li');
            variableItem.setAttribute('data-variable-key', varData.key);
            variableItem.textContent = varData.value;
            return variableItem;
        }));

        let variablesDiv  = document.createElement('div');
        variablesDiv.setAttribute('style', 'flex-grow: 1; min-height: 0; overflow-y: scroll;');
        variablesDiv.append(variablesList);
        return variablesDiv;
    }
    function buildCommentBlock(data) {
        let commentLabel = document.createElement('span');
        commentLabel.setAttribute('style', 'font-size: 10px;');
        commentLabel.textContent = 'Комментарий';

        let commentInput = document.createElement('textarea');
        commentInput.setAttribute('class', 'comment_field');
        commentInput.setAttribute('placeholder', 'Можно не заполнять');
        if (data.has_comment) {
            commentInput.value = data.comment;
        }

        let commentDiv = document.createElement('div');
        commentDiv.append(commentLabel, commentInput);
        return commentDiv;
    }
    function buildConfirmBtn(data) {
        let btnLink = document.createElement('a');
        btnLink.setAttribute('class', 'message_confirm_btn');
        btnLink.textContent = 'Проверено';
        return btnLink;
    }

    const boxDiv = document.createElement('div');
    boxDiv.setAttribute('class', 'message_box');
    boxDiv.append(buildVariablesBlock(data), buildCommentBlock(data), buildConfirmBtn(data));
    return boxDiv;
}

function renderMessBox(marker_uid, container, messPos, messSize) {
    // like <foreignObject x="46" y="22" width="200" height="300">
    let wrapper = document.createElementNS("http://www.w3.org/2000/svg", 'foreignObject');
    const props = {
        'x': messPos[0],
        'y': messPos[1],
        'width': messSize[0],
        'height': messSize[1],
    };
    for (const attr in props)
        wrapper.setAttribute(attr, props[attr]);

    const messNode = buildMessBox(markerData);
    wrapper.appendChild(messNode);
    container.appendChild(wrapper);
}

function test() {
    const layerTitle = '124_D_HAN';
    const c = document.getElementsByClassName('layer_messages ' + layerTitle)[0];
    renderMessBox('47735e8f-9c07-4df6-81e0-991b8c70fd65', c, position, size);
}
window.addEventListener('load', test);
