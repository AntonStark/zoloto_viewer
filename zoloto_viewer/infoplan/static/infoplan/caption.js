function renderCaptionElement(data) {
    function buildCaptionTextElem(data) {
        let textElem = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        textElem.textContent = data.marker.number;

        const markerPos = data.marker.position;
        const captionOffset = data.data.offset;
        textElem.setAttributeNS(null, 'x', markerPos.center_x + captionOffset[0]);
        textElem.setAttributeNS(null, 'y', markerPos.center_y + captionOffset[1]);
        textElem.setAttributeNS(null, 'class', `caption layer-${data.marker.layer}`);
        return textElem;
    }

    function buildCaptionGroup(data) {
        let g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttributeNS(null, 'class', `caption_group layer-${data.marker.layer}`);
        g.append(buildCaptionTextElem(data));
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
