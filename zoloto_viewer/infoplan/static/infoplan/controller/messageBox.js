"use strict";
function ControllerMessageBox(render) {
    let _renderedMessagesIndex = {};     // marker_uid -> {messContainer: MessageBoxNode}
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
        /* todo
        1) -- получить размер компонента с планом
        2) -- создать матрицу с шагом 10px заполненную [0, 0]
        3) -- обойти отрендеренные блоки и пометить их узлы в матрице как null (если они видимы!)
        4) -- этот метод должен знать размер размещаемого блока

        5) -- запросить координаты маркера для markerUid
        6) пометить также узлы, размещение в которых закрывает маркер
        7) обойти матрицу и заполнить (пропуская null) величины расстояний
           до маркера, попутно отслеживая argmin по метрике L2
         */
        const [mapScrWidth, mapScrHeight] = mapScaleController.origSize();
        const [hPoints, vPoints] = [mapScrWidth / nodesSparseFactor, mapScrHeight / nodesSparseFactor].map(Math.floor);
        let nodeMatrix = Array(vPoints).fill().map(
            () => Array(hPoints).fill([undefined, undefined])
        );
        // fixme есть проблема с массивами при выводе второго блока
        //  Cannot set property '0' of undefined
        //  seems to i be out of bounds
        function viewMatrix(color) {
            // для каждой вершины вывести черную точку если там null, иначе -- цветную
            const svgNS = 'http://www.w3.org/2000/svg';
            const elementId = 'view-matrix-svg-group';
            let groupElement = document.createElementNS(svgNS,'g');
            for (let i = 0; i < nodeMatrix.length; ++i) {
                const y = i * nodesSparseFactor;
                for (let j = 0; j < nodeMatrix[i].length; ++j) {
                    const x = j * nodesSparseFactor;
                    const point = document.createElementNS(svgNS,'circle');
                    point.setAttributeNS(null,"cx",x);
                    point.setAttributeNS(null,"cy",y);
                    point.setAttributeNS(null,"r",1);
                    point.setAttributeNS(null,'stroke','none');
                    point.setAttributeNS(null,'fill',
                        (nodeMatrix[i][j] === null ? 'black' : color));
                    groupElement.append(point);
                }
            }
            let oldGroupElement = document.getElementById(elementId);
            if (oldGroupElement) {
                oldGroupElement.parentNode.replaceChild(groupElement, oldGroupElement);
            }
            else {
                const svgElem = document.getElementById('project-page-plan-svg');
                svgElem.append(groupElement);
            }
            groupElement.setAttributeNS(null, 'id', elementId);
        }

        const [newBoxWidth, newBoxHeight] = [messContainer.offsetWidth, messContainer.offsetHeight];
        function toNodesLowerBound(length) { return Math.ceil(length / nodesSparseFactor); }
        function toNodesUpperBound(length) { return Math.floor(length / nodesSparseFactor); }
        function coveredHorizontalNodes(box) {
            const boxRect = box.getBoundingClientRect();
            const mapRect = mapScaleController.mapRect();
            const from = toNodesLowerBound(Math.max(0, boxRect.left - (newBoxWidth + boxMargins) - mapRect.left));
            const to = toNodesUpperBound(Math.min(mapRect.right, boxRect.right - mapRect.left));
            return Array.from(Array(to - from + 1), (e, i) => from + i);
        }
        function coveredVerticalNodes(box) {
            const boxRect = box.getBoundingClientRect();
            const mapRect = mapScaleController.mapRect();
            const from = toNodesLowerBound(Math.max(0, boxRect.top - (newBoxHeight + boxMargins) - mapRect.top))
            const to = toNodesUpperBound(Math.min(mapRect.bottom, boxRect.bottom - mapRect.top))
            return Array.from(Array(to - from + 1), (e, i) => from + i);
        }

        for (const markerUid of renderedMessagesIds()) {
            if (!visibleMessagesIndex[markerUid])
                continue;

            const box = getContainerOrNull(markerUid);
            if (box !== null) {
                console.debug(box.getBoundingClientRect());

                const horizontalNodesInterval = coveredHorizontalNodes(box);
                const verticalNodesInterval = coveredVerticalNodes(box);
                console.log(markerUid, 'horizontal:', horizontalNodesInterval, 'vertical:', verticalNodesInterval);
                for (let i of verticalNodesInterval) {
                    for (let j of horizontalNodesInterval) {
                        nodeMatrix[i][j] = null;
                    }
                }
            }

            const marker = getMarkerOrNull(markerUid);
            if (marker !== null) {
                console.debug(marker.getBoundingClientRect());

                const horizontalNodesInterval = coveredHorizontalNodes(marker);
                const verticalNodesInterval = coveredVerticalNodes(marker);
                console.log(markerUid, 'horizontal:', horizontalNodesInterval, 'vertical:', verticalNodesInterval);
                for (let i of verticalNodesInterval) {
                    for (let j of horizontalNodesInterval) {
                        nodeMatrix[i][j] = null;
                    }
                }
            }
        }
        // viewMatrix('red');
        // TODO 2) удалить старый способ
        const [rawMarX, rawMarY] = markerCirclesManager.position(markerUid);
        const planScale = mapScaleController.current();
        const [marX, marY] = [planScale * rawMarX, planScale * rawMarY];

        const targetMarker = getMarkerOrNull(markerUid);
        const tmClientRect = targetMarker.getBoundingClientRect();
        const tmcX = (tmClientRect.left + tmClientRect.right) / 2;
        const tmcY = (tmClientRect.top + tmClientRect.bottom) / 2;
        // TODO 1) debug that two ways of getting marker coordinates are equal
        // TODO 3) вычисление расстояния (по x и y) от каждой Node до целевого маркера
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

    function placeDefault(container, markerUid, messContainer) {
        _setPosition(messContainer);
        _setDisplay(messContainer, false);

        container.append(messContainer);
        _registerMessageItem(markerUid, {messContainer: messContainer});
    }

    function hideMessage(markerUid) {
        const maybeMessItem = getContainerOrNull(markerUid);
        if (maybeMessItem !== null) {
            _setDisplay(maybeMessItem, false);
            visibleMessagesIndex[markerUid] = false;
            markerCirclesManager.setShown(markerUid, false);
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
            _setDisplay(maybeMessItem);
            maybeMessItem.focus();
            visibleMessagesIndex[markerUid] = true;
            markerCirclesManager.setShown(markerUid, true);
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
        doApiCall('GET', API_MARKER_GET_DATA(markerUid), undefined,
            function (markerData) {
                const messageElem = renderMessage(markerData);
                let messContainer = makeWrapper(undefined, undefined, messageElem);
                // сначала размещаем в дефолтном положении и невидимым
                placeDefault(container, markerData.marker, messContainer);
                const position = acquireMessagePosition(markerUid, messContainer);
                // а теперь выставляем положение и показываем
                if (position) {
                    _setPosition(messContainer, position)
                    _setDisplay(messContainer)
                    visibleMessagesIndex[markerUid] = true;
                }
                else {
                    // todo нужны разные коды ошибок для разных ситуаций (какие ситуации описаны в тз?)
                    console.log('position=', position);

                    container.removeChild(messContainer);
                    messContainer = null;       // for proper garbage collection
                    return;
                }

                messLinksManager.update(markerUid, messContainer);
                messContainer.focus();
            });
        if (visibleMessagesIndex[markerUid])
            markerCirclesManager.setShown(markerUid, true);
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
        // wrapper.style.display = 'none';
    }
}

function _setDisplay(wrapper, block=true) {
    if (block) {
        // wrapper.style.display = 'block';
        wrapper.style.opacity = '1';
    }
    else {
        // wrapper.style.display = 'none';
        wrapper.style.opacity = '0';
    }
}
