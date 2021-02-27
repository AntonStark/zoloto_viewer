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
    //    todo sync selection after delete
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
        if (e.code === 'Backspace') {
            _deleteRoutine(markerSelection);
        } else if (e.code === 'Escape') {
            dropSelection();
        } else if (e.code === 'KeyI') {
            messageBoxManager.showSelected(mapInteractionsController.isInSelection);
        } else if (e.code === 'KeyQ') {
            const acceleration = e.shiftKey;
            handleRotationNegative(acceleration);
        } else if (e.code === 'KeyE') {
            const acceleration = e.shiftKey;
            handleRotationPositive(acceleration);
        }
    }
    function handleClickMap(e) {
        const [svgX, svgY] = getSvgCoordinates(e);
        // console.debug(svgX, svgY, activeLayer(), getPageCode());

        messageBoxManager.hideAll();
        dropSelection();

        if (isInsertMode()) {
            _createHelper(svgX, svgY);
        }

        markerCirclesManager.render(mapInteractionsController.isInSelection);
    }
    function handleClickMarkerCircle(e) {
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
    }

    function _takeSelectionRect(secondCorner, reset=true) {
        const xCoords = [rectSelectionCorner[0], secondCorner[0]];
        const yCoords = [rectSelectionCorner[1], secondCorner[1]];
        if (reset) {
            rectSelectionCorner = undefined;
        }
        return [xCoords, yCoords];
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
    function handleDragStart(e) {
        // console.log('handleDragStart', e);

        rectSelectionCorner = getSvgCoordinates(e);
        const [xInit, yInit] = _takeSelectionRect(getSvgCoordinates(e), false);
        _boundSelectionRect(xInit, yInit);
        _toggleSelectionRect(true);

        mapScaleController.mapSvg().addEventListener('mousemove', mapInteractionsController.handleDragMove);
    }
    function handleDragMove(e) {
        const [xCoords, yCoords] = _takeSelectionRect(getSvgCoordinates(e), false);
        _boundSelectionRect(xCoords, yCoords);
    }
    function handleDragEnd(e) {
        // console.log('handleDragEnd', e);
        mapScaleController.mapSvg().removeEventListener('mousemove', mapInteractionsController.handleDragMove);

        const [xCoords, yCoords] = _takeSelectionRect(getSvgCoordinates(e));
        console.log('setSelectionRect', xCoords, yCoords);
        markerCirclesManager.setSelectionRect(xCoords, yCoords);
        _toggleSelectionRect(false);

        markerCirclesManager.render(markerCirclesManager.isInsideSelectionRect, toggleIsSelected);
        // console.log(rect);

        // debugger;
    }

    function handleRotationPositive(accelerated) {
        markerCirclesManager.updateRotation(getSelection(), true, accelerated);
    }
    function handleRotationNegative(accelerated) {
        markerCirclesManager.updateRotation(getSelection(), false, accelerated);
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
        handleClickMap          : handleClickMap,
        handleClickMarkerCircle : handleClickMarkerCircle,

        handleDragStart : handleDragStart,
        handleDragMove  : handleDragMove,
        handleDragEnd   : handleDragEnd,

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
