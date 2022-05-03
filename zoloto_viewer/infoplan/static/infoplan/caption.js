function renderCaptionElement(data) {
    const markerPos = data.marker.position;
    // initially place an marker center and setup correct position later with transform
    const captionX = markerPos.center_x;
    const captionY = markerPos.center_y;

    function buildCaptionTextElem(data) {
        const markerNumber = data.marker.number;
        const layerTitle = data.marker.layer;

        let textElem = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        textElem.setAttributeNS(null, 'class', `caption layer-${layerTitle}`);
        textElem.textContent = markerNumber;
        textElem.setAttributeNS(null, 'x', captionX);
        textElem.setAttributeNS(null, 'y', captionY);
        return textElem;
    }

    function buildRotationBtn(data) {
        const captionRotation = data.data.rotation;
        const markerUid = data.marker.marker;

        let btn = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        btn.setAttributeNS(null, 'class', `caption_rotator`);
        btn.textContent = (captionRotation === 0 ? '↺' : '↻');
        btn.setAttributeNS(null, 'x', captionX);
        btn.setAttributeNS(null, 'y', captionY - 16);
        btn.dataset.markerUid = markerUid;
        btn.style.fill = 'black';
        return btn;
    }

    function buildCaptionGroup(data) {
        const markerUid = data.marker.marker;
        const layerTitle = data.marker.layer;

        let g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttributeNS(null, 'class', `caption_group layer-${layerTitle}`);
        g.dataset.markerUid = markerUid;
        setupCaptionGroupGeometryDataset(g, data);
        g.append(buildCaptionTextElem(data), buildRotationBtn(data));
        return g;
    }

    const layerGroup = mapSvgElem.getElementsByClassName(`layer_markers layer-${data.marker.layer}`)[0];
    if (layerGroup) {
        layerGroup.append(buildCaptionGroup(data));
    }
}

function setupCaptionGroupGeometryDataset(captionGroup, data) {
    const markerPos = data.marker.position;
    const captionRotation = data.data.rotation;
    const captionOffset = data.data.offset;

    captionGroup.dataset.captionRotation = captionRotation;
    captionGroup.dataset.isRotated = captionRotation !== 0;
    captionGroup.dataset.markerCenter = JSON.stringify([markerPos.center_x, markerPos.center_y]);
    captionGroup.dataset.originOffset = JSON.stringify(captionOffset);
    captionGroup.dataset.captionOffset = JSON.stringify(captionOffset);
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

function calcTranslateParams(isRotated, offsetX, offsetY, bounds) {
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
    const {captionRotation, isRotated, captionOffset} = captionGroup.dataset;
    const markerCenter = JSON.parse(captionGroup.dataset.markerCenter);

    const bg = captionGroup.firstChild;
    const bounds = bg.getBBox();
    const [offsetX, offsetY] = JSON.parse(captionOffset);
    const [translateX, translateY] = calcTranslateParams(isRotated, offsetX, offsetY, bounds);
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
