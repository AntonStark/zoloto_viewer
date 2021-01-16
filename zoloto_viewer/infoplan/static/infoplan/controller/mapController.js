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
    function clickHandler(e) {
        const [svgX, svgY] = [e.offsetX, e.offsetY];
        console.log(svgX, svgY);
    }
    function keyUpHandler(e) {
        console.log(e);
    }

    return {
        isInsertMode: isInsertMode,
        isSelectMode: isSelectMode,

        isInSelection: isInSelection,
        addToSelection: addToSelection,
        dropSelection: dropSelection,

        clickHandler: clickHandler,
        keyUpHandler: keyUpHandler,
    }
}
