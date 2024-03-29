"use strict";
function ControllerMapInteractions() {
    // state
    let markerSelection = [];
    let rectSelectionCorner = undefined;
    let markerMovement = false;
    let movementStartPoint = undefined;

    // map interaction modes
    function isInsertMode() {
        const control = document.getElementById('menu_actions_option1');
        if (!control) return false;
        return control.checked;
    }
    function isSelectMode() {
        const control = document.getElementById('menu_actions_option2');
        if (!control) return true;
        return control.checked;
    }
    function isCaptionsMode() {
        const control = document.getElementById('menu_actions_option3');
        if (!control) return false;
        return control.checked;
    }
    function toggleInsertMode() {
        const control = document.getElementById('menu_actions_option1');
        control.checked = true;
    }
    function toggleSelectMode() {
        const control = document.getElementById('menu_actions_option2');
        control.checked = true;
    }
    function toggleCaptionsMode() {
        const control = document.getElementById('menu_actions_option3');
        control.checked = true;
    }

    function activeLayer()
    { return enabledLayersController.getActive(); }
    function getPageCode()
    { return pageCode; }
    function getProjectUid()
    { return projectUid; }

    // marker selection
    function isInSelection(markerUid)
    { return markerSelection.indexOf(markerUid) !== -1; }
    function addToSelection(markerUid)
    { markerSelection.push(markerUid); }
    function toggleIsSelected(markerUid, include) {
        if (isInSelection(markerUid) && !include) {
            const i = markerSelection.indexOf(markerUid);
            if (i > -1) {
                markerSelection.splice(i, 1);
            }
        }
        else if (!isInSelection(markerUid) && include) {
            addToSelection(markerUid);
        }
    }
    function dropSelection()
    { markerSelection.splice(0, markerSelection.length); }
    function getSelection()
    { return Array.from(markerSelection); }

    // inner methods
    function _deleteRoutine(markerUidArray) {
        // console.debug('deleteRoutine', markerUidArray);
        for (const markerUid of markerUidArray) {
            deleteMarker(markerUid, function (rep) {
                if (rep['status'] === 'ok') {
                    markerCirclesManager.delete(markerUid);
                    messageBoxManager.delMarkerAndMessage(markerUid);
                }
            });
        }
        dropSelection();
    }

    // marker creator
    function _createHelper(posX, posY) {
        createMarker({
            project: projectUid,
            page: mapInteractionsController.pageCode(),
            layer: mapInteractionsController.activeLayer(),
            position: {
                center_x: posX,
                center_y: posY,
                rotation: 0,
            }
        }, function (rep) {
            renderMarkerElement(rep);
            addToSelection(rep.marker);
            markerCirclesManager.render(mapInteractionsController.isInSelection);
        });
    }

    // marker copy creators
    function _pasteMarkerHelper(markerUidArray) {
        let payload = {
            'clipboard_uuid': markerUidArray,
            'project': mapInteractionsController.getProjectUid(),
            'page': mapInteractionsController.pageCode(),
        };
        clipMarkers(payload,
            function (rep) {
            dropSelection();
            for (const elem of rep.created) {
                renderMarkerElement(elem);
                addToSelection(elem.marker);
            }
            markerCirclesManager.render(mapInteractionsController.isInSelection);
        });
    }
    function _duplicateMarkerHelper(markerUidArray) {
        let payload = {
            'clipboard_uuid': markerUidArray,
            'project': mapInteractionsController.getProjectUid(),
            'page': mapInteractionsController.pageCode(),
            'shift': false,
        };
        clipMarkers(payload,
            function (rep) {
            dropSelection();
            for (const elem of rep.created) {
                renderMarkerElement(elem);
                addToSelection(elem.marker);
            }
            markerCirclesManager.render(mapInteractionsController.isInSelection);

            mapScaleController.mapSvg().addEventListener('mousemove', mapInteractionsController.handleMouseMove);
        });
    }

    // map interaction handlers
    function handleKeyUp(e) {
        if (e.code === 'Backspace' && UI_AUTH) {
            _deleteRoutine(markerSelection);
        } else if (e.code === 'Escape') {
            dropSelection();
            markerCirclesManager.render(mapInteractionsController.isInSelection);
        } else if (e.code === 'KeyI') {
            handleInfoplanOpen(mapInteractionsController.getSelection());
        } else if (e.code === 'KeyX') {
            mapInteractionsController.toggleInsertMode();
        } else if (e.code === 'KeyV') {
            mapInteractionsController.toggleSelectMode();
        } else if (e.code === 'KeyN' && UI_AUTH) {
            console.log(getSelection());
        } else if (e.code === 'ArrowUp' && e.shiftKey) {
            // upper area
            areasListController.toUpperArea(pageCode);
        } else if (e.code === 'ArrowDown' && e.shiftKey) {
            // lower area
            areasListController.toLowerArea(pageCode);
        }
    }
    function handleKeyPress(e) {
        if (!UI_AUTH)
            return;     // modification will fail in guest mode
        if (e.target.classList.contains('variables-container-side-input'))
            return;     // skip if in infoplan text block

        const keyToOffset = {
            'KeyW': [0, -1],
            'KeyA': [-1, 0],
            'KeyS': [0, 1],
            'KeyD': [1, 0],
            'ArrowUp': [0, -1],
            'ArrowLeft': [-1, 0],
            'ArrowDown': [0, 1],
            'ArrowRight': [1, 0],
        }
        const acceleration = e.shiftKey;
        if (e.code === 'KeyQ') {            // positive rotation
            handleRotation(true, acceleration)
        } else if (e.code === 'KeyE') {     // negative rotation
            handleRotation(false, acceleration);
        } else if (keyToOffset.hasOwnProperty(e.code)) {
            let offset = keyToOffset[e.code];
            if (acceleration) {
                offset[0] = 10 * offset[0];
                offset[1] = 10 * offset[1];
            }
            _updateMarkersVisiblePositions(offset);
            markerCirclesManager.finishMovement(getSelection());
        }
    }
    function handleClickMap(e) {
        // console.log('handleClickMap');
        const [svgX, svgY] = getSvgCoordinates(e);
        const inside = mapScaleController.isInsideMapRect(svgX, svgY);
        if (!inside)
            return;

        // console.debug(svgX, svgY, activeLayer(), getPageCode());

        messageBoxManager.hideAll();
        dropSelection();

        if (isInsertMode()) {
            _createHelper(svgX, svgY);
        }

        markerCirclesManager.render(mapInteractionsController.isInSelection);
    }

    function _takeSelectionRect(secondCorner, reset=true) {
        if (!rectSelectionCorner) {
            return [ [0, 0], [0, 0] ];
        }
        const xCoords = [rectSelectionCorner[0], secondCorner[0]];
        const yCoords = [rectSelectionCorner[1], secondCorner[1]];
        if (reset) {
            rectSelectionCorner = undefined;
        }
        return [xCoords, yCoords];
    }
    function _isCollapsedSelection(xCoords, yCoords) {
        const COLLAPSE = 10;
        const [x1, x2] = xCoords;
        const [y1, y2] = yCoords;
        return Math.abs(x2 - x1) < COLLAPSE
            && Math.abs(y2 - y1) < COLLAPSE;
    }
    function _isCollapsedOffset(offsetX, offsetY) {
        const COLLAPSE = 10;
        return Math.sqrt(Math.pow(offsetX, 2) + Math.pow(offsetY, 2)) < COLLAPSE;
    }
    function _toggleSelectionRect(visibility) {
        const rect = document.getElementById('project-page-svg-selection-rect');
        rect.classList.toggle('active', visibility);
    }
    function _boundSelectionRect(xCoords, yCoords) {
        if (!(xCoords[0] < xCoords[1]))
            xCoords = xCoords.reverse();
        if (!(yCoords[0] < yCoords[1]))
            yCoords = yCoords.reverse();
        const rect = document.getElementById('project-page-svg-selection-rect');
        rect.setAttributeNS(null, 'x', xCoords[0]);
        rect.setAttributeNS(null, 'y', yCoords[0]);
        rect.setAttributeNS(null, 'width', xCoords[1] - xCoords[0]);
        rect.setAttributeNS(null, 'height', yCoords[1] - yCoords[0]);
    }
    function _updateMarkersVisiblePositions(offset) {
        markerCirclesManager.updateMarkerPosition(getSelection(), offset);
    }
    function handleMouseDown(e) {
        // console.log('handleMouseDown', e);
        if (isInsertMode() || isCaptionsMode())
            return;

        messageBoxManager.hideAll();

        const maybeCircleElement = e.target;
        const movementAllowed = UI_AUTH;    // modification will fail in guest mode
        markerMovement = maybeCircleElement.classList.contains('marker_circle');

        if (!markerMovement) {
            rectSelectionCorner = getSvgCoordinates(e);
            const [xInit, yInit] = _takeSelectionRect(getSvgCoordinates(e), false);
            _boundSelectionRect(xInit, yInit);
            _toggleSelectionRect(true);
        }
        else {
            movementStartPoint = getSvgCoordinates(e);
            const markerUid = maybeCircleElement.dataset.markerUid;

            if (e.altKey) {
                // если зажат Alt/Option, то применяем конструктор копированием аналогичный _pasteMarkerHelper
                // но обработчик mousemove устанавливается в onSuccess чтобы не затронуть существующий маркер
                _duplicateMarkerHelper([markerUid]);
                return;
            }

            if (!isInSelection(markerUid)) {
                if (!e.shiftKey) {
                    dropSelection();
                }
                addToSelection(markerUid);
                markerCirclesManager.render(mapInteractionsController.isInSelection);
            }
        }

        if (!markerMovement || movementAllowed) {
            mapScaleController.mapSvg().addEventListener('mousemove', mapInteractionsController.handleMouseMove);
        }
    }
    function handleMouseMove(e) {
        if (!markerMovement) {
            const [xCoords, yCoords] = _takeSelectionRect(getSvgCoordinates(e), false);
            _boundSelectionRect(xCoords, yCoords);
        }
        else {
            const endPoint = getSvgCoordinates(e);
            const offset = [endPoint[0] - movementStartPoint[0], endPoint[1] - movementStartPoint[1]];
            if (_isCollapsedOffset(offset[0], offset[1])) return;
            _updateMarkersVisiblePositions(offset);
        }
    }
    function handleMouseUp(e) {
        // console.log('handleMouseUp', 'mapController', e);
        mapScaleController.mapSvg().removeEventListener('mousemove', mapInteractionsController.handleMouseMove);
        mapScaleController.mapSvg().removeEventListener('mousemove', captionsController.handleMouseMove);

        // если подпись выпрыгнула из под мышки (проход через ноль) то
        // срабатывает этот метод, а не captionsController.handleMouseUp и нужно перенаправить
        if (captionsController.isCaptionMovement()) {
            // delegate
            captionsController.handleMouseUp(e);
            return;
        }

        if (markerMovement) {
            // обновлять данные в индексе ControllerMarkerCircles.circleCenterIndex и положение сообщения
            markerCirclesManager.finishMovement(getSelection());

            movementStartPoint = undefined;
            markerMovement = false;
            return;
        }
        // если режим добавления, то mouseup равносильно клику
        // а в режиме выделения, нужно в mouseup смотреть
        // размер прямоугольника выделения если мал, значит клик
        const [xCoords, yCoords] = _takeSelectionRect(getSvgCoordinates(e));
        if (isInsertMode()
            || (isInSelection() && _isCollapsedSelection(xCoords, yCoords)))
            return handleClickMap(e);

        // console.log('setSelectionRect', xCoords, yCoords);
        markerCirclesManager.setSelectionRect(xCoords, yCoords);
        _toggleSelectionRect(false);

        const selectionPredicate = ( e.shiftKey
            ? function (markerUid)
                { return isInSelection(markerUid) || markerCirclesManager.isInsideSelectionRect(markerUid); }
            : markerCirclesManager.isInsideSelectionRect
        );

        markerCirclesManager.render(selectionPredicate, toggleIsSelected);
    }

    function handleRotation(isPositive, isAccelerated) {
        const posFactor = (isPositive ? 1 : -1);
        const accFactor = (isAccelerated ? 10 : 1);
        const rotationDelta = posFactor * accFactor;
        markerCirclesManager.updateRotation(getSelection(), rotationDelta);
    }

    function handleCopyEvent(e) {
        if (!UI_AUTH)
            return;     // modification will fail in guest mode
        if (e.target.classList.contains('variables-container-side-input'))
            return;     // skip paste in infoplan text block

        const text = encodeClipboardContent(getSelection());
        // console.debug('Copy!', text);
        window.navigator.clipboard.writeText(text);
    }
    function handlePasteEvent(e) {
        if (!UI_AUTH)
            return;     // modification will fail in guest mode
        if (e.target.classList.contains('variables-container-side-input'))
            return;     // skip paste in infoplan text block

        // console.debug('Paste start!');
        function onClipboardResolve(text) {
            const markerUidArray = decodeClipboardContent(text);
            // console.debug('Paste!', markerUidArray);
            _pasteMarkerHelper(markerUidArray);
        }
        function onError(e) {
            alert('Доступ к буфферу заблокирован.\n' +
                'Требуется разрешение.\n' +
                'Свяжитесь с администратором.')
        }
        window.navigator.clipboard.readText()
            .then(onClipboardResolve)
            .catch(onError);
    }

    function handleInfoplanOpen(markerUidArray) {
        if (markerUidArray.length === 1) {
            messageBoxManager.show(markerUidArray[0]);
        }
        else {
            messageBoxManager.showMany(markerUidArray)
        }
    }

    return {
        isInsertMode: isInsertMode,
        isSelectMode: isSelectMode,
        isCaptionsMode: isCaptionsMode,
        toggleInsertMode : toggleInsertMode,
        toggleSelectMode : toggleSelectMode,

        getProjectUid   : getProjectUid,
        activeLayer : activeLayer,
        pageCode    : getPageCode,

        isInSelection   : isInSelection,
        addToSelection  : addToSelection,
        dropSelection   : dropSelection,
        getSelection    : getSelection,
        toggleIsSelected: toggleIsSelected,

        handleKeyUp             : handleKeyUp,
        handleKeyPress          : handleKeyPress,

        handleMouseDown : handleMouseDown,
        handleMouseMove : handleMouseMove,
        handleMouseUp   : handleMouseUp,

        handleCopyEvent: handleCopyEvent,
        handlePasteEvent: handlePasteEvent,
    }
}

function getSvgCoordinates(mouseEvent) {
    probePt.x = mouseEvent.clientX;
    probePt.y = mouseEvent.clientY;

    // The cursor point, translated into svg coordinates
    const cursorPt =  probePt.matrixTransform(mapSvgElem.getScreenCTM().inverse());
    return [cursorPt.x, cursorPt.y];
}

// not used
function toOuterCoordinates(x, y) {
    probePt.x = x;
    probePt.y = y;

    const cursorPt =  probePt.matrixTransform(mapSvgElem.getScreenCTM());
    return [cursorPt.x, cursorPt.y];
}
