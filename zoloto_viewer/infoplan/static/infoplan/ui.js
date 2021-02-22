"use strict";

let mapSvgElem;
let probePt;

const messageBoxManager = ControllerMessageBox(buildMessBox);
const markerCirclesManager = ControllerMarkerCircles();
const varWrongnessManager = ControllerVariableWrongness();
const mapScaleController = ControllerMapScale();
const enabledLayersController = ControllerEnabledLayers();
const mapInteractionsController = ControllerMapInteractions();


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

function setHandlers() {
    mapScaleController.setup();
    document.getElementById('map_control_plus').addEventListener('click', handleClickMapPlus);
    document.getElementById('map_control_minus').addEventListener('click', handleClickMapMinus);

    window.addEventListener('keyup', mapInteractionsController.handleKeyUp);
    document.getElementById('project-page-svg-background')
        .addEventListener('click', mapInteractionsController.handleClickMap);

    mapScaleController.mapSvg().addEventListener('mousedown', mapInteractionsController.handleDragStart);
    mapScaleController.mapSvg().addEventListener('mouseup', mapInteractionsController.handleDragEnd);
}
window.addEventListener('load', setHandlers);
window.addEventListener('load', markerCirclesManager.init);

function updateControlStyle() {
    const plus = document.getElementById('map_control_plus');
    if (plus.classList.contains('disabled') !== !mapScaleController.couldIncrease())
        plus.classList.toggle('disabled');

    const minus = document.getElementById('map_control_minus');
    if (minus.classList.contains('disabled') !== !mapScaleController.couldDecrease())
        minus.classList.toggle('disabled');
}

function setActiveLayer(layer_li_tag) {
    layer_li_tag.classList.add('active');
    function getSiblings(elem) {
        // Setup siblings array and get the first sibling
        let siblings = [];
        let sibling = elem.parentNode.firstChild;

        // Loop through each sibling and push to the array
        while (sibling) {
            if (sibling.nodeType === 1 && sibling !== elem) {
                siblings.push(sibling);
            }
            sibling = sibling.nextSibling
        }
        return siblings;
    }

    for (const sibling of getSiblings(layer_li_tag)) {
        sibling.classList.remove('active');
    }

    const layerTitle = layer_li_tag.getElementsByClassName('layer-title-span')[0].textContent;
    enabledLayersController.setActive(layerTitle);
}

window.addEventListener('load', function () {
    const layersMenu = document.getElementById('project-page-layers-box');
    const layerLiTag = layersMenu.getElementsByTagName('li')[0];
    if (layerLiTag) {
        setActiveLayer(layerLiTag);
    }

    for (const markerCircle of document.getElementsByClassName('marker_circle')) {
        markerCircle.addEventListener('click', mapInteractionsController.handleClickMarkerCircle);
    }

    mapSvgElem = document.getElementById('project-page-plan-svg');
    probePt = mapSvgElem.createSVGPoint();
});

function toggleLayerHandler(title) {
    enabledLayersController.toggle(title);
}

function renderMarkerElement(data) {
    console.debug(data);
    function buildMark(data) {
        const markerUid = data.marker;
        const layerTitle = data.layer;
        const pos = data.position;

        let use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        use.setAttributeNS(null, 'href', `#marker_layer-${layerTitle}`);

        use.setAttributeNS(null, 'x', pos.center_x);
        use.setAttributeNS(null, 'y', pos.center_y);
        use.setAttributeNS(null, 'transform',
            `rotate(${pos.rotation} ${pos.center_x} ${pos.center_y})`);

        use.setAttributeNS(null, 'class', 'plan_marker');
        use.setAttributeNS(null, 'data-marker-uid', markerUid);
        use.setAttributeNS(null, 'data-layer-title', layerTitle);

        return use;
    }
    function buildAdditionalGroup(data) {
        function buildLinkLine(data) {
            const posX = data.position.center_x;
            const posY = data.position.center_y;

            let line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttributeNS(null, 'class', 'marker_link');

            const radius = MARKER_DISPLAY_CONFIG.circle_radius;
            line.setAttributeNS(null, 'data-mr', radius);
            line.setAttributeNS(null, 'data-cx', posX);
            line.setAttributeNS(null, 'data-cy', posY);

            line.setAttributeNS(null, 'x1', posX);
            line.setAttributeNS(null, 'y1', posY);
            line.setAttributeNS(null, 'x2', posX);
            line.setAttributeNS(null, 'y2', posY);
            return line;
        }
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
            const commentsResolved = (data.all_comments_resolved ? 'marker_comments_resolved': '');

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
        g.append(buildLinkLine(data), buildMarkerCircle(data), buildCommentMark(data));
        return g;
    }

    const layerGroup = mapSvgElem.getElementsByClassName(`layer_markers layer-${data.layer}`)[0];
    if (layerGroup) {
        layerGroup.append(buildMark(data), buildAdditionalGroup(data));

        const circleElement = document.getElementById(`marker_circle-${data.marker}`);
        markerCirclesManager.register(circleElement);

        const markerElement = circleElement.parentNode.previousElementSibling;
        messageBoxManager.reg(markerElement);

        circleElement.addEventListener('click', mapInteractionsController.handleClickMarkerCircle);
    }
}

function refreshMarkerElement(data) {
    const markerUid = data.marker;

    function refreshCommentMark(element, data) {
        element.classList.toggle('marker_has_comment', data.has_comment);
        element.classList.toggle('marker_comments_resolved', data.all_comments_resolved);
    }

    const circleElement = document.getElementById(`marker_circle-${markerUid}`);
    const markerAdditionalGroup = circleElement.parentNode;
    const commentMark = markerAdditionalGroup.getElementsByClassName('marker_comment_mark')[0];

    refreshCommentMark(commentMark, data);
}
