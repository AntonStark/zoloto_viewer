"use strict";
function ControllerCaptions() {
    function showAllCaptions() {
        //    запросить все данные
        //    и для каждого объекта в массиве ответа
        //    вызвать рендер
        const floor = mapInteractionsController.pageCode();
        requestCaptionsPlacement(floor, _renderFloorCaptionsData);
    }
    function hideAllCaptions() {

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
            // todo append move handlers
        }
    }

    return {
        showAll: showAllCaptions,
        hideALl: hideAllCaptions,
    }
}
