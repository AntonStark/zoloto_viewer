function renderCaptionElement(data) {
    const markerPos = data.marker.position;
    const captionOffset = data.data.offset;
    const captionRotation = data.data.rotation;
    // initially place an marker center and setup correct position later with transform
    const captionX = markerPos.center_x;
    const captionY = markerPos.center_y;

    function buildCaptionTextElem(data) {
        let textElem = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        textElem.setAttributeNS(null, 'class', `caption layer-${data.marker.layer}`);
        textElem.textContent = data.marker.number;

        textElem.setAttributeNS(null, 'x', captionX);
        textElem.setAttributeNS(null, 'y', captionY);
        return textElem;
    }

    function buildRotationBtn(data) {
        let btn = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        btn.setAttributeNS(null, 'class', `caption_rotator`);
        btn.textContent = (data.data.rotation === 0 ? '↺' : '↻');
        btn.setAttributeNS(null, 'x', captionX);
        btn.setAttributeNS(null, 'y', captionY - 16);
        btn.dataset.markerUid = data.marker.marker;
        btn.style.fill = 'black';
        return btn;
    }

    function buildCaptionGroup(data) {
        let g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttributeNS(null, 'class', `caption_group layer-${data.marker.layer}`);
        g.append(buildCaptionTextElem(data), buildRotationBtn(data));
        g.dataset.markerUid = data.marker.marker;
        g.dataset.captionRotation = captionRotation;
        g.dataset.isRotated = captionRotation !== 0;
        g.dataset.markerCenter = JSON.stringify([markerPos.center_x, markerPos.center_y]);
        g.dataset.originOffset = JSON.stringify(captionOffset);
        g.dataset.captionOffset = JSON.stringify(captionOffset);
        g.dataset.markerX = markerPos.center_x;
        g.dataset.markerY = markerPos.center_y;
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
    // calc text direction related offset
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

    // apply actual offset
    [x, y] = [x + offsetX, y + offsetY];

    // apply rotation
    if (isRotated === 'true') {
        [x, y] = [-y, x];
    }
    return [x, y];
}

function applyProperTransform(captionGroup) {
    const {captionRotation, isRotated} = captionGroup.dataset;
    const markerCenter = JSON.parse(captionGroup.dataset.markerCenter);
    const captionOffset = JSON.parse(captionGroup.dataset.captionOffset);
    const captionX = markerCenter[0] + captionOffset[0];
    const captionY = markerCenter[1] + captionOffset[1];

    // console.log(captionRotation, isRotated, captionX, captionY);
    const [translateX, translateY] = calcTranslateParams(captionGroup);
    // console.log(translateX, translateY);
    const transform = ( isRotated === 'true'
            ? `rotate(${-captionRotation}, ${markerCenter[0]}, ${markerCenter[1]}) translate(${translateX}, ${translateY})`
            : `translate(${translateX}, ${translateY})`
    );
    captionGroup.setAttributeNS(null, 'transform', transform);
}

function updateCaptionPosition(captionGroup, moveOffset) {
    const originOffset = JSON.parse(captionGroup.dataset.originOffset);
    const newOffset = [originOffset[0] + moveOffset[0], originOffset[1] + moveOffset[1]];
    // console.log('updateCaptionPosition', newOffset)

    // update transform with new Offset
    captionGroup.dataset.captionOffset = JSON.stringify(newOffset);
    applyProperTransform(captionGroup);
}
