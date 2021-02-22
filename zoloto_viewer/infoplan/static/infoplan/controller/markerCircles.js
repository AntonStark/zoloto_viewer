"use strict";
function ControllerMarkerCircles() {
    const MARKER_CORRECT_CLASS = 'marker_correct';
    const MARKER_INCORRECT_CLASS = 'marker_wrong';
    const MARKER_HAS_COMMENT_CLASS = 'marker_has_comment';
    const MARKER_MESSAGE_SHOWN_CLASS = 'message_shown';

    let markerCorrCircles = {};         // marker_uid -> SvgCircleElement
    let circleCenterIndex = {};         // marker_uid -> [x, y]
    let selectionRect = undefined;

    function _setCorrectness(element, correct) {
        if (correct === null)
            return;
        if (element.classList.contains(MARKER_CORRECT_CLASS) !== correct)
            element.classList.toggle(MARKER_CORRECT_CLASS);
        if (element.classList.contains(MARKER_INCORRECT_CLASS) !== !correct)
            element.classList.toggle(MARKER_INCORRECT_CLASS);
    }
    function _setHasComment(element, has) {
        if (!element)
            return;
        if (element.classList.contains(MARKER_HAS_COMMENT_CLASS) !== has)
            element.classList.toggle(MARKER_HAS_COMMENT_CLASS);
    }
    function _setMessShown(element, isShown) {
        if (!element)
            return;
        if (element.classList.contains(MARKER_MESSAGE_SHOWN_CLASS) !== isShown)
            element.classList.toggle(MARKER_MESSAGE_SHOWN_CLASS);
    }
    function _setShownStatus(markerUid, isShown) {
        const elem = markerCorrCircles[markerUid];
        _setMessShown(elem.parentNode, isShown);
        // console.debug('setShownStatus', markerUid, isShown);
    }
    function _evalViewportPosition(circleElement) {
        const transform = circleElement.getCTM();
        let probe = circleElement.ownerSVGElement.createSVGPoint();
        probe.x = circleElement.cx.baseVal.value;
        probe.y = circleElement.cy.baseVal.value;
        probe = probe.matrixTransform(transform);
        const scale = mapScaleController.current();
        return [probe.x / scale, probe.y / scale];
    }

    function registerMarkerCircle(circleElement) {
        const markerUid = circleElement.dataset.markerUid;
        markerCorrCircles[markerUid] = circleElement;
        circleCenterIndex[markerUid] = _evalViewportPosition(circleElement);
    }
    function deleteMarkerCircleGroup(markerUid) {
        markerCorrCircles[markerUid].parentNode.remove();
        delete markerCorrCircles[markerUid];
    }
    function updateCorrectness(markerData) {
        // console.log('updateCorrectness', markerData);
        const elem = markerCorrCircles[markerData.marker];
        if (elem !== undefined) {
            const [correct, hasComment] = [markerData.correct, markerData.has_comment];
            _setCorrectness(elem.parentNode, correct);
            _setHasComment(elem.nextElementSibling, hasComment);
        }
    }
    function getCircleCenter(markerUid) {
        return circleCenterIndex[markerUid];
    }
    function _getCircleCenterSvgCoord(markerUid) {
        const circleElement = markerCorrCircles[markerUid];
        if (!circleElement) return;

        return [circleElement.cx.baseVal.value, circleElement.cy.baseVal.value];
    }

    function setSelectionRect(xBounds, yBounds) {
        if (!(xBounds[0] < xBounds[1])) {
            xBounds = xBounds.reverse();
        }
        if (!(yBounds[0] < yBounds[1])) {
            yBounds = yBounds.reverse();
        }

        selectionRect = [xBounds, yBounds];
        // console.log(selectionRect[0], selectionRect[1]);
    }
    function isInsideSelectionRect(markerUid) {
        // return true if center coord is inside specified selection
        const res = _getCircleCenterSvgCoord(markerUid);
        if (!res) return false;

        const [x, y] = res;
        const [xBounds, yBounds] = selectionRect;
        console.log('isInsideSelectionRect', xBounds, yBounds);
        return (
            (xBounds[0] <= x && x < xBounds[1]) &&
            (yBounds[0] <= y && y < yBounds[1])
        )
    }

    // регистрируем все circleElement при создании контроллера
    function init() {
        const svgElem = document.getElementById('project-page-plan-svg');
        for (const circleElement of svgElem.getElementsByClassName('marker_circle')) {
            registerMarkerCircle(circleElement);
        }
    }
    function renderSelection(isInSelectionMethod, toggleSelected=undefined) {
        for (const markerUid in markerCorrCircles) {
            const isIn = isInSelectionMethod(markerUid);
            _setShownStatus(markerUid, isIn);
            if (toggleSelected) {
                toggleSelected(markerUid, isIn);
            }
        }
    }

    return {
        init    : init,
        register: registerMarkerCircle,
        delete  : deleteMarkerCircleGroup,
        sync    : updateCorrectness,
        position: getCircleCenter,
        render  : renderSelection,

        setSelectionRect: setSelectionRect,
        isInsideSelectionRect: isInsideSelectionRect,
        circleCenterIndex: circleCenterIndex,   // fixme remove
    }
}
