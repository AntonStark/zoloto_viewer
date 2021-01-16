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
    }
    function handleClickMap(e) {
        messageBoxManager.hideAll();
        const [svgX, svgY] = [e.offsetX, e.offsetY];
        console.log(svgX, svgY);
    }
    function handleClickMarkerCircle(circleElement) {
        const markerUid = circleElement.dataset.markerUid;
        const markerElement = circleElement.parentNode.previousElementSibling;
        messageBoxManager.reg(markerElement);

        markerCirclesManager.register(circleElement);

        const messLink = circleElement.parentNode.getElementsByClassName('marker_link')[0];
        messLinksManager.register(markerUid, messLink);

        // messageBoxManager.hideAll();
        messageBoxManager.show(markerUid);
    }


    return {
        isInsertMode: isInsertMode,
        isSelectMode: isSelectMode,

        isInSelection: isInSelection,
        addToSelection: addToSelection,
        dropSelection: dropSelection,

        handleKeyUp: handleKeyUp,
        handleClickMap: handleClickMap,
        handleClickMarkerCircle: handleClickMarkerCircle,
    }
}
