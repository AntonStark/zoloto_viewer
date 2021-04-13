"use strict";
function ControllerMapInteractions() {
    // state
    let markerSelection = [];
    let rectSelectionCorner = undefined;

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
    function activeLayer()
    { return enabledLayersController.getActive(); }
    function getPageCode()
    { return pageCode; }

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
    function handleClickMarkerCircle(e) {
        // console.log('handleClickMarkerCircle');

        const circleElement = e.target;
        const markerUid = circleElement.dataset.markerUid;

        messageBoxManager.hideAll();
        if (isSelectMode()) {
            if (e.shiftKey) {
                addToSelection(markerUid);
            } else {
                dropSelection();
                addToSelection(markerUid);
            }
        }

        const markerElement = circleElement.parentNode.previousElementSibling;
        messageBoxManager.reg(markerElement);

        markerCirclesManager.render(mapInteractionsController.isInSelection);
        // e.stopPropagation();
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
    function handleMouseDown(e) {
        // console.log('handleMouseDown', e);
        if (isInsertMode())
            return;

        messageBoxManager.hideAll();
        rectSelectionCorner = getSvgCoordinates(e);
        const [xInit, yInit] = _takeSelectionRect(getSvgCoordinates(e), false);
        _boundSelectionRect(xInit, yInit);
        _toggleSelectionRect(true);

        mapScaleController.mapSvg().addEventListener('mousemove', mapInteractionsController.handleMouseMove);
    }
    function handleMouseMove(e) {
        const [xCoords, yCoords] = _takeSelectionRect(getSvgCoordinates(e), false);
        _boundSelectionRect(xCoords, yCoords);
    }
    function handleMouseUp(e) {
        // console.log('handleMouseUp', e);
        mapScaleController.mapSvg().removeEventListener('mousemove', mapInteractionsController.handleMouseMove);
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

    function handleCopyEvent() {
        console.log('Copy!');
    }
    function handlePasteEvent() {
        console.log('Paste!');
    }

    return {
        isInsertMode: isInsertMode,
        isSelectMode: isSelectMode,
        activeLayer : activeLayer,
        pageCode    : getPageCode,

        isInSelection   : isInSelection,
        addToSelection  : addToSelection,
        dropSelection   : dropSelection,
        getSelection    : getSelection,
        toggleIsSelected: toggleIsSelected,

        handleKeyUp             : handleKeyUp,
        handleKeyPress          : handleKeyPress,
        handleClickMarkerCircle : handleClickMarkerCircle,

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
