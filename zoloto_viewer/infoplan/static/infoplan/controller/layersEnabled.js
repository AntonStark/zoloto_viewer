"use strict";
function ControllerEnabledLayers() {
    const HIDDEN_LAYERS_PARAM = 'hide_layers';
    const LAYER_TITLE_SEP = ' ';

    const ENABLED_LAYER_CLASS = 'enabled_layer';
    const PAGE_LINK_CLASS = 'project-page-link';

    let layersLiElemIndex = {};
    let positionsIndex = {};

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

    function init() {
        const container = document.getElementsByClassName('layers-box side_box_list')[0];
        if (!container) return;

        let index = 0;
        for (const layerLiTag of container.children) {
            const layerTitle = layerLiTag.getElementsByClassName('layer-title-span')[0].textContent;
            layersLiElemIndex[layerTitle] = layerLiTag;
            positionsIndex[layerTitle] = index;
            positionsIndex[index] = layerTitle;
            index++;
            // console.log(layerLiTag);
        }

        if (positionsIndex[0]) {
            setActiveLayer(positionsIndex[0]);
            shiftActiveLayerToVisible();
        }
    }

    function toggleLayer(layerTitle) {
        const layerClassTitle = 'layer-' + layerTitle;
        const layerRelatedElements = document.getElementsByClassName(layerClassTitle);
        for (const el of layerRelatedElements)
            el.classList.toggle(ENABLED_LAYER_CLASS);

        let actualUrl = new URL(document.location.href);
        const newUrl = _toggleLayerUrlParam(actualUrl, layerTitle);
        window.history.pushState({}, '', newUrl.toString());

        const projectPageLinks = document.getElementsByClassName(PAGE_LINK_CLASS);
        for (const linkItem of projectPageLinks) {
            let targetUrl = new URL(linkItem.href);
            linkItem.href = _toggleLayerUrlParam(targetUrl, layerTitle);
        }
    }
    function isEnabled(layerTitle) {
        const layerLiTag = layersLiElemIndex[layerTitle];
        if (!layerLiTag)
            return false;

        return layerLiTag.classList.contains(ENABLED_LAYER_CLASS);
    }

    function setActiveLayer(layerTitle) {
        activeLayerTitle = layerTitle;
        for (let title in layersLiElemIndex) {
            const layerLiTag = layersLiElemIndex[title];
            layerLiTag.classList.toggle('active', title === layerTitle);
        }
    }
    function getActiveLayer() {
        return activeLayerTitle;
    }
    function isActive(layerTitle) {
        return activeLayerTitle === layerTitle;
    }
    function nextTitle(layerTitle) {
        const curIndex = positionsIndex[layerTitle];
        let nextTitle = positionsIndex[curIndex+1];
        if (!nextTitle)
            nextTitle = positionsIndex[0];
        return nextTitle;
    }

    function shiftActiveLayerToVisible() {
        let active = getActiveLayer();
        // console.log(active);
        while (!isEnabled(active)) {    // set active to next
            const next = nextTitle(active);
            if (!next) {
                break;
            }
            setActiveLayer(next);
            active = getActiveLayer();
        }

    }

    return {
        init     : init,
        toggle   : toggleLayer,
        isEnabled: isEnabled,

        setActive: setActiveLayer,
        getActive: getActiveLayer,
        isActive : isActive,

        shift: shiftActiveLayerToVisible,
    }
}
