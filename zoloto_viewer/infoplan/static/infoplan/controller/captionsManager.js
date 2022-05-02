"use strict";
function ControllerCaptions() {
    let captionsIndex = {};

    function showAllCaptions() {
        const floor = mapInteractionsController.pageCode();
        requestCaptionsPlacement(floor, _renderFloorCaptionsData);
    }
    function hideAllCaptions() {
        for (const [markerUid, caption] of Object.entries(captionsIndex)) {
            _removeDomElement(caption);
        }
    }

    function _renderFloorCaptionsData(rep) {
        for (const capData of rep.data) {
            console.log(capData);
            renderCaptionElement(capData);
        }
        _postRenderProcessing();
    }

    function _postRenderProcessing() {
        const captionGroupList = document.getElementsByClassName('caption_group');
        for (const captionGroup of captionGroupList) {
            // prepend every caption's group with background rect
            insertBackground(captionGroup);
            applyProperTransform(captionGroup);
            _registerCaptionGroup(captionGroup);
            _setMoveHandlers(captionGroup);
        }
    }

    function _registerCaptionGroup(captionGroup) {
        const markerUid = captionGroup.dataset.markerUid;
        console.log(markerUid);
        captionsIndex[markerUid] = captionGroup;
    }
    function _removeDomElement(captionGroup) {
        captionGroup.parentNode.removeChild(captionGroup);
        captionGroup = null;
    }
    function _setMoveHandlers(captionGroup) {
        const caption = captionGroup.getElementsByClassName('caption')[0]
        if (caption) {
            caption.addEventListener('mousedown', captionsController.handleMouseDown);
            caption.addEventListener('mouseup', captionsController.handleMouseUp);
        }

        const rotator = captionGroup.getElementsByClassName('caption_rotator')[0]
        if (rotator) {
            rotator.addEventListener('click', captionsController.handleClickRotate);
        }
    }

    let captionMovement = false;
    let movementTarget = undefined;
    let movementStartPoint = undefined;

    function handleMouseDown(e) {
        if (!mapInteractionsController.isCaptionsMode())
            return;

        messageBoxManager.hideAll();
        const movementAllowed = UI_AUTH;    // modification will fail in guest mode
        let maybeCaptionGroup;
        for (maybeCaptionGroup of e.path) {
            // console.log('maybeCaptionGroup', maybeCaptionGroup);
            captionMovement = maybeCaptionGroup.classList.contains('caption_group');
            if (captionMovement)
                break;
        }
        movementTarget = maybeCaptionGroup;
        // console.log('handleMouseDown', 'captionMovement=', captionMovement, 'movementAllowed=', movementAllowed);

        movementStartPoint = getSvgCoordinates(e);
        if (movementAllowed && captionMovement) {
            mapScaleController.mapSvg().addEventListener('mousemove', captionsController.handleMouseMove);
        }
        e.stopPropagation();
    }
    function handleMouseMove(e) {
        const endPoint = getSvgCoordinates(e);
        const moveOffset = [endPoint[0] - movementStartPoint[0], endPoint[1] - movementStartPoint[1]];
        updateCaptionPosition(movementTarget, moveOffset);
    }
    function handleMouseUp(e) {
        // console.log('handleMouseUp', 'captionsController', e);
        // remove throw mapInteractionsController.handleMouseUp
        // mapScaleController.mapSvg().removeEventListener('mousemove', captionsController.handleMouseMove);

        const endPoint = getSvgCoordinates(e);
        const moveOffset = [endPoint[0] - movementStartPoint[0], endPoint[1] - movementStartPoint[1]];
        // console.log(movementTarget.dataset);
        // _updateHelper()

        captionMovement = false;
        movementStartPoint = movementTarget = undefined;
    //    todo послать на сервер и обновить из ответа рендер-параметры: x, y, dataset...
    }

    function handleClickRotate(e) {
        console.log('caption_rotator');
    }

    function _updateHelper(offset, rotation) {
        updateCaptionPlacement()
    }

    return {
        showAll: showAllCaptions,
        hideALl: hideAllCaptions,

        handleMouseDown : handleMouseDown,
        handleMouseMove : handleMouseMove,
        handleMouseUp   : handleMouseUp,
        handleClickRotate: handleClickRotate,
    }
}
