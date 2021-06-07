"use strict";
function ControllerMapInteractions() {
    // state
    let markerSelection = [];
    let rectSelectionCorner = undefined;
    let markerMovement = false;
    let movementStartPoint = undefined;

    // map interaction mode
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
    function toggleSelectMode() {
        const control = document.getElementById('menu_actions_option2');
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
    function _pasteMarkerHelper(clipboardContent) {
        clipMarkers(clipboardContent,
            function (rep) {
            dropSelection();
            for (const elem of rep.created) {
                renderMarkerElement(elem);
                addToSelection(elem.marker);
            }
            markerCirclesManager.render(mapInteractionsController.isInSelection);
        });
    }

    // map interaction handlers
    function handleKeyUp(e) {
        // console.log(e);
        if (e.code === 'Backspace' && UI_AUTH) {
            _deleteRoutine(markerSelection);
        } else if (e.code === 'Escape') {
            dropSelection();
            markerCirclesManager.render(mapInteractionsController.isInSelection);
        } else if (e.code === 'KeyI') {
            messageBoxManager.showSelected(mapInteractionsController.isInSelection);
        }
    }
    function handleKeyPress(e) {
        if (!UI_AUTH) return;   // modification will fail in guest mode
        if (e.code === 'KeyQ') {
            const acceleration = e.shiftKey;
            handleRotationNegative(acceleration);
        } else if (e.code === 'KeyE') {
            const acceleration = e.shiftKey;
            handleRotationPositive(acceleration);
        }
    }
    function handleClickMap(e) {
        // console.log('handleClickMap');
        const [svgX, svgY] = getSvgCoordinates(e);
        const inside = mapScaleController.isInsideMapRect(svgX, svgY);
        if (!inside)
            return;

        // debugger;
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
        if (isInsertMode())
            return;

        messageBoxManager.hideAll();

        const maybeCircleElement = e.target;
        const movementAllowed = UI_AUTH;    // modification will fail in guest mode
        markerMovement = movementAllowed
            && maybeCircleElement.classList.contains('marker_circle');

        if (!markerMovement) {
            rectSelectionCorner = getSvgCoordinates(e);
            const [xInit, yInit] = _takeSelectionRect(getSvgCoordinates(e), false);
            _boundSelectionRect(xInit, yInit);
            _toggleSelectionRect(true);
        }
        else {
            movementStartPoint = getSvgCoordinates(e);
            const markerUid = maybeCircleElement.dataset.markerUid;
            if (!isInSelection(markerUid)) {
                if (!e.shiftKey) {
                    dropSelection();
                }
                addToSelection(markerUid);
                markerCirclesManager.render(mapInteractionsController.isInSelection);
            }
        }

        mapScaleController.mapSvg().addEventListener('mousemove', mapInteractionsController.handleMouseMove);
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
        // console.log('handleMouseUp', e);
        mapScaleController.mapSvg().removeEventListener('mousemove', mapInteractionsController.handleMouseMove);

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

    function handleRotationPositive(accelerated) {
        const rotationDelta = (accelerated ? 10 : 1);
        markerCirclesManager.updateRotation(getSelection(), rotationDelta);
    }
    function handleRotationNegative(accelerated) {
        const rotationDelta = (accelerated ? -10 : -1);
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
            let payload = decodeClipboardContent(text);
            payload.project = mapInteractionsController.getProjectUid();
            payload.page = mapInteractionsController.pageCode();

            // console.debug('Paste!', payload);
            _pasteMarkerHelper(payload);
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

    return {
        isInsertMode: isInsertMode,
        isSelectMode: isSelectMode,
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
