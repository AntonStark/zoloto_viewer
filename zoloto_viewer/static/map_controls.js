const mapScaleController = function() {
    const POSSIBLE_SCALES = [100, 125, 150, 200];
    let scaleIndex = 0;
    let mapObj = undefined;
    let scrollDiv = undefined;


    function setMapObj() {
        mapObj = document.getElementById('project-page-plan-svg');
        scrollDiv = document.getElementById('project-page-plan-box')
            .getElementsByClassName('scrollable')[0];
    }
    function currentScale() {
        return POSSIBLE_SCALES[scaleIndex] / 100;
    }

    function couldIncrease() {
        return scaleIndex < (POSSIBLE_SCALES.length - 1);
    }
    function couldDecrease() {
        return scaleIndex > 0;
    }

    function _setScaled() {
        const scale = currentScale();
        const deltaFactor = scale - 1;    // relative size of difference of scaled plan over original
        const width = mapObj.width.baseVal.value;
        const height = mapObj.height.baseVal.value;
        const transform = `translate(${deltaFactor * width / 2}, ${deltaFactor * height / 2}) scale(${scale})`;
        mapObj.setAttribute('transform', transform);
    }
    function _setNormal() {
        mapObj.removeAttribute('transform');
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

        couldIncrease: couldIncrease,
        couldDecrease: couldDecrease,

        increase: increase,
        decrease: decrease,
    }
}();


function handleClickMapPlus() {
    if (!mapScaleController.couldIncrease())
        return;
    mapScaleController.increase();
    updateControlStyle();
}

function handleClickMapMinus() {
    if (!mapScaleController.couldDecrease())
        return;
    mapScaleController.decrease();
    updateControlStyle();
}

function setHandlers() {
    mapScaleController.setup();
    document.getElementById('map_control_plus').addEventListener('click', handleClickMapPlus);
    document.getElementById('map_control_minus').addEventListener('click', handleClickMapMinus);
}
window.addEventListener('load', setHandlers);

function updateControlStyle() {
    const plus = document.getElementById('map_control_plus');
    if (plus.classList.contains('disabled') !== !mapScaleController.couldIncrease())
        plus.classList.toggle('disabled');

    const minus = document.getElementById('map_control_minus');
    if (minus.classList.contains('disabled') !== !mapScaleController.couldDecrease())
        minus.classList.toggle('disabled');
}