"use strict";
function ControllerCaptions() {
    let captionsIndex = {};

    function showAllCaptions() {
        hideAllCaptions();
        const floor = mapInteractionsController.pageCode();
        requestCaptionsPlacement(floor, _renderFloorCaptionsData);
    }
    function hideAllCaptions() {
        for (const [markerUid, caption] of Object.entries(captionsIndex)) {
            _removeDomElement(caption);
            delete captionsIndex[markerUid];
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
            if (captionMovement) {
                movementTarget = maybeCaptionGroup;
                break;
            }
        }
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
        const endPoint = getSvgCoordinates(e);
        const moveOffset = [endPoint[0] - movementStartPoint[0], endPoint[1] - movementStartPoint[1]];
        // send new offset and rotation and update from response
        const originOffset = JSON.parse(movementTarget.dataset.originOffset);
        const totalOffset = [originOffset[0] + moveOffset[0], originOffset[1] + moveOffset[1]];
        _updateHelper(movementTarget, totalOffset);

        captionMovement = false;
        movementStartPoint = movementTarget = undefined;
    }

    function handleClickRotate(e) {
        let maybeCaptionGroup, isCaptionGroupTarget, captionGroupTarget;
        for (maybeCaptionGroup of e.path) {
            // console.log('maybeCaptionGroup', maybeCaptionGroup);
            isCaptionGroupTarget = maybeCaptionGroup.classList.contains('caption_group');
            if (isCaptionGroupTarget) {
                captionGroupTarget = maybeCaptionGroup;
                break;
            }
        }
        // console.log('caption_rotator', markerUid, e, captionGroupTarget);
        const isAlreadyRotated = captionGroupTarget.dataset.isRotated;
        const newRotation = ( isAlreadyRotated === 'true' ? 0 : 90);
        _updateHelper(captionGroupTarget, undefined, newRotation);
    }

    function _updateHelper(captionGroup, offset=undefined, rotation=undefined) {
        function successHandler(rep) {
            //    {
            //     "data": {
            //         "offset": [
            //             -10.8582763671875,
            //             69.2216796875
            //         ],
            //         "rotation": 0
            //     },
            //     "marker": {
            //         "marker": "96b8a36f-2333-4312-aa69-f006b1feb50a",
            //         "number": "110_S/L2/2",
            //         "position": {
            //             "center_x": 1268,
            //             "center_y": 651,
            //             "rotation": 91
            //         },
            //         "layer": "110_S"
            //     }
            // }
            console.log('successHandler', rep.data.offset);
            setupCaptionGroupGeometryDataset(captionGroup, rep);
            console.log('after setupCaptionGroupGeometryDataset', captionGroup.dataset.captionOffset)
            applyProperTransform(captionGroup);
        }
        const markerUid = captionGroup.dataset.markerUid;
        console.log('_updateHelper', offset);
        updateCaptionPlacement(markerUid, offset, rotation, successHandler);
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
