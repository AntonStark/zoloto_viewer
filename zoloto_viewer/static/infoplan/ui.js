"use strict";

let SVG_VIEWPORT_BOUNDS = undefined;
window.addEventListener('load', function () {
    const svgElement = document.getElementById('project-page-plan-svg');
    // console.log(svgElement.width.baseVal.value);
    SVG_VIEWPORT_BOUNDS = [svgElement.width.baseVal.value, svgElement.height.baseVal.value];
});


function buildMessBox(data) {
    function buildVariablesBlock(data) {
        let variablesList = document.createElement('ul');

        let [numberLine, emptyLine] = [document.createElement('li'), document.createElement('li')];
        numberLine.style.cursor = emptyLine.style.cursor = 'unset';
        numberLine.textContent = data.number;
        emptyLine.innerHTML = '&nbsp;';
        variablesList.append(numberLine, emptyLine);

        variablesList.append(...data.variables.map(varData => {
            let variableItem = document.createElement('li');
            variableItem.setAttribute('data-variable-key', varData.key);
            variableItem.textContent = varData.value;
            variableItem.addEventListener('click', () => handleToggleWrong(data.marker, varData.key));
            varWrongnessManager.register(data.marker, varData.key, variableItem, varData.wrong);
            return variableItem;
        }));

        let variablesDiv  = document.createElement('div');
        variablesDiv.setAttribute('class', `variables_container`);
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
        btnLink.addEventListener('click',
            () => handlerConfirmBtmClick(data.marker));
        return btnLink;
    }

    const boxDiv = document.createElement('div');
    boxDiv.setAttribute('class', 'message_box');
    boxDiv.append(buildVariablesBlock(data), buildCommentBlock(data), buildConfirmBtn(data));
    return boxDiv;
}

const messageBoxManager = function () {
    let renderedMessagesIndex = {};     // marker_uid -> MessageBoxNode
    let visibleMessagesIndex  = {};     // marker_uid -> visibility (bool)
    let markerElementIndex    = {};     // marker_uid -> MarkerElement

    function _registerMessageItem(marker_uid, messageObj) {
        const messNode = messageObj.messContainer;

        if (renderedMessagesIndex[marker_uid] !== undefined) {
            const storedContainer = renderedMessagesIndex[marker_uid].messContainer;
            if (storedContainer !== messNode)
                renderedMessagesIndex[marker_uid].remove();
        }
        renderedMessagesIndex[marker_uid] = {messContainer: messNode, messLink: undefined};
    }
    function renderedMessagesIds() {
        return Object.keys(renderedMessagesIndex);
    }
    function getContainerOrNull(marker_uid) {
        if (renderedMessagesIndex[marker_uid] !== undefined)
            return renderedMessagesIndex[marker_uid].messContainer;
        else
            return null;
    }

    function acquireMessagePosition(marker_uid) {
        const [rawMarX, rawMarY] = markerCirclesManager.position(marker_uid);
        const planScale = mapScaleController.current();

        const [marX, marY] = [planScale * rawMarX, planScale * rawMarY];
        const [boxW, boxH] = [0, 0];    // stub for a while
        const [svgW, svgH] = SVG_VIEWPORT_BOUNDS;
        const d = 20;

        const x = (marX + (d + boxW) < svgW
            ? marX + d
            : marX - (d + boxW));
        const y = (marY + (d + boxH) < svgH
            ? marY + d
            : marY - (d + boxH));

        return [x, y];
    }
    function onMapScaleChange() {
        for (const markerUid of renderedMessagesIds()) {
            const newPos = acquireMessagePosition(markerUid);
            const messageContainer = getContainerOrNull(markerUid);
            messageContainer.style.left = newPos[0] + 'px';
            messageContainer.style.top = newPos[1] + 'px';
            messLinksManager.update(markerUid, messageContainer);
        }
        // console.debug('map scale set to ', newScale);
    }
    function makeWrapper(position, size, mess) {
        // const wrapper = document.createElementNS("http://www.w3.org/2000/svg",
        //     'foreignObject');
        const wrapper = document.createElement('div');
        wrapper.style.position = 'absolute';
        wrapper.style.left = position[0] + 'px';
        wrapper.style.top = position[1] + 'px';
        if (size !== undefined) {
            wrapper.style.width = size[0] + 'px';
            wrapper.style.height = size[1] + 'px';
        }
        wrapper.style.outline = 'none';

        wrapper.append(mess);
        wrapper.addEventListener('focus', handlerMessageDivFocus);
        return wrapper;
    }
    function deduceContainer(layerTitle) {
        const c = document.getElementsByClassName('layer_messages layer-' + layerTitle);
        if (c.length > 0)
            return c[0];
        else
            return undefined;
    }

    function hideMessage(marker_uid) {
        const maybeMessItem = getContainerOrNull(marker_uid);
        if (maybeMessItem !== null) {
            maybeMessItem.style.display = 'none';
            visibleMessagesIndex[marker_uid] = false;
            markerCirclesManager.setShown(marker_uid, false);
            return true;
        }
        else
            return false;
    }
    function showMessage(marker_uid) {
        // проверить индекс и если есть, просто переключить видимость
        // console.log('showMessage', markerPosition);
        const maybeMessItem = getContainerOrNull(marker_uid);
        if (maybeMessItem !== null) {
            maybeMessItem.style.display = 'block';
            maybeMessItem.focus();
            visibleMessagesIndex[marker_uid] = true;
            markerCirclesManager.setShown(marker_uid, true);
            return;
        }

        const layer_title = markerElementIndex[marker_uid].dataset.layerTitle;
        const container = deduceContainer(layer_title);
        if (!container)
            return;

        // если сообщения ещё нет в индексе, нужно:
        //   1) запросить место
        //   2) если место нашлось запросить данные
        //   3) если данные пришли, построить Node сообщения, закинуть в индекс и отобразить в контейнере
        const position = acquireMessagePosition(marker_uid);
        if (!position)      // todo нужны разные коды ошибок для разных ситуаций (какие ситуации описаны в тз?)
            return;

        doApiCall('GET', API_MARKER_GET_DATA(marker_uid), undefined,
            function (markerData) {
            const messContainer = makeWrapper(position, undefined,
                buildMessBox(markerData));
            _registerMessageItem(markerData.marker, {messContainer: messContainer});
            container.append(messContainer);
            messLinksManager.update(marker_uid, messContainer);
            messContainer.focus();
        });
        visibleMessagesIndex[marker_uid] = true;
        markerCirclesManager.setShown(marker_uid, true);
    }
    function getComment(markerUid) {
        const box = getContainerOrNull(markerUid);
        if (!box)
            return undefined;

        const commentField = box.getElementsByTagName('textarea');
        if (commentField.length > 0)
            return commentField[0].value;
        else
            return undefined;
    }
    function registerMarkerElement(markerElement) {
        markerElementIndex[markerElement.dataset.markerUid] = markerElement;
    }

    function hideAllMessages() {
        for (const markerUid in visibleMessagesIndex)
            if (visibleMessagesIndex[markerUid])
                handlerMessBlur(markerUid);
    }

    return {
        show: showMessage,
        hide: hideMessage,
        read: getComment,
        get : getContainerOrNull,
        reg : registerMarkerElement,
        hideAll: hideAllMessages,
        onMapScaleChange: onMapScaleChange,
    }
}();


const markerCirclesManager = function () {
    const MARKER_CORRECT_CLASS = 'marker_correct';
    const MARKER_INCORRECT_CLASS = 'marker_wrong';
    const MARKER_HAS_COMMENT_CLASS = 'marker_has_comment';
    const MARKER_MESSAGE_SHOWN_CLASS = 'message_shown';
    let markerCorrCircles = {};         // marker_uid -> SvgCircleElement
    let circleCenterIndex = {};         // marker_uid -> [x, y]

    function _setCorrectness(element, correct) {
        if (correct === null)
            return;
        if (element.classList.contains(MARKER_CORRECT_CLASS) !== correct)
            element.classList.toggle(MARKER_CORRECT_CLASS);
        if (element.classList.contains(MARKER_INCORRECT_CLASS) !== !correct)
            element.classList.toggle(MARKER_INCORRECT_CLASS);
    }
    function _setHasComment(element, has) {
        if (!element)
            return;
        if (element.classList.contains(MARKER_HAS_COMMENT_CLASS) !== has)
            element.classList.toggle(MARKER_HAS_COMMENT_CLASS);
    }
    function _setMessShown(element, isShown) {
        if (!element)
            return;
        if (element.classList.contains(MARKER_MESSAGE_SHOWN_CLASS) !== isShown)
            element.classList.toggle(MARKER_MESSAGE_SHOWN_CLASS);
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
        const elem = markerCorrCircles[markerData.marker];
        if (elem !== undefined) {
            const [correct, hasComment] = [markerData.correct, markerData.has_comment];
            _setCorrectness(elem.parentNode, correct);
            _setHasComment(elem.nextElementSibling, hasComment);
        }
    }
    function getCircleCenter(markerUid) {
        return circleCenterIndex[markerUid];
    }
    function setShownStatus(markerUid, isShown) {
        const elem = markerCorrCircles[markerUid];
        _setMessShown(elem.parentNode, isShown);
        // console.debug('setShownStatus', markerUid, isShown);
    }

    return {
        register: registerMarkerCircle,
        sync    : updateCorrectness,
        position: getCircleCenter,
        setShown: setShownStatus,
    }

}();


const messLinksManager = function () {
    let messLinkIndex = {};         // marker_uid -> <line> elem
    
    function registerLinkElem(markerUid, elem) {
        if (messLinkIndex[markerUid] !== undefined
            && messLinkIndex[markerUid] !== elem)
            messLinkIndex[markerUid].remove();
        messLinkIndex[markerUid] = elem;
    }

    function _toSvgCoordinates(linkElement, screenCoordinates) {
        const inverseTransform = linkElement.getCTM().inverse();
        let probe = linkElement.ownerSVGElement.createSVGPoint();
        probe.x = screenCoordinates[0];
        probe.y = screenCoordinates[1];
        probe = probe.matrixTransform(inverseTransform);
        return [probe.x, probe.y];
    }

    function updateLinkParams(markerUid, messContainer) {
        return;
        const messLink = messLinkIndex[markerUid];
        if (!messLink)
             return;

        const [cx, cy, mr] = [Number(messLink.dataset.cx), Number(messLink.dataset.cy), Number(messLink.dataset.mr)];
        const htmlCoords = [messContainer.offsetLeft, messContainer.offsetTop];
        const [left, top] = _toSvgCoordinates(messLink, htmlCoords);
        const x2 = left;
        const y2 = top;
        // y = (1-l) * cy + l * y2
        // dx^2 + dy^2 = mr^2
        const l = Math.sqrt(mr ** 2 / ( (y2 - cy) ** 2 + (x2 - cx) ** 2));
        const x1 = (1-l) * cx + l * x2;
        const y1 = (1-l) * cy + l * y2;
        messLink.setAttribute('x1', x1);
        messLink.setAttribute('y1', y1);
        messLink.setAttribute('x2', x2);
        messLink.setAttribute('y2', y2);
    }

    return {
        register: registerLinkElem,
        update  : updateLinkParams,
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
    function allMarkerVars(markerUid) {
        const mData = variablesWrongnessIndex[markerUid];
        if (!mData)
            return undefined;

        return Object.entries(mData)
            .map((pair) => ({'key': pair[0], 'wrong': pair[1]}));
    }

    return {
        register: registerVariableItem,
        sync    : updateWrongStatus,
        status  : isWrong,
        data    : allMarkerVars,
    }
}();
