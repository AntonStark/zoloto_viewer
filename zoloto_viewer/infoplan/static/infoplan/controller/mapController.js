"use strict";
function ControllerMapInteractions() {
    // state
    let markerSelection = [];

    // map interaction mode
    function isInsertMode() {
        return document.getElementById('menu_actions_option1').checked;
    }
    function isSelectMode() {
        return document.getElementById('menu_actions_option2').checked;
    }
    function activeLayer() {
        return enabledLayersController.getActive();
    }

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

    // map interaction handlers
    function handleKeyUp(e) {
        console.log(e);
        if (e.key === 'Backspace') {
            deleteRoutine(markerSelection);
        }

    }
    function handleClickMap(e) {
        messageBoxManager.hideAll();
        dropSelection();

        const [svgX, svgY] = [e.offsetX, e.offsetY];
        console.log(svgX, svgY, activeLayer());
        markerCirclesManager.render(mapInteractionsController.isInSelection);
    }
    function handleClickMarkerCircle(circleElement) {
        const markerUid = circleElement.dataset.markerUid;

        addToSelection(markerUid);

        const markerElement = circleElement.parentNode.previousElementSibling;
        messageBoxManager.reg(markerElement);

        markerCirclesManager.register(circleElement);

        const messLink = circleElement.parentNode.getElementsByClassName('marker_link')[0];
        messLinksManager.register(markerUid, messLink);

        // messageBoxManager.hideAll();
        messageBoxManager.show(markerUid);
        markerCirclesManager.render(mapInteractionsController.isInSelection);
    }


    return {
        isInsertMode: isInsertMode,
        isSelectMode: isSelectMode,
        activeLayer : activeLayer,

        isInSelection   : isInSelection,
        addToSelection  : addToSelection,
        dropSelection   : dropSelection,

        handleKeyUp             : handleKeyUp,
        handleClickMap          : handleClickMap,
        handleClickMarkerCircle : handleClickMarkerCircle,
    }
}

function deleteRoutine(markerUidArray) {
    console.debug('deleteRoutine', markerUidArray);
    for (const markerUid of markerUidArray) {
        deleteMarker(markerUid);
    }
}
