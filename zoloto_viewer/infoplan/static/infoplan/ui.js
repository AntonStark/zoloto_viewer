"use strict";

const messageBoxManager = ControllerMessageBox(buildMessBox);
const markerCirclesManager = ControllerMarkerCircles();
const messLinksManager = ControllerMessageLinks();
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


function buildMessBox(data) {
    function buildVariablesBlock(data) {
        let variablesList = document.createElement('ul');

        let [numberLine, emptyLine] = [document.createElement('li'), document.createElement('li')];
        numberLine.style.cursor = emptyLine.style.cursor = 'unset';
        numberLine.textContent = data.number;
        emptyLine.innerHTML = '&nbsp;';
        variablesList.append(numberLine, emptyLine);

        variablesList.append(...data.variables.map(varData => {
            let variableItem = document.createElement('li');
            variableItem.setAttribute('data-variable-key', varData.key);
            variableItem.textContent = varData.value;
            variableItem.addEventListener('click', () => handleToggleWrong(data.marker, varData.key));
            varWrongnessManager.register(data.marker, varData.key, variableItem, varData.wrong);
            return variableItem;
        }));

        let variablesDiv  = document.createElement('div');
        variablesDiv.setAttribute('class', `variables_container`);
        variablesDiv.append(variablesList);
        return variablesDiv;
    }
    function buildCommentBlock(data) {
        let commentLabel = document.createElement('span');
        commentLabel.setAttribute('style', 'font-size: 10px;');
        commentLabel.textContent = 'Комментарий';

        let commentInput = document.createElement('textarea');
        commentInput.setAttribute('class', 'comment_field');
        commentInput.setAttribute('placeholder', 'Можно не заполнять');
        if (data.has_comment) {
            commentInput.value = data.comment;
        }

        let commentDiv = document.createElement('div');
        commentDiv.append(commentLabel, commentInput);
        return commentDiv;
    }
    function buildConfirmBtn(data) {
        let btnLink = document.createElement('a');
        btnLink.setAttribute('class', 'message_confirm_btn');
        btnLink.textContent = 'Проверено';
        btnLink.addEventListener('click',
            () => handlerConfirmBtmClick(data.marker));
        return btnLink;
    }

    const boxDiv = document.createElement('div');
    boxDiv.setAttribute('class', 'message_box');
    boxDiv.append(buildVariablesBlock(data), buildCommentBlock(data), buildConfirmBtn(data));
    return boxDiv;
}

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

            line.setAttributeNS(null, 'data-mr', MARKER_CIRCLE_RADIUS);
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

            circle.setAttributeNS(null, 'cx', pos.center_x);
            circle.setAttributeNS(null, 'cy', pos.center_y);
            circle.setAttributeNS(null, 'r', MARKER_CIRCLE_RADIUS);

            circle.setAttributeNS(null, 'id', `marker_circle-${markerUid}`);
            circle.setAttributeNS(null, 'class', 'marker_circle');

            circle.setAttributeNS(null, 'data-marker-uid', markerUid);
            circle.setAttributeNS(null, 'data-layer-title', layerTitle);

            // circle.setAttributeNS(null, 'onclick',
            //     'mapInteractionsController.handleClickMarkerCircle(this)');

            return circle;
        }
        function buildCommentMark(data) {
            const posX = data.position.center_x;
            const posY = data.position.center_y;
            const hasComment = (data.has_comment ? 'marker_has_comment': '');

            let circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');

            circle.setAttributeNS(null, 'cx', posX);
            circle.setAttributeNS(null, 'cy', posY);
            circle.setAttributeNS(null, 'r', 1);

            circle.setAttributeNS(null, 'transform',
                `translate(${COMMENT_MARK_PADDING}, -${COMMENT_MARK_PADDING})`);
            circle.setAttributeNS(null, 'class',
                `marker_comment_mark ${hasComment}`);

            return circle;
        }

        let g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttributeNS(null, 'class', `marker_group`);
        g.append(buildLinkLine(data), buildMarkerCircle(data), buildCommentMark(data));
        return g;
    }

    const mapRoot = document.getElementById('project-page-plan-svg');
    const layerGroup = mapRoot.getElementsByClassName(`layer_markers layer-${data.layer}`)[0];
    if (layerGroup) {
        layerGroup.append(buildMark(data), buildAdditionalGroup(data));

        const circleElement = document.getElementById(`marker_circle-${data.marker}`);
        markerCirclesManager.register(circleElement);

        circleElement.addEventListener('click', mapInteractionsController.handleClickMarkerCircle);
    }
}
