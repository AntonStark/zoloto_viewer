"use strict";
function ControllerEnabledLayers() {
    const HIDDEN_LAYERS_PARAM = 'hide_layers';
    const LAYER_TITLE_SEP = ' ';

    const ENABLED_LAYER_CLASS = 'enabled_layer';
    const PAGE_LINK_CLASS = 'project-page-link';

    let activeLayerTitle = '';

    function _toggleLayerUrlParam(actualUrl, title) {
        const paramValue = actualUrl.searchParams.get(HIDDEN_LAYERS_PARAM);
        const layerTitles = ( paramValue ? paramValue.split(LAYER_TITLE_SEP) : []);
        let hiddenLayers = layerTitles
            .reduce((hash, l, _) => {
                hash[l] = true;
                return hash;
            }, {});
        hiddenLayers[title] = !hiddenLayers[title];
        // console.log(hiddenLayers, hiddenLayers[title]);

        actualUrl.searchParams.delete(HIDDEN_LAYERS_PARAM);
        let arr = [];
        for (const [title, disabled] of Object.entries(hiddenLayers)) {
            if (disabled) {
                arr.push(title);
            }
        }
        if (arr.length > 0) {
            actualUrl.searchParams.append(HIDDEN_LAYERS_PARAM, arr.join(LAYER_TITLE_SEP));
        }
        return actualUrl;
    }

    function toggleLayer(title) {
        const layerRelatedElements = document.getElementsByClassName(title);
        for (const el of layerRelatedElements)
            el.classList.toggle(ENABLED_LAYER_CLASS);

        const layerPrefix = 'layer-'
        const layerOwnTitle = ( title.startsWith(layerPrefix) ? title.slice(layerPrefix.length) : title );

        let actualUrl = new URL(document.location.href);
        const newUrl = _toggleLayerUrlParam(actualUrl, layerOwnTitle);
        window.history.pushState({}, '', newUrl.toString());

        const projectPageLinks = document.getElementsByClassName(PAGE_LINK_CLASS);
        for (const linkItem of projectPageLinks) {
            let targetUrl = new URL(linkItem.href);
            linkItem.href = _toggleLayerUrlParam(targetUrl, layerOwnTitle);
        }
    }
    function isEnabled(layerTitle) {
        const layersList = document.getElementsByClassName('layers-box')[0];
        if (!layersList)
            return false;

        const layerLiTag = layersList.getElementsByClassName(layerTitle)[0];
        if (!layerLiTag)
            return false;

        return layerLiTag.classList.contains(ENABLED_LAYER_CLASS);
    }

    function setActiveLayer(layerTitle) {
        activeLayerTitle = layerTitle;
    }
    function getActiveLayer() {
        return activeLayerTitle;
    }
    function isActive(layerTitle) {
        return activeLayerTitle === layerTitle;
    }

    return {
        toggle   : toggleLayer,
        isEnabled: isEnabled,

        setActive: setActiveLayer,
        getActive: getActiveLayer,
        isActive : isActive,
    }
}
