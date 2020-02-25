"use strict";

const MESSAGE_BOX_SIZE = [160, 260];
let SVG_VIEWPORT_BOUNDS = undefined;
window.addEventListener('load', function () {
    const svgElement = document.getElementById('project-page-plan-svg');
    // console.log(svgElement.width.baseVal.value);
    SVG_VIEWPORT_BOUNDS = [svgElement.width.baseVal.value, svgElement.height.baseVal.value];
});


function buildMessBox(data) {
    function buildVariablesBlock(data) {
        let variablesList = document.createElement('ul');
        variablesList.setAttribute('style', `color: white; background: ${data.layer.color}`);
        variablesList.append(...data.variables.map(varData => {
            let variableItem = document.createElement('li');
            variableItem.setAttribute('data-variable-key', varData.key);
            variableItem.textContent = varData.value;
            variableItem.addEventListener('click', () => handleToggleWrong(data.marker, varData.key));
            varWrongnessManager.register(data.marker, varData.key, variableItem, varData.wrong);
            return variableItem;
        }));

        let variablesDiv  = document.createElement('div');
        variablesDiv.setAttribute('class', 'variables_container');
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

    function acquirePosition(markerPosition) {
        const [marX, marY] = markerPosition;
        const [boxW, boxH] = MESSAGE_BOX_SIZE;
        const [svgW, svgH] = SVG_VIEWPORT_BOUNDS;
        const d = 10;

        const x = (marX + (d + boxW) < svgW
            ? marX + d
            : marX - (d + boxW));
        const y = (marY + (d + boxH) < svgH
            ? marY + d
            : marY - (d + boxH));

        return [x, y];
    }
    function onFetchData(marker_uid, dataCallback) {
        let req = new XMLHttpRequest();
        req.open('GET', API_MARKER_GET_DATA(marker_uid));
        req.onreadystatechange = function () {
            if (req.readyState === XMLHttpRequest.DONE) {
                if (req.status === 200) {
                    const markerData = JSON.parse(req.responseText);
                    return dataCallback(markerData);
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
    function showMessage(marker_uid) {
        // проверить индекс и если есть, просто переключить видимость
        // console.log('showMessage', markerPosition);
        const maybeMessItem = checkMessageIndex(marker_uid);
        if (maybeMessItem !== null) {
            maybeMessItem.style.display = 'block';
            return;
        }

        // если сообщения ещё нет в индексе, нужно:
        //   1) запросить место
        //   2) если место нашлось запросить данные
        //   3) если данные пришли, построить Node сообщения, закинуть в индекс и отобразить в контейнере
        return onFetchData(marker_uid, function (markerData) {
            const layer_title = markerData.layer.title;
            // todo вообще то стоит опредялть container и markerPosition снаружи (до запроса данных)
            //  но для этого надо брать layer_title не из данных
            const container = deduceContainer(layer_title);
            if (!container)
                return;

            const markerPosition = markerCirclesManager.position(markerData.marker);
            const position = acquirePosition(markerPosition);
            if (!position)
                return undefined;

            const messNode = makeWrapper(position, MESSAGE_BOX_SIZE,
                buildMessBox(markerData), handlerMessBlur(markerData.marker));
            _registerMessageItem(markerData.marker, messNode);
            container.append(messNode);
            messNode.focus();
        });
    }

    return {
        show: showMessage,
        hide: hideMessage,
    }
}();


const markerCirclesManager = function () {
    const MARKER_CORRECT_CLASS = 'marker_correct';
    const MARKER_INCORRECT_CLASS = 'marker_wrong';
    let markerCorrCircles = {};         // marker_uid -> SvgCircleElement
    let circleCenterIndex = {};         // marker_uid -> [x, y]

    function _setCorrectness(element, correct) {
        if (element.classList.contains(MARKER_CORRECT_CLASS) !== correct)
            element.classList.toggle(MARKER_CORRECT_CLASS);
        if (element.classList.contains(MARKER_INCORRECT_CLASS) !== !correct)
            element.classList.toggle(MARKER_INCORRECT_CLASS);
    }
    function _evalViewportPosition(circleElement) {
        const transform = circleElement.getCTM();
        let probe = circleElement.ownerSVGElement.createSVGPoint();
        probe.x = circleElement.cx.baseVal.value;
        probe.y = circleElement.cy.baseVal.value;
        probe = probe.matrixTransform(transform);
        return [probe.x, probe.y];
    }

    function registerMarkerCircle(circleElement) {
        const markerUid = circleElement.dataset.markerUid;
        markerCorrCircles[markerUid] = circleElement;
        circleCenterIndex[markerUid] = _evalViewportPosition(circleElement);
    }
    function updateCorrectness(markerData) {
        // console.log('updateCorrectness', markerData);
        const [markerUid, correct] = [markerData.marker, markerData.correct];
        const elem = markerCorrCircles[markerUid];
        if (elem !== undefined)
            _setCorrectness(elem, correct);
    }
    function getCircleCenter(markerUid) {
        return circleCenterIndex[markerUid];
    }

    return {
        register: registerMarkerCircle,
        sync    : updateCorrectness,
        position: getCircleCenter,
    }

}();


const varWrongnessManager = function () {
    const WRONG_VARIABLE_CLASS = 'wrong_variable';
    let variablesItemsIndex = {};       // { marker_uid -> { key -> Item} }
    let variablesWrongnessIndex = {};       // { marker_uid -> { key -> isWrong} }

    function _setVariableWrongness(varItem, wantedStatus) {
        if (varItem.classList.contains(WRONG_VARIABLE_CLASS) !== wantedStatus)
            varItem.classList.toggle(WRONG_VARIABLE_CLASS);
    }

    function registerVariableItem(markerUid, key, item, isWrong) {
        if (variablesItemsIndex[markerUid] === undefined)
            variablesItemsIndex[markerUid] = {};
        variablesItemsIndex[markerUid][key] = item;

        if (variablesWrongnessIndex[markerUid] === undefined)
            variablesWrongnessIndex[markerUid] = {};
        variablesWrongnessIndex[markerUid][key] = isWrong;
        _setVariableWrongness(variablesItemsIndex[markerUid][key], isWrong);
    }
    function updateWrongStatus(markerVarData) {
        const [markerUid, varData] = [markerVarData.marker, markerVarData.variable];
        const [key, wrong] = [varData.key, varData.wrong];

        if (variablesItemsIndex[markerUid] && variablesItemsIndex[markerUid][key]) {
            variablesWrongnessIndex[markerUid][key] = wrong;
            _setVariableWrongness(variablesItemsIndex[markerUid][key], wrong);
        }
    }
    function isWrong(markerUid, key) {
        if (variablesWrongnessIndex[markerUid] && variablesWrongnessIndex[markerUid][key])
            return variablesWrongnessIndex[markerUid][key];
        else
            return undefined;
    }

    return {
        register: registerVariableItem,
        sync: updateWrongStatus,
        status: isWrong,
    }
}();
