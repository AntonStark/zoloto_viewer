"use strict";
function ControllerMessageBox(render) {
    let _renderedMessagesIndex = {};    // marker_uid -> {messContainer: MessageBoxNode}
    let visibleMessagesIndex  = {};     // marker_uid -> visibility (bool)
    let markerElementIndex    = {};     // marker_uid -> MarkerElement
    const renderMessage = render;
    const nodesSparseFactor = 10;
    const boxMargins = 20;

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
    function getMarkerOrNull(marker_uid) {
        if (markerElementIndex[marker_uid] !== undefined)
            return markerElementIndex[marker_uid];
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
    function acquireMessagePosition(markerUid, messContainer) {
        const [rawMarX, rawMarY] = markerCirclesManager.position(markerUid);
        const planScale = mapScaleController.current();
        const [marX, marY] = [planScale * rawMarX, planScale * rawMarY];

        const targetMarker = getMarkerOrNull(markerUid);
        const tmClientRect = targetMarker.getBoundingClientRect();
        const tmcX = (tmClientRect.left + tmClientRect.right) / 2;
        const tmcY = (tmClientRect.top + tmClientRect.bottom) / 2;
        const d = MARKER_DISPLAY_CONFIG.circle_radius;

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

    function placeDefault(container, markerUid, messContainer) {
        _setPosition(messContainer);
        _setVisibility(messContainer, false);

        container.append(messContainer);
        _registerMessageItem(markerUid, {messContainer: messContainer});
    }

    function hideMessage(markerUid) {
        const maybeMessItem = getContainerOrNull(markerUid);
        if (maybeMessItem !== null) {
            _setVisibility(maybeMessItem, false);
            visibleMessagesIndex[markerUid] = false;
            return true;
        }
        else
            return false;
    }
    function showMessage(markerUid) {
        // проверить индекс и если есть, просто переключить видимость
        // console.log('showMessage', markerPosition);
        const maybeMessItem = getContainerOrNull(markerUid);
        if (maybeMessItem !== null) {
            _setVisibility(maybeMessItem);
            maybeMessItem.focus();
            visibleMessagesIndex[markerUid] = true;
            return;
        }

        const layer_title = markerElementIndex[markerUid].dataset.layerTitle;
        const container = deduceContainer(layer_title);
        if (!container)
            return;

        // если сообщения ещё нет в индексе, нужно:
        //   1) запросить данные
        //   2) если данные пришли, построить Node сообщения, закинуть в индекс и отобразить в контейнере
        //   3) запросить и установить размещение. если места не нашлось, удалить
        makeDataRequest(markerUid, function (markerData) {
                const messageElem = renderMessage(markerData);
                let messContainer = makeWrapper(undefined, undefined, messageElem);
                // сначала размещаем в дефолтном положении и невидимым
                placeDefault(container, markerData.marker, messContainer);
                const position = acquireMessagePosition(markerUid, messContainer);
                // а теперь выставляем положение и показываем
                if (position) {
                    _setPosition(messContainer, position)
                    _setVisibility(messContainer)
                    visibleMessagesIndex[markerUid] = true;
                }
                else {
                    console.log('position=', position);

                    container.removeChild(messContainer);
                    messContainer = null;       // for proper garbage collection
                    return;
                }

                messContainer.focus();
            });
    }
    function getComment(markerUid) {
        const box = getContainerOrNull(markerUid);
        if (!box)
            return undefined;

        const commentField = box.getElementsByClassName('comment_field');
        console.log(commentField, commentField.length);
        if (commentField.length > 0)
            return commentField[0].value;
        else
            return undefined;
    }
    function registerMarkerElement(markerElement) {
        markerElementIndex[markerElement.dataset.markerUid] = markerElement;
    }
    function deleteMessage(markerUid) {
        let c = getContainerOrNull(markerUid);
        if (c)
            c.remove();
        delete _renderedMessagesIndex[markerUid];
        delete visibleMessagesIndex[markerUid];
    }
    function deleteMarkerAndMessage(markerUid) {
        let m = getMarkerOrNull(markerUid)
        if (m)
            m.remove();
        delete markerElementIndex[markerUid];

        deleteMessage(markerUid);
    }

    function hideAllMessages() {
        for (const markerUid in visibleMessagesIndex)
            if (visibleMessagesIndex[markerUid])
                handlerMessBlur(markerUid);
    }
    function showAllSelected(isSelected) {
        for (const markerUid of Object.keys(markerElementIndex)) {
            if (isSelected(markerUid)) {
                showMessage(markerUid);
            }
        }
    }

    return {
        show: showMessage,
        hide: hideMessage,
        read: getComment,
        get : getContainerOrNull,
        getMarker: getMarkerOrNull,
        reg : registerMarkerElement,

        deleteMessage: deleteMessage,
        delMarkerAndMessage : deleteMarkerAndMessage,

        hideAll: hideAllMessages,
        showSelected: showAllSelected,
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
        // wrapper.style.display = 'none';
    }
}

function _setVisibility(wrapper, block=true) {
    if (block) {
        wrapper.style.visibility = 'visible';
    }
    else {
        wrapper.style.visibility = 'hidden';
    }
}
