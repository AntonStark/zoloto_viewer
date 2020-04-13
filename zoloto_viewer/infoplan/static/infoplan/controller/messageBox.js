"use strict";
function ControllerMessageBox(render) {
    let _renderedMessagesIndex = {};     // marker_uid -> {messContainer: MessageBoxNode}
    let visibleMessagesIndex  = {};     // marker_uid -> visibility (bool)
    let markerElementIndex    = {};     // marker_uid -> MarkerElement
    const renderMessage = render;

    function _registerMessageItem(marker_uid, messageObj) {
        const messNode = messageObj.messContainer;

        if (_renderedMessagesIndex[marker_uid] !== undefined) {
            const storedContainer = _renderedMessagesIndex[marker_uid].messContainer;
            if (storedContainer !== messNode)
                _renderedMessagesIndex[marker_uid].remove();
        }
        _renderedMessagesIndex[marker_uid] = {messContainer: messNode, messLink: undefined};
    }
    function renderedMessagesIds() {
        return Object.keys(_renderedMessagesIndex);
    }
    function getContainerOrNull(marker_uid) {
        if (_renderedMessagesIndex[marker_uid] !== undefined)
            return _renderedMessagesIndex[marker_uid].messContainer;
        else
            return null;
    }

    function deduceContainer(layerTitle) {
        const c = document.getElementsByClassName('layer_messages layer-' + layerTitle);
        if (c.length > 0)
            return c[0];
        else
            return undefined;
    }
    function acquireMessagePosition(marker_uid) {
        for (const markerUid of renderedMessagesIds()) {
            const box = getContainerOrNull(markerUid);
            console.debug(box.getBoundingClientRect());
        }
        const [rawMarX, rawMarY] = markerCirclesManager.position(marker_uid);
        const planScale = mapScaleController.current();

        const [marX, marY] = [planScale * rawMarX, planScale * rawMarY];
        const d = 20;

        const x = marX + d;
        const y = marY + d;

        return [x, y];
    }
    function onMapScaleChange() {
        for (const markerUid of renderedMessagesIds()) {
            // todo обновление положения при изменении масштаба должно вычисляться быстрее, чем первичное размещение
            //  и эффективнее если сразу для всего массива (возможно с сообщением об ошибке "недостаточно места")
            const newPos = acquireMessagePosition(markerUid);
            const messageContainer = getContainerOrNull(markerUid);
            _setPosition(messageContainer, newPos)
            messLinksManager.update(markerUid, messageContainer);
        }
        // console.debug('map scale set to ', newScale);
    }
    function makeWrapper(position, size, mess) {
        const wrapper = document.createElement('div');
        wrapper.style.position = 'absolute';
        _setPosition(wrapper, position)
        _setSize(wrapper, size)
        wrapper.style.outline = 'none';

        wrapper.append(mess);
        wrapper.addEventListener('focus', handlerMessageDivFocus);
        return wrapper;
    }

    function hideMessage(marker_uid) {
        const maybeMessItem = getContainerOrNull(marker_uid);
        if (maybeMessItem !== null) {
            _setDisplay(maybeMessItem, false);
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
            _setDisplay(maybeMessItem);
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
        //   1) запросить данные
        //   2) если данные пришли, построить Node сообщения, закинуть в индекс и отобразить в контейнере
        //   3) запросить и установить размещение. если места не нашлось, удалить
        doApiCall('GET', API_MARKER_GET_DATA(marker_uid), undefined,
            function (markerData) {
                const messageElem = renderMessage(markerData);
                let messContainer = makeWrapper(undefined, undefined, messageElem);
                const position = acquireMessagePosition(marker_uid);
                if (!position) {
                    // todo нужны разные коды ошибок для разных ситуаций (какие ситуации описаны в тз?)
                    console.log('position=', position);
                    messContainer = null;       // for proper garbage collection
                    return;
                }
                else {
                    _setPosition(messContainer, position)
                    _setDisplay(messContainer)
                }

                container.append(messContainer);
                _registerMessageItem(markerData.marker, {messContainer: messContainer});
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
}

function _setSize(wrapper, size) {
    if (size !== undefined) {
        wrapper.style.width = size[0] + 'px';
        wrapper.style.height = size[1] + 'px';
    }
}

function _setPosition(wrapper, position) {
    if (position !== undefined) {
        wrapper.style.left = position[0] + 'px';
        wrapper.style.top = position[1] + 'px';
    }
    else {
        wrapper.style.left = '0';
        wrapper.style.top = '0';
        wrapper.style.display = 'none';
    }
}

function _setDisplay(wrapper, block=true) {
    if (block)
        wrapper.style.display = 'block';
    else
        wrapper.style.display = 'none';
}
