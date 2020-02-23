"use strict";

const MESSAGE_BOX_SIZE = [160, 260];
const WRONG_VARIABLE_CLASS = 'wrong_variable';

const BASE_URL = 'http://localhost:8000/viewer/api/';
const API_VARIABLE_ALTER_WRONG = (marker_uid) => BASE_URL + `marker/${marker_uid}/variable/`;
const API_MARKER_GET_DATA = (marker_uid) => BASE_URL + `marker/${marker_uid}`;
const API_MARKER_LOAD_REVIEW = (marker_uid) => BASE_URL + `marker/${marker_uid}/review/`;

const mockPosition = [300, 200];

const layerColor = '#70153f';       // todo убрать

function buildMessBox(data) {
    function buildVariablesBlock(data) {
        function toggleVariableWrong(varItem, wantedStatus) {
            if (wantedStatus !== varItem.classList.contains(WRONG_VARIABLE_CLASS))
                varItem.classList.toggle(WRONG_VARIABLE_CLASS);
            varItem.dataset.isWrong = wantedStatus;
        }

        let variablesList = document.createElement('ul');
        variablesList.setAttribute('class', 'variables_list');
        variablesList.setAttribute('style', `color: white; background: ${layerColor}`);
        variablesList.append(...data.variables.map(varData => {
            let variableItem = document.createElement('li');
            variableItem.setAttribute('data-variable-key', varData.key);
            if (varData.wrong) {
                toggleVariableWrong(variableItem, varData.wrong);
            }
            variableItem.textContent = varData.value;
            variableItem.addEventListener('click', () =>
                handleToggleWrong(data.marker, varData.key, variableItem, toggleVariableWrong)
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
    function obtainData(marker_uid, dataDisplayCallback) {
        let req = new XMLHttpRequest();
        req.open('GET', API_MARKER_GET_DATA(marker_uid));
        req.onreadystatechange = function () {
            if (req.readyState === XMLHttpRequest.DONE) {
                if (req.status === 200) {
                    const markerData = JSON.parse(req.responseText);
                    return dataDisplayCallback(markerData);
                }
                else {
                    console.error(req);
                    return undefined;
                }
            }
        };
        req.send();
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
    function appendMessageBox(container, markerData) {
        const position = acquirePosition();
        if (!position)
            return undefined;

        const messNode = makeWrapper(position, MESSAGE_BOX_SIZE,
            buildMessBox(markerData), handlerMessBlur(markerData.marker));
        _registerMessageItem(markerData.marker, messNode);
        container.append(messNode);
        messNode.focus();
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

        return obtainData(marker_uid, (data) => appendMessageBox(container, data));
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

function handleToggleWrong(marker_uid, variable_key, variableItem, viewModifier) {
    // console.debug('handleToggleWrong', marker_uid, variable_key);
    let req = new XMLHttpRequest();
    req.open('POST', API_VARIABLE_ALTER_WRONG(marker_uid));
    req.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    req.onreadystatechange = function() {
        if (req.readyState === XMLHttpRequest.DONE) {
            if (req.status === 200) {
                console.debug(req, 'modifyView');
                const rep = JSON.parse(req.responseText);
                if (rep['marker'] === marker_uid && rep['variable'] !== undefined) {
                    viewModifier(variableItem, rep['variable']['wrong']);
                    // todo обновлять кружок корректности
                }
            }
            else {
                console.error(req);
            }
        }
    };
    const currentlyWrong = variableItem.dataset.isWrong === 'true';
    req.send(JSON.stringify({'key': variable_key, 'wrong': !currentlyWrong}));
    // todo не позволять пометить пустую переменную
}

function handleClickMarkerCircle(circleElement) {
    messageBoxManager.show(circleElement.dataset.markerUid, circleElement.dataset.layerTitle);
}
