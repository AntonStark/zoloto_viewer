"use strict";
function ControllerMapScale() {
    const POSSIBLE_SCALES = [100, 125, 150, 200];
    let scaleIndex = 0;
    let mapObj = undefined;
    let svgOrigin = undefined;
    let scrollDiv = undefined;
    let originalSize = undefined;


    function setMapObj() {
        mapObj = document.getElementById('project-page-plan-svg');
        originalSize = [mapObj.width.baseVal.value, mapObj.height.baseVal.value];

        svgOrigin = document.getElementById('project-page-svg-origin');
        scrollDiv = document.getElementById('project-page-plan-box')
            .getElementsByClassName('scrollable')[0];
    }
    function currentScale() {
        return POSSIBLE_SCALES[scaleIndex] / 100;
    }
    function getOriginalSize() {
        return originalSize;
    }
    function mapRect() {
        return mapObj.getBoundingClientRect();
    }

    function couldIncrease() {
        return scaleIndex < (POSSIBLE_SCALES.length - 1);
    }
    function couldDecrease() {
        return scaleIndex > 0;
    }

    function _setScaled() {
        const scale = currentScale();
        // const deltaFactor = scale - 1;    // relative size of difference of scaled plan over original
        // const width = mapObj.width.baseVal.value;
        // const height = mapObj.height.baseVal.value;
        // const transform = `translate(${deltaFactor * width / 2}, ${deltaFactor * height / 2}) scale(${scale})`;
        const transform = `scale(${scale})`;
        svgOrigin.setAttribute('transform', transform);

        mapObj.setAttribute('width', scale * originalSize[0]);
        mapObj.setAttribute('height', scale * originalSize[1]);
    }
    function _setNormal() {
        svgOrigin.removeAttribute('transform');
        mapObj.setAttribute('width', originalSize[0]);
        mapObj.setAttribute('height', originalSize[1]);
    }
    function displayScale() {
        if (scaleIndex > 0)
            _setScaled();
        else
            _setNormal();

        messageBoxManager.onMapScaleChange();
    }

    function increase() {
        // to preserve central point  (scrollLeft + clientWidth/2) / scrollWidth
        const relX = (scrollDiv.scrollLeft + scrollDiv.clientWidth / 2.) / scrollDiv.scrollWidth;
        const relY = (scrollDiv.scrollTop + scrollDiv.clientHeight / 2.) / scrollDiv.scrollHeight;

        ++scaleIndex;
        displayScale();

        scrollDiv.scrollLeft = relX * scrollDiv.scrollWidth - scrollDiv.clientWidth / 2.;
        scrollDiv.scrollTop = relY * scrollDiv.scrollHeight - scrollDiv.clientHeight / 2.;
        return couldIncrease();
    }
    function decrease() {
        const relX = (scrollDiv.scrollLeft + scrollDiv.clientWidth / 2.) / scrollDiv.scrollWidth;
        const relY = (scrollDiv.scrollTop + scrollDiv.clientHeight / 2.) / scrollDiv.scrollHeight;

        --scaleIndex;
        displayScale();

        scrollDiv.scrollLeft = relX * scrollDiv.scrollWidth - scrollDiv.clientWidth / 2.;
        scrollDiv.scrollTop = relY * scrollDiv.scrollHeight - scrollDiv.clientHeight / 2.;
        return couldDecrease();
    }

    return {
        setup: setMapObj,
        current: currentScale,
        origSize: getOriginalSize,
        mapRect: mapRect,

        couldIncrease: couldIncrease,
        couldDecrease: couldDecrease,

        increase: increase,
        decrease: decrease,
    }
}
