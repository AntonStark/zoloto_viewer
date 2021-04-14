"use strict";
function ControllerMarkerCircles() {
    const MARKER_CORRECT_CLASS = 'marker_correct';
    const MARKER_INCORRECT_CLASS = 'marker_wrong';
    const MARKER_REVIEWED_CLASS = 'marker_reviewed';
    const MARKER_HAS_COMMENT_CLASS = 'marker_has_comment';
    const MARKER_MESSAGE_SHOWN_CLASS = 'message_shown';

    let markerCorrCircles = {};         // marker_uid -> SvgCircleElement
    let circleCenterIndex = {};         // marker_uid -> [x, y]
    let selectionRect = undefined;

    let markersTouched = new Set();     // { marker_uid, }
    let timerApplyChanges = undefined;

    function _setCorrectness(element, correct) {
        if (correct === null)
            return;
        if (element.classList.contains(MARKER_CORRECT_CLASS) !== correct)
            element.classList.toggle(MARKER_CORRECT_CLASS);
        if (element.classList.contains(MARKER_INCORRECT_CLASS) !== !correct)
            element.classList.toggle(MARKER_INCORRECT_CLASS);
    }
    function _setReviewed(element, reviewed) {
        if (!element)
            return;
        if (element.classList.contains(MARKER_REVIEWED_CLASS) !== reviewed)
            element.classList.toggle(MARKER_REVIEWED_CLASS);
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
            const [reviewed, hasComment] = [markerData.reviewed, markerData.has_comment];
            // _setCorrectness(elem.parentNode, null);
            _setReviewed(elem.nextElementSibling, reviewed);
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
        // todo respect visibility
        const res = _getCircleCenterSvgCoord(markerUid);
        if (!res)
            throw Error('circle element not registered');

        const [x, y] = res;
        const [xBounds, yBounds] = selectionRect;
        // console.log('isInsideSelectionRect', xBounds, yBounds);
        // noinspection UnnecessaryLocalVariableJS
        const isIn = (xBounds[0] <= x && x < xBounds[1])
            && (yBounds[0] <= y && y < yBounds[1]);
        return isIn;
    }

    function _addMarkersTouched(markerUidArray) {
        for (const markerUid of markerUidArray) {
            markersTouched.add(markerUid);
        }
    }
    function _clearMarkersTouched()
    { markersTouched.clear(); }
    function _saveGeometryFromUI() {
        for (const markerUid of markersTouched.values()) {
            const m = markerPosition(markerUid);
            if (!m)
                return;
            // 'pos_x', 'pos_y', 'rotation'
            doApiCall('PATCH', API_MARKER_PATCH_GEOM(markerUid), {
                pos_x: Number.parseInt(m.pos_x),
                pos_y: Number.parseInt(m.pos_y),
                rotation: Number.parseInt(m.rotation),
            })
        }
    }

    function markerPosition(markerUid) {
        const marker = messageBoxManager.getMarker(markerUid);
        if (!marker)
            return;

        return {
            pos_x: marker.getAttribute('x'),
            pos_y: marker.getAttribute('y'),
            rotation: marker.transform.animVal[0].angle,
        };
    }
    function _rotationHelper(markerUid, delta) {
        // todo markerCircles -> markers
        //  and this encapsulates markerElements too (rather than messageBoxManager)
        const m = markerPosition(markerUid);
        if (!m)
            return;

        const marker = messageBoxManager.getMarker(markerUid);
        marker.setAttribute('transform', `rotate(${m.rotation + delta} ${m.pos_x} ${m.pos_y})`);
        _addMarkersTouched([markerUid]);
    }
    function updateRotation(markerUidArray, delta) {
        for (const markerUid of markerUidArray) {
            _rotationHelper(markerUid, delta);
        }

        if (timerApplyChanges)
            window.clearTimeout(timerApplyChanges);
        timerApplyChanges = window.setTimeout(function () {
            _saveGeometryFromUI();
            _clearMarkersTouched();
        }, 500);
    }

    // регистрируем все circleElement при создании контроллера
    function init() {
        const svgElem = document.getElementById('project-page-plan-svg');
        for (const circleElement of svgElem.getElementsByClassName('marker_circle')) {
            registerMarkerCircle(circleElement);

            const markerElement = circleElement.parentNode.previousElementSibling;
            messageBoxManager.reg(markerElement);
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
        isInsideSelectionRect   : isInsideSelectionRect,
        updateRotation  : updateRotation,
    }
}
