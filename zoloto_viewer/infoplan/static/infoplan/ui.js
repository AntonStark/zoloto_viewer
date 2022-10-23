"use strict";

let mapSvgElem;
let probePt;

const messageBoxManager = ControllerMessageBox(buildMessBox);
const markerCirclesManager = ControllerMarkerCircles();
const varWrongnessManager = ControllerVariableWrongness();
const mapScaleController = ControllerMapScale();
const enabledLayersController = ControllerEnabledLayers();
const mapInteractionsController = ControllerMapInteractions();
const areasListController = ControllerAreasList();
const captionsController = ControllerCaptions();
const statusComponent = StatusComponent();


let SVG_VIEWPORT_BOUNDS = undefined;
window.addEventListener('load', function () {
    const svgElement = document.getElementById('project-page-plan-svg');
    // console.log(svgElement.width.baseVal.value);
    SVG_VIEWPORT_BOUNDS = [svgElement.width.baseVal.value, svgElement.height.baseVal.value];
});


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

function init() {
    mapScaleController.setup();
    markerCirclesManager.init();
    enabledLayersController.init();
    areasListController.init();

    document.getElementById('map_control_plus').addEventListener('click', handleClickMapPlus);
    document.getElementById('map_control_minus').addEventListener('click', handleClickMapMinus);

    document.getElementById('all-layers-toggle-invisible')
        .addEventListener('click', enabledLayersController.handleSetAllInvisible);
    document.getElementById('all-layers-toggle-visible')
        .addEventListener('click', enabledLayersController.handleSetAllVisible);

    const downloadPdfSpan = document.getElementById('download_pdf_span');
    if (downloadPdfSpan) {
        downloadPdfSpan.addEventListener('click',
            (e) => e.currentTarget === e.target && handleFileDownloadWithRetryAfter(downloadPdfSpan.dataset.targetUrl));
    }

    const insertModeBtn = document.getElementById('menu_actions_option1');
    if (insertModeBtn) {
        insertModeBtn.addEventListener('click', enabledLayersController.shift);
    }

    const captionsModeBtn = document.getElementById('menu_actions_option3');
    if (captionsModeBtn) {
        captionsModeBtn.addEventListener('click', captionsController.showAll);
    }
    if (insertModeBtn) {
        insertModeBtn.addEventListener('click', captionsController.hideALl);
    }
    const selectModeBtn = document.getElementById('menu_actions_option2');
    if (selectModeBtn) {
        selectModeBtn.addEventListener('click', captionsController.hideALl);
    }

    window.addEventListener('keyup', mapInteractionsController.handleKeyUp);
    window.addEventListener('keypress', mapInteractionsController.handleKeyPress);

    mapScaleController.mapSvg().addEventListener('mousedown', mapInteractionsController.handleMouseDown);
    mapScaleController.mapSvg().addEventListener('mouseup', mapInteractionsController.handleMouseUp);

    window.addEventListener('copy', mapInteractionsController.handleCopyEvent);
    window.addEventListener('paste', mapInteractionsController.handlePasteEvent);

    statusComponent.init();
    checkApiStatus();
    setInterval(checkApiStatus, 30000);
}
window.addEventListener('load', init);

function updateControlStyle() {
    const plus = document.getElementById('map_control_plus');
    if (plus.classList.contains('disabled') !== !mapScaleController.couldIncrease())
        plus.classList.toggle('disabled');

    const minus = document.getElementById('map_control_minus');
    if (minus.classList.contains('disabled') !== !mapScaleController.couldDecrease())
        minus.classList.toggle('disabled');
}

function toggleLayerHandler(title)
{ enabledLayersController.toggle(title); }
function handleClickLayerListItem(layerLiTag) {
    /*  клик по выключенному включает и делает активным,
        клик по включённому делает активным
    * */
    const layerTitle = layerLiTag.getElementsByClassName('layer-title-span')[0].textContent;
    // console.log('isEnabled', enabledLayersController.isEnabled(layerClassTitle));
    // console.log('isActive', enabledLayersController.isActive(layerTitle));
    if (!enabledLayersController.isEnabled(layerTitle)) {
        enabledLayersController.toggle(layerTitle);
        enabledLayersController.setActive(layerTitle);
    } else if (!enabledLayersController.isActive(layerTitle)) {
        enabledLayersController.setActive(layerTitle);
    } else {
        // enabledLayersController.toggle(layerTitle);
        // mapInteractionsController.toggleSelectMode();

        // const nextLayerTag = layerLiTag.nextElementSibling || layerLiTag.parentElement.firstElementChild;
        // setActiveLayer(nextLayerTag);
    }
}
function handleClickLayerListItemCircle(event) {
    /*  клик по выключенному только включает, но не делает активным,
        клик по включённому выключает (и если он был активен, то сбрасывает активность)
    * */
    const layerLiTagMarksBox = event.currentTarget;
    const layerLiTag = layerLiTagMarksBox.parentElement;
    const layerTitle = layerLiTag.getElementsByClassName('layer-title-span')[0].textContent;
    if (!enabledLayersController.isEnabled(layerTitle)) {
        enabledLayersController.toggle(layerTitle);
    }
    else {
        enabledLayersController.toggle(layerTitle);
        if (enabledLayersController.isActive(layerTitle)) {
            enabledLayersController.dropActive();
        }
    }
    event.stopPropagation();
}

window.addEventListener('load', function () {
    mapSvgElem = document.getElementById('project-page-plan-svg');
    probePt = mapSvgElem.createSVGPoint();
});


function renderMarkerElement(data) {
    // console.debug(data);
    function buildMark(data) {
        const markerUid = data.marker;
        const layerTitle = data.layer;
        const layerKindName = data.layer_kind_name || null;
        const pos = data.position;

        let use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        use.setAttributeNS(null, 'href', `#marker_layer-${layerTitle}`);

        use.setAttributeNS(null, 'x', pos.center_x);
        use.setAttributeNS(null, 'y', pos.center_y);
        use.setAttributeNS(null, 'transform',
            `rotate(${-pos.rotation} ${pos.center_x} ${pos.center_y})`);

        use.setAttributeNS(null, 'class', 'plan_marker');
        use.setAttributeNS(null, 'data-marker-uid', markerUid);
        use.setAttributeNS(null, 'data-layer-title', layerTitle);
        use.setAttributeNS(null, 'data-origin-x', pos.center_x);
        use.setAttributeNS(null, 'data-origin-y', pos.center_y);

        // fingerpost fix
        if (layerKindName && layerKindName === 'фингерпост') {
            use.classList.add('pane-1')
        }

        return use;
    }
    function buildAdditionalGroup(data) {
        function buildMarkerCircle(data) {
            const markerUid = data.marker;
            const layerTitle = data.layer;
            const pos = data.position;

            let circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');

            const radius = MARKER_DISPLAY_CONFIG.circle_radius;
            circle.setAttributeNS(null, 'cx', pos.center_x);
            circle.setAttributeNS(null, 'cy', pos.center_y);
            circle.setAttributeNS(null, 'r', radius);

            circle.setAttributeNS(null, 'id', `marker_circle-${markerUid}`);
            circle.setAttributeNS(null, 'class', 'marker_circle');

            circle.setAttributeNS(null, 'data-marker-uid', markerUid);
            circle.setAttributeNS(null, 'data-layer-title', layerTitle);

            return circle;
        }
        function buildCommentMark(data) {
            const posX = data.position.center_x;
            const posY = data.position.center_y;
            const hasComment = (data.has_comment ? 'marker_has_comment': '');
            const commentsResolved = (data.comments_resolved ? 'marker_comments_resolved': '');

            let circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');

            circle.setAttributeNS(null, 'cx', posX);
            circle.setAttributeNS(null, 'cy', posY);
            const radius = MARKER_DISPLAY_CONFIG.comment_mark_radius;
            circle.setAttributeNS(null, 'r', radius);

            const padding = MARKER_DISPLAY_CONFIG.comment_mark_padding;
            circle.setAttributeNS(null, 'transform',
                `translate(${padding}, -${padding})`);
            circle.setAttributeNS(null, 'class',
                `marker_comment_mark ${hasComment} ${commentsResolved}`);

            return circle;
        }

        let g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttributeNS(null, 'class', `marker_group`);
        g.append(buildMarkerCircle(data), buildCommentMark(data));
        return g;
    }

    const layerGroup = mapSvgElem.getElementsByClassName(`layer_markers layer-${data.layer}`)[0];
    if (layerGroup) {
        layerGroup.append(buildMark(data), buildAdditionalGroup(data));

        const circleElement = document.getElementById(`marker_circle-${data.marker}`);
        markerCirclesManager.register(circleElement);

        const markerElement = circleElement.parentNode.previousElementSibling;
        messageBoxManager.reg(markerElement);
    }
}

function refreshMarkerElement(data) {
    const markerUid = data.marker;

    function refreshCommentMark(element, data) {
        element.classList.toggle('marker_has_comment', data.has_comment);
        element.classList.toggle('marker_comments_resolved', data.comments_resolved);
    }

    const circleElement = document.getElementById(`marker_circle-${markerUid}`);
    const markerAdditionalGroup = circleElement.parentNode;
    const commentMark = markerAdditionalGroup.getElementsByClassName('marker_comment_mark')[0];

    refreshCommentMark(commentMark, data);
}
