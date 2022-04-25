function renderCaptionElement(data) {
    const markerPos = data.marker.position;
    const captionOffset = data.data.offset;
    const captionRotation = data.data.rotation;
    const captionX = markerPos.center_x + captionOffset[0];
    const captionY = markerPos.center_y + captionOffset[1];

    function buildCaptionTextElem(data) {
        let textElem = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        textElem.setAttributeNS(null, 'class', `caption layer-${data.marker.layer}`);
        textElem.textContent = data.marker.number;

        textElem.setAttributeNS(null, 'x', captionX);
        textElem.setAttributeNS(null, 'y', captionY);
        return textElem;
    }

    function buildCaptionGroup(data) {
        let g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttributeNS(null, 'class', `caption_group layer-${data.marker.layer}`);
        g.append(buildCaptionTextElem(data));
        g.dataset.markerUid = data.marker.marker;
        g.dataset.captionRotation = captionRotation;
        g.dataset.captionOffset = JSON.stringify(captionOffset);
        g.dataset.isRotated = captionRotation !== 0;
        g.dataset.captionX = captionX;
        g.dataset.captionY = captionY;
        return g;
    }

    const layerGroup = mapSvgElem.getElementsByClassName(`layer_markers layer-${data.marker.layer}`)[0];
    if (layerGroup) {
        layerGroup.append(buildCaptionGroup(data));
    }
}

function insertBackground(captionGroup) {
    const caption = captionGroup.firstChild;
    const bounds = caption.getBBox();
    let bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');

    var style = getComputedStyle(caption)
    var padding_top = parseInt(style["padding-top"])
    var padding_left = parseInt(style["padding-left"])
    var padding_right = parseInt(style["padding-right"])
    var padding_bottom = parseInt(style["padding-bottom"])

    bg.setAttribute("x", bounds.x - parseInt(style["padding-left"]))
    bg.setAttribute("y", bounds.y - parseInt(style["padding-top"]))
    bg.setAttribute("width", bounds.width + padding_left + padding_right)
    bg.setAttribute("height", bounds.height + padding_top + padding_bottom)
    bg.setAttribute("fill", style["background-color"])

    captionGroup.insertBefore(bg, caption);
    caption.style.fill = 'white';
}

function calcTranslateParams(captionGroup) {
    const { isRotated, captionOffset } = captionGroup.dataset;
    const bg = captionGroup.firstChild;
    const [offsetX, offsetY] = JSON.parse(captionOffset);
    const bounds = bg.getBBox();

    let x, y;
    // console.log('calcTranslateParams', [offsetX, offsetY], isRotated)
    if (isRotated === 'true') {
        if (offsetY > 0) {
            [x, y] = [bounds.height / 2., bounds.width];
        }
        else {
            [x, y] = [bounds.height / 2., 0];
        }
    }
    else {
        if (offsetX > 0) {
            [x, y] = [0, bounds.height / 2.];
        }
        else {
            [x, y] = [- bounds.width, bounds.height / 2.];
        }
    }
    return [x, y];
}

function applyProperTransform(captionGroup) {
    const {captionRotation, isRotated, captionX, captionY} = captionGroup.dataset;
    // console.log(captionRotation, isRotated, captionX, captionY);
    const [translateX, translateY] = calcTranslateParams(captionGroup);
    // console.log(translateX, translateY);
    const transform = ( isRotated
            ? `translate(${translateX}, ${translateY}) rotate(${-captionRotation}, ${captionX}, ${captionY})`
            : `translate(${translateX}, ${translateY})`
    );
    captionGroup.setAttributeNS(null, 'transform', transform);
}
