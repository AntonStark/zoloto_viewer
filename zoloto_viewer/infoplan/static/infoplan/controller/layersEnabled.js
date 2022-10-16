"use strict";
function ControllerEnabledLayers() {
    const HIDDEN_LAYERS_PARAM = 'hide_layers';
    const LAYER_TITLE_SEP = ' ';

    const ENABLED_LAYER_CLASS = 'enabled_layer';
    const PAGE_LINK_CLASS = 'project-page-link';

    const lsKeyToggleAll = 'ZW:layers-box:toggle-all-direction';

    let layersLiElemIndex = {};
    let positionsIndex = {};

    let toggleDirectionTurnOn;

    const activeLayerTitles = new Set();

    function _adjustHiddenLayersUrlParam(url, hiddenLayers) {
        let arr = [];
        for (const [title, disabled] of Object.entries(hiddenLayers)) {
            if (disabled) {
                arr.push(title);
            }
        }

        url.searchParams.delete(HIDDEN_LAYERS_PARAM);
        if (arr.length > 0) {
            url.searchParams.append(HIDDEN_LAYERS_PARAM, arr.join(LAYER_TITLE_SEP));
        }
        return url;
    }
    function _toggleLayerUrlParam(actualUrl, title) {
        const paramValue = actualUrl.searchParams.get(HIDDEN_LAYERS_PARAM);

        const layerTitles = ( paramValue ? paramValue.split(LAYER_TITLE_SEP) : []);
        let hiddenLayers = layerTitles
            .reduce((hash, l, _) => {
                hash[l] = true;
                return hash;
            }, {});
        hiddenLayers[title] = !hiddenLayers[title];

        return _adjustHiddenLayersUrlParam(actualUrl, hiddenLayers);
    }
    function _setupEnabledLayersMarksListeners() {
        const elements = document.getElementsByClassName('side-box-list__item__marks-box');
        for (const el of elements) {
            el.addEventListener('click', handleClickLayerListItemCircle);
        }
    }
    function _syncActiveClasses() {
        for (let title in layersLiElemIndex) {
            const layerLiTag = layersLiElemIndex[title];
            layerLiTag.classList.toggle('active', activeLayerTitles.has(title));
        }
    }
    function _syncToggleAllLayersControls() {
        const controlTurnOff = document.getElementById('all-layers-toggle-invisible');
        const controlTurnOn = document.getElementById('all-layers-toggle-visible');
        if (!controlTurnOff || !controlTurnOn) return;

        const isDirectionTurnOn = toggleDirectionTurnOn;
        controlTurnOn.classList.toggle('active', isDirectionTurnOn);
        controlTurnOff.classList.toggle('active', !isDirectionTurnOn);
    }

    function _setToggleAllLayersDirection(isDirectionTurnOn) {
        toggleDirectionTurnOn = isDirectionTurnOn;
        window.localStorage.setItem(lsKeyToggleAll, toggleDirectionTurnOn);
        _syncToggleAllLayersControls();
    }

    function _syncToggleAll_FromLayersList() {
        function _isAllEnabled() {
            function isTrue(v) {return v === true;}
            return Object.keys(layersLiElemIndex).map(isEnabled).every(isTrue);
        }
        function _isAllDisabled() {
            function isFalse(v) {return v === false;}
            return Object.keys(layersLiElemIndex).map(isEnabled).every(isFalse);
        }

        if (_isAllEnabled()) {
            _setToggleAllLayersDirection(false);
        } else if ( _isAllDisabled()) {
            _setToggleAllLayersDirection(true);
        }
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

        // if (positionsIndex[0] && UI_AUTH) {
        //     setActiveLayer(positionsIndex[0]);
        //     shiftActiveLayerToVisible();
        // }

        _setupEnabledLayersMarksListeners();

        toggleDirectionTurnOn = window.localStorage.getItem(lsKeyToggleAll) === 'true';
        _syncToggleAll_FromLayersList();
        _syncToggleAllLayersControls();
    }

    function _toggleLayerRelatedComponents(layerTitle, state=undefined) {
        const layerClassTitle = 'layer-' + layerTitle;
        const layerRelatedElements = document.getElementsByClassName(layerClassTitle);
        for (const el of layerRelatedElements)
            el.classList.toggle(ENABLED_LAYER_CLASS, state);
    }
    function toggleLayer(layerTitle) {
        _toggleLayerRelatedComponents(layerTitle);

        let actualUrl = new URL(document.location.href);
        const newUrl = _toggleLayerUrlParam(actualUrl, layerTitle);
        window.history.pushState({}, '', newUrl.toString());

        const projectPageLinks = document.getElementsByClassName(PAGE_LINK_CLASS);
        for (const linkItem of projectPageLinks) {
            let targetUrl = new URL(linkItem.href);
            linkItem.href = _toggleLayerUrlParam(targetUrl, layerTitle);
        }

        _syncToggleAll_FromLayersList();
    }
    function _handleSetAllVisible() {

        for (const layerTitle in layersLiElemIndex) {
            _toggleLayerRelatedComponents(layerTitle, true);
        }

        const targetHiddenLayersParam = {};

        let actualUrl = new URL(document.location.href);
        const newUrl = _adjustHiddenLayersUrlParam(actualUrl, targetHiddenLayersParam);
        window.history.pushState({}, '', newUrl.toString());

        const projectPageLinks = document.getElementsByClassName(PAGE_LINK_CLASS);
        for (const linkItem of projectPageLinks) {
            let targetUrl = new URL(linkItem.href);
            linkItem.href = _adjustHiddenLayersUrlParam(targetUrl, targetHiddenLayersParam);
        }

        _setToggleAllLayersDirection(false);
    }
    function _handleSetAllInvisible() {

        for (const layerTitle in layersLiElemIndex) {
            _toggleLayerRelatedComponents(layerTitle, false);
        }
        resetActiveLayer();

        // hack there: layersLiElemIndex contain all layer titles as keys and values cast to true
        const targetHiddenLayersParam = layersLiElemIndex;

        let actualUrl = new URL(document.location.href);
        const newUrl = _adjustHiddenLayersUrlParam(actualUrl, targetHiddenLayersParam);
        window.history.pushState({}, '', newUrl.toString());

        const projectPageLinks = document.getElementsByClassName(PAGE_LINK_CLASS);
        for (const linkItem of projectPageLinks) {
            let targetUrl = new URL(linkItem.href);
            linkItem.href = _adjustHiddenLayersUrlParam(targetUrl, targetHiddenLayersParam);
        }

        _setToggleAllLayersDirection(true);

    }

    function isEnabled(layerTitle) {
        const layerLiTag = layersLiElemIndex[layerTitle];
        if (!layerLiTag)
            return false;

        return layerLiTag.classList.contains(ENABLED_LAYER_CLASS);
    }

    function setActiveLayer(layerTitle) {
        activeLayerTitles.clear()
        activeLayerTitles.add(layerTitle);
        _syncActiveClasses();
    }
    function addActive(layerTitle) {
        activeLayerTitles.add(layerTitle);
        _syncActiveClasses();
    }

    function resetActiveLayer() {
        activeLayerTitles.clear()
        _syncActiveClasses();
    }
    function getActiveLayer() {
        function withMinimalNumber(one, two) {return ( Number.parseInt(one) < Number.parseInt(two) ? one : two ); }

        try {
            return Array.from(activeLayerTitles.values()).reduce(withMinimalNumber)
        } catch (e) {
            return null;
        }
    }
    function isActive(layerTitle) {
        return activeLayerTitles.has(layerTitle);
    }
    function nextTitle(layerTitle) {
        const curIndex = positionsIndex[layerTitle];
        let nextTitle = positionsIndex[curIndex+1];
        if (!nextTitle)
            return null;
        return nextTitle;
    }

    function shiftActiveLayerToVisible() {
        let active = getActiveLayer();
        // console.log(active);
        while (!isEnabled(active)) {    // set active to next
            const next = nextTitle(active);
            if (!next) {
                const firstLayerTitle = positionsIndex[0]
                setActiveLayer(firstLayerTitle);
                if (!isEnabled(firstLayerTitle)) {
                    toggleLayer(firstLayerTitle);
                }
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
        addActive: addActive,
        getActive: getActiveLayer,
        dropActive: resetActiveLayer,
        isActive : isActive,

        shift: shiftActiveLayerToVisible,
        handleSetAllVisible     : _handleSetAllVisible,
        handleSetAllInvisible   : _handleSetAllInvisible,
    }
}
