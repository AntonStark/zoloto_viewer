"use strict";

const MESSAGE_BOX_SIZE = [160, 260];
const WRONG_VARIABLE_CLASS = 'wrong_variable';
const HIDDEN_MESSAGE_CLASS = 'hidden_box';

const BASE_URL = 'http://localhost:8000/viewer/api/';
const API_VARIABLE_ALTER_WRONG = (marker_uid) => `marker/${marker_uid}/variable/`;
const API_MARKER_GET_DATA = (marker_uid) => `marker/${marker_uid}`;
const API_MARKER_LOAD_REVIEW = (marker_uid) => `marker/${marker_uid}/review/`;

const mockPosition = [300, 200];

const mockLayerTitle = '124_D_HAN';
const mockMarkerData = {
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
            if (varData.wrong) {
                toggleItemWrong(variableItem);
            }
            variableItem.textContent = varData.value;
            variableItem.addEventListener('click', () =>
                handleToggleWrong(data.marker, varData.key,
                    () => toggleItemWrong(variableItem))
            );
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

function toggleItemWrong(element) {
    element.classList.toggle(WRONG_VARIABLE_CLASS);
}

function test() {
    messageBoxManager.show(mockMarkerData.marker, mockLayerTitle);
}
window.addEventListener('load', test);

const messageBoxManager = function () {
    let renderedMessagesIndex = {};     // marker_uid -> MessageBoxNode
    function _registerMessageItem(marker_uid, item) {
        if (renderedMessagesIndex[marker_uid] !== undefined
            && renderedMessagesIndex[marker_uid] !== item)
            renderedMessagesIndex[marker_uid].remove();
        renderedMessagesIndex[marker_uid] = item;
    }
    function checkMessageIndex(marker_uid) {
        if (renderedMessagesIndex[marker_uid] !== undefined)
            return renderedMessagesIndex[marker_uid];
        else
            return null;
    }

    function acquirePosition() {
        return mockPosition;
    }
    function obtainData(marker_uid) {
        return mockMarkerData;
    }
    function makeWrapper(position, size, mess, hideCallback) {
        const wrapper = document.createElementNS("http://www.w3.org/2000/svg",
            'foreignObject');
        wrapper.setAttribute('x', position[0]);
        wrapper.setAttribute('y', position[1]);
        wrapper.setAttribute('width', size[0]);
        wrapper.setAttribute('height', size[1]);
        wrapper.style.outline = 'none';

        wrapper.append(mess);
        wrapper.addEventListener('blur', () => hideCallback());
        return wrapper;
    }
    function deduceContainer(layerTitle) {
        const c = document.getElementsByClassName('layer_messages ' + layerTitle);
        if (c.length > 0)
            return c[0];
        else
            return undefined;
    }

    function hideMessage(marker_uid) {
        const maybeMessItem = checkMessageIndex(marker_uid);
        if (maybeMessItem !== null) {
            maybeMessItem.style.display = 'none';
            return true;
        }
        else
            return false;
    }
    function showMessage(marker_uid, layer_title) {
        // проверить индекс и если есть, просто переключить видимость
        const maybeMessItem = checkMessageIndex(marker_uid);
        if (maybeMessItem !== null) {
            maybeMessItem.style.display = 'initial';
            return;
        }

        // если сообщения ещё нет в индексе, нужно:
        //   1) запросить место
        //   2) если место нашлось запросить данные
        //   3) если данные пришли, построить Node сообщения, закинуть в индекс и отобразить в контейнере
        const container = deduceContainer(layer_title);
        if (!container)
            return;

        const position = acquirePosition();
        if (!position)
            return;

        const markerData = obtainData(marker_uid);
        if (!markerData)
            return;     // todo free position

        const messNode = makeWrapper(position, MESSAGE_BOX_SIZE, buildMessBox(markerData), handlerMessBlur(marker_uid));
        _registerMessageItem(marker_uid, messNode);
        container.append(messNode);
        messNode.focus();
    }

    return {
        show: showMessage,
        hide: hideMessage,
    }
}();

function handlerMessBlur(marker_uid) {
    // todo send req

    return () => messageBoxManager.hide(marker_uid);
}

function handleToggleWrong(marker_uid, variable_key, viewModifier) {
    console.debug('handleToggleWrong', marker_uid, variable_key);
    let req = new XMLHttpRequest();
    req.open('POST', BASE_URL + API_VARIABLE_ALTER_WRONG(marker_uid));
    req.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    req.onreadystatechange = function() {
        if (req.readyState === XMLHttpRequest.DONE) {
            if (req.status === 200) {
                console.debug(req, 'modifyView');
                viewModifier();
            }
            else {
                console.error(req);
            }
        }
    };
    req.send(JSON.stringify({'key': variable_key, 'wrong': true}));
}
