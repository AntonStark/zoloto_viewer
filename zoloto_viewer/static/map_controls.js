const mapController = (function() {
    let mapObj = undefined;
    let scrollDiv = undefined;
    function setMapObj() {
        mapObj = document.getElementById('project-page-plan-svg');
        scrollDiv = document.getElementById('project-page-plan-box')
            .getElementsByClassName('scrollable')[0];
    }

    const possibleScales = [100, 125, 150, 200];
    let scaleIndex = 0;
    function couldIncrease() {
        return scaleIndex < (possibleScales.length - 1);
    }
    function couldDecrease() {
        return scaleIndex > 0;
    }

    function setNormal() {
        mapObj.removeAttribute('transform');
    }
    function set125() {
        const width = document.getElementById('project-page-plan-svg').width.baseVal.value;
        const height = document.getElementById('project-page-plan-svg').height.baseVal.value;
        const transform = `translate(${width/2}, ${height/2}) scale(1.25)`;
        mapObj.setAttribute('transform', transform);
    }
    function set150() {
        const width = document.getElementById('project-page-plan-svg').width.baseVal.value;
        const height = document.getElementById('project-page-plan-svg').height.baseVal.value;
        const transform = `translate(${width/2}, ${height/2}) scale(1.5)`;
        mapObj.setAttribute('transform', transform);
    }
    function set200() {
        const width = document.getElementById('project-page-plan-svg').width.baseVal.value;
        const height = document.getElementById('project-page-plan-svg').height.baseVal.value;
        const transform = `translate(${width/2}, ${height/2}) scale(2)`;
        mapObj.setAttribute('transform', transform);
    }
    function displayScale() {
        // todo update messages positions
        switch (possibleScales[scaleIndex]) {
            case 125:
                set125();
                break;
            case 150:
                set150();
                break;
            case 200:
                set200();
                break;
            default:
                setNormal();
        }
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

        couldIncrease: couldIncrease,
        couldDecrease: couldDecrease,

        increase: increase,
        decrease: decrease,
    }
})();


function handleClickMapPlus() {
    if (!mapController.couldIncrease())
        return;
    mapController.increase();
    updateControlStyle();
}

function handleClickMapMinus() {
    if (!mapController.couldDecrease())
        return;
    mapController.decrease();
    updateControlStyle();
}

function setHandlers() {
    mapController.setup();
    document.getElementById('map_control_plus').addEventListener('click', handleClickMapPlus);
    document.getElementById('map_control_minus').addEventListener('click', handleClickMapMinus);
}
window.addEventListener('load', setHandlers);

function updateControlStyle() {
    const plus = document.getElementById('map_control_plus');
    if (plus.classList.contains('disabled') !== !mapController.couldIncrease())
        plus.classList.toggle('disabled');

    const minus = document.getElementById('map_control_minus');
    if (minus.classList.contains('disabled') !== !mapController.couldDecrease())
        minus.classList.toggle('disabled');
}