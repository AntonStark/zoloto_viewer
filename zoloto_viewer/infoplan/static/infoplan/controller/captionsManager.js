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
            // todo append move handlers
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

    return {
        showAll: showAllCaptions,
        hideALl: hideAllCaptions,
    }
}
