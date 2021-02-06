"use strict";
function ControllerMapInteractions() {
    // state
    let markerSelection = [];

    // map interaction mode
    function isInsertMode()
    { return document.getElementById('menu_actions_option1').checked; }
    function isSelectMode()
    { return document.getElementById('menu_actions_option2').checked; }
    function activeLayer()
    { return enabledLayersController.getActive(); }
    function getPageCode()
    { return pageCode; }

    // marker selection
    function isInSelection(markerUid) {
        return markerSelection.indexOf(markerUid) !== -1;
    }
    function addToSelection(markerUid) {
        markerSelection.push(markerUid);
    }
    function dropSelection() {
        markerSelection.splice(0, markerSelection.length);
    }

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
    //    todo syns selection after delete
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
        console.log(e);
        if (e.key === 'Backspace') {
            _deleteRoutine(markerSelection);
        } else if (
            (e.key === 'i' || e.key === 'ш')
            // && (e.ctrlKey || e.metaKey)
        ) {
            messageBoxManager.showSelected(mapInteractionsController.isInSelection);
        }

    }
    function handleClickMap(e) {
        const [svgX, svgY] = [e.offsetX, e.offsetY];
        console.debug(svgX, svgY, activeLayer(), getPageCode());

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
        const messLink = circleElement.parentNode.getElementsByClassName('marker_link')[0];
        messLinksManager.register(markerUid, messLink);

        markerCirclesManager.render(mapInteractionsController.isInSelection);
    }


    return {
        isInsertMode: isInsertMode,
        isSelectMode: isSelectMode,
        activeLayer : activeLayer,
        pageCode    : getPageCode,

        isInSelection   : isInSelection,
        addToSelection  : addToSelection,
        dropSelection   : dropSelection,

        handleKeyUp             : handleKeyUp,
        handleClickMap          : handleClickMap,
        handleClickMarkerCircle : handleClickMarkerCircle,
    }
}
