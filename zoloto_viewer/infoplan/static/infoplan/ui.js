"use strict";

const messageBoxManager = ControllerMessageBox(buildMessBox);
const markerCirclesManager = ControllerMarkerCircles();
const messLinksManager = ControllerMessageLinks();
const varWrongnessManager = ControllerVariableWrongness();
const mapScaleController = ControllerMapScale();
const enabledLayersController = ControllerEnabledLayers();


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

function toggleLayerHandler(title) {
    enabledLayersController.toggle(title);
}