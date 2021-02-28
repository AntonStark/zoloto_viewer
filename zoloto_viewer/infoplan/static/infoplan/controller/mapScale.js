"use strict";
function ControllerMapScale() {
    const POSSIBLE_SCALES = PAGE_CONFIG.map_scale_factors;
    let scaleIndex = 0;
    let mapObj = undefined;
    let mapBackground = undefined;
    let mapImage = undefined;
    let scrollDiv = undefined;
    let originalSize = undefined;


    function setMapObj() {
        mapObj = document.getElementById('project-page-plan-svg');
        originalSize = [mapObj.width.baseVal.value, mapObj.height.baseVal.value];

        mapImage = document.getElementById('project-page-svg-plan-image');
        scrollDiv = document.getElementById('project-page-plan-box')
            .getElementsByClassName('scrollable')[0];
    }
    function currentScale() {
        return POSSIBLE_SCALES[scaleIndex] / 100;
    }
    function getOriginalSize() {
        return originalSize;
    }
    function getMapObj() {
        return mapObj;
    }
    function isInsideMapRect(x, y) {
        const box = mapImage.getBBox();
        return (
            box.x <= x && x < box.x + box.width
            && box.y <= y && y < box.y + box.height
        );
    }

    function couldIncrease() {
        return scaleIndex < (POSSIBLE_SCALES.length - 1);
    }
    function couldDecrease() {
        return scaleIndex > 0;
    }

    function _setScaled() {
        const scale = currentScale();
        // const transform = `scale(${scale})`;
        // svgOrigin.setAttribute('transform', transform);

        mapObj.style.height = 'initial';
        mapObj.style.width = 'initial';

        mapObj.setAttribute('width', scale * originalSize[0]);
        mapObj.setAttribute('height', scale * originalSize[1]);
    }
    function _setNormal() {
        // svgOrigin.removeAttribute('transform');

        mapObj.style.height = '';
        mapObj.style.width = '';

        mapObj.removeAttribute('width');
        mapObj.removeAttribute('height');
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
        mapSvg: getMapObj,
        isInsideMapRect: isInsideMapRect,

        couldIncrease: couldIncrease,
        couldDecrease: couldDecrease,

        increase: increase,
        decrease: decrease,
    }
}


function markersScaleChange(input) {
    input.dataset.changed = input.value !== input.dataset.initial;
}
function markersScaleSubmit() {
    const factor = Number.parseInt(document.getElementById('actions_menu_scale_markers').value)
    doApiCall('PUT', API_PUT_PAGE_DATA(PAGE_CONFIG.code), {
        marker_size_factor: factor
    },
        (rep) => {document.location.reload();},
        (rep) => {console.log(rep); alert('Возникла ошибка.')});
    return false;
}
