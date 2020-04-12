"use strict";
function ControllerMessageBox(render) {
    let renderedMessagesIndex = {};     // marker_uid -> MessageBoxNode
    let visibleMessagesIndex  = {};     // marker_uid -> visibility (bool)
    let markerElementIndex    = {};     // marker_uid -> MarkerElement
    const renderMessage = render;

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
        const d = 20;

        const x = marX + d;
        const y = marY + d;

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
                const messageElem = renderMessage(markerData);
                const messContainer = makeWrapper(position, undefined, messageElem);
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
}
