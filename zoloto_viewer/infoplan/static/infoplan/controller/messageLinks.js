"use strict";
function ControllerMessageLinks() {
    let messLinkIndex = {};         // marker_uid -> <line> elem

    function registerLinkElem(markerUid, elem) {
        if (messLinkIndex[markerUid] !== undefined
            && messLinkIndex[markerUid] !== elem)
            messLinkIndex[markerUid].remove();
        messLinkIndex[markerUid] = elem;
    }

    function _toSvgCoordinates(linkElement, screenCoordinates) {
        const inverseTransform = linkElement.getCTM().inverse();
        let probe = linkElement.ownerSVGElement.createSVGPoint();
        probe.x = screenCoordinates[0];
        probe.y = screenCoordinates[1];
        probe = probe.matrixTransform(inverseTransform);
        return [probe.x, probe.y];
    }

    function updateLinkParams(markerUid, messContainer) {
        return;
        const messLink = messLinkIndex[markerUid];
        if (!messLink)
            return;

        const [cx, cy, mr] = [Number(messLink.dataset.cx), Number(messLink.dataset.cy), Number(messLink.dataset.mr)];
        const htmlCoords = [messContainer.offsetLeft, messContainer.offsetTop];
        const [left, top] = _toSvgCoordinates(messLink, htmlCoords);
        const x2 = left;
        const y2 = top;
        // y = (1-l) * cy + l * y2
        // dx^2 + dy^2 = mr^2
        const l = Math.sqrt(mr ** 2 / ( (y2 - cy) ** 2 + (x2 - cx) ** 2));
        const x1 = (1-l) * cx + l * x2;
        const y1 = (1-l) * cy + l * y2;
        messLink.setAttribute('x1', x1);
        messLink.setAttribute('y1', y1);
        messLink.setAttribute('x2', x2);
        messLink.setAttribute('y2', y2);
    }

    return {
        register: registerLinkElem,
        update  : updateLinkParams,
    }
}
