"use strict";
function ControllerEnabledLayers() {
    const LAYER_PARAM = 'layer';
    const ENABLED_LAYER_CLASS = 'enabled_layer';
    const PAGE_LINK_CLASS = 'project-page-link';

    let activeLayerTitle = '';

    function _toggleLayerUrlParam(title, actualUrl) {
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

    function toggleLayer(title) {
        const layerRelatedElements = document.getElementsByClassName(title);
        for (const el of layerRelatedElements)
            el.classList.toggle(ENABLED_LAYER_CLASS);

        let actualUrl = new URL(document.location.href);
        const newUrl = _toggleLayerUrlParam(title, actualUrl);
        window.history.pushState({}, '', newUrl.toString());

        const projectPageLinks = document.getElementsByClassName(PAGE_LINK_CLASS);
        for (const linkItem of projectPageLinks) {
            let targetUrl = new URL(linkItem.href);
            linkItem.href = _toggleLayerUrlParam(title, targetUrl);
        }
    }

    function setActiveLayer(layerTitle) {
        activeLayerTitle = layerTitle;
    }
    function getActiveLayer() {
        return activeLayerTitle;
    }

    return {
        toggle   : toggleLayer,
        setActive: setActiveLayer,
        getActive: getActiveLayer,
    }
}
