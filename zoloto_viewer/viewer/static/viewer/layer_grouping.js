"use strict";

"API"

const API_GROUPS = `${BASE_URL}/viewer/project/${project_id}/group_layers`;

function doApiCall(method, url, data, onResponse, onError=undefined) {
    let req = new XMLHttpRequest();
    req.open(method, url);

    req.onreadystatechange = function() {
        if (req.readyState === XMLHttpRequest.DONE) {
            if (req.status === 200) {
                const rep = JSON.parse(req.responseText);
                if (onResponse) {
                    onResponse(rep);
                }
            } else if (onError) {
                onError(req);
            }
            else {
                console.error(method, url, 'status=', req.status, req);
            }
        }
    };

    req.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    req.send(JSON.stringify(data));
}

function apiGetAllGroupsData(onResponse) {
    const actualUrl = API_GROUPS + '?response_json=true';
    doApiCall('GET', actualUrl, undefined, onResponse);
}

function apiExcludeLayers(layerIdList, onResponse) {
    const payload = {
        'exclude': {
            'layers': layerIdList
        }
    }
    doApiCall('PATCH', API_GROUPS, payload, onResponse);
}

function apiIncludeLayersToGroup(layerIdList, groupNum, onResponse) {
    const payload = {
        'include': [{
            'group': Number(groupNum),
            'layers': layerIdList,
        }]
    }
    doApiCall('PATCH', API_GROUPS, payload, onResponse);
}


"UI"

/*
<div>
    <span>{{ layer.title }}</span>
    <a class="layer_grouping_group_item_exclude"
       data-group-num="{{ group.num }}"
       data-layer-id="{{ layer.id }}"
    >x</a>
</div>
* */
function buildGroupItem(layerId, layerTitle, groupNum) {
    const span = document.createElement('span');
    span.textContent = layerTitle;

    const a = document.createElement('a');
    a.textContent = 'x'
    a.classList.add('layer_grouping_group_item_exclude')
    a.dataset['groupNum'] = groupNum;
    a.dataset['layerId'] = layerId;
    a.addEventListener('click', handleExcludeLayer);

    const div = document.createElement('div');
    div.append(span, a);
    return div;
}

function clear(node) {
    while (node.firstChild) {
        node.removeChild(node.lastChild);
    }
}

function setupGroupBucket(groupElem, data) {
    const groupNum = Number(groupElem.dataset['groupNum']);
    if (!groupNum)
        return;
    const groupData = data.groups.filter(obj => obj.num === groupNum);
    if (!groupData)
        return;
    // [{id, title}, ..]
    const grLayers = groupData[0].layers;

    clear(groupElem);
    groupElem.append(...grLayers.map(
        layerObj => buildGroupItem(layerObj.id, layerObj.title, groupNum)
    ));
}

/*
<div>
    <input type="checkbox" id="layer_grouping_item_{{ layer.id }}">
    <label for="layer_grouping_item_{{ layer.id }}" style="display:block;">
        {{ layer.title }}
    </label>
</div>
*/
function buildLayerItemNonGrouped(layerId, layerTitle) {
    const input = document.createElement('input');
    input.type = 'checkbox';

    const label = document.createElement('label');
    label.htmlFor = input.id = `layer_grouping_item_${layerId}`
    label.style.display = 'block';
    label.textContent = layerTitle;

    const div = document.createElement('div');
    div.append(input, label);
    div.dataset['layerId'] = layerId;
    return div;
}

function isLayerItemNonGroupedChecked(item) {
    return item.getElementsByTagName('input')[0].checked;
}

function setupNonGroupedContainer(container, data) {
    if (!container)
        return;

    // [{id, title}, ..]
    const nonGrouped = data.not_grouped_layers;
    if (!nonGrouped)
        return;

    clear(container);
    container.append(...nonGrouped.map(
       layerObj => buildLayerItemNonGrouped(layerObj.id, layerObj.title)
    ));
}

function setupAddBtnHandlers() {
    // class="group_setup_panel__group_container__add-btn"
    for (const btn of document.getElementsByClassName('group_setup_panel__group_container__add-btn')) {
        btn.addEventListener('click', handleAddLayersToGroup);
    }
}

function getNonGroupedContainer() {
    return document.getElementById('group_setup_panel__non_group_container');
}

function getSelectedLayerIds() {
    const container = getNonGroupedContainer();
    if (!container)
        return [];
    const checkedLayers = Array
        .from(container.children)
        .filter(layerItem => isLayerItemNonGroupedChecked(layerItem))

    const getLayerId = (layerItem) => layerItem.dataset['layerId'];
    return checkedLayers.map(getLayerId);
}

function getGroupBuckets(num=undefined) {
    const groupBuckets = document.getElementsByClassName('group_setup_panel__group_container__bucket');
    if (num) {
        const gr = Array.from(groupBuckets).filter(group => group.dataset['groupNum'] === num);
        if (gr)
            return gr[0];
    }
    return groupBuckets;
}

function setupAllBuckets() {
    apiGetAllGroupsData(function (rep) {
        setupNonGroupedContainer(getNonGroupedContainer(), rep);
        for (const elem of getGroupBuckets()) {
            setupGroupBucket(elem, rep);
        }
    });
    setupAddBtnHandlers();
}

function addDownloadPdfHandler() {
    const downloadPdfLabel = document.getElementById('download_pdf_label');
    downloadPdfLabel.addEventListener('click',
        (e) => e.currentTarget === e.target && handleFileDownloadWithRetryAfter(downloadPdfLabel.dataset.targetUrl))
}

"HANDLERS"

function makeUpdateHandlerNonGroupedAndBucket(groupNum) {
    return function (rep) {
        const groupChanged = getGroupBuckets(groupNum)
        setupNonGroupedContainer(getNonGroupedContainer(), rep);
        setupGroupBucket(groupChanged, rep);
    }
}

function handleAddLayersToGroup(e) {
    const layerGroupItem = e.target;
    const layersIdList = getSelectedLayerIds();
    const groupNum = layerGroupItem.dataset['groupNum'];
    apiIncludeLayersToGroup(layersIdList, groupNum, makeUpdateHandlerNonGroupedAndBucket(groupNum));
}

function handleExcludeLayer(e) {
    const layerGroupItem = e.target;
    const layerId = Number(layerGroupItem.dataset['layerId']);
    if (!layerId)
        return;

    const groupNum = layerGroupItem.dataset['groupNum'];
    apiExcludeLayers([layerId], makeUpdateHandlerNonGroupedAndBucket(groupNum))
}

setupAllBuckets();
addDownloadPdfHandler();
