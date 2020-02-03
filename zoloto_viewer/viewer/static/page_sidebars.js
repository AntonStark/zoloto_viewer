"use strict";
const LAYER_PARAM = 'layer';

function toggleLayer(elem, title) {
    console.debug('toggleLayer', elem, title);
    elem.classList.toggle('enabled_layer');
    const newUrl = toggleLayerUrlParam(title);
    window.history.pushState({}, '', newUrl.toString())
}

function toggleLayerUrlParam(title) {
    let actualUrl = new URL(document.location.href);
    let enabledLayers = actualUrl.searchParams.getAll(LAYER_PARAM)
        .reduce((hash, l, _) => {
            hash[l] = true;
            return hash;
        }, {});
    enabledLayers[title] = !enabledLayers[title];
    // console.log(enabledLayers, enabledLayers[title]);

    actualUrl.searchParams.delete(LAYER_PARAM);
    for (const [title, enabled] of Object.entries(enabledLayers))
        if (enabled)
            actualUrl.searchParams.append(LAYER_PARAM, title);
    return actualUrl;
}
