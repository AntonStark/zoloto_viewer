"use strict";

const API_MARKER_CREATE      = `${BASE_URL}/viewer/api/marker/`;
const API_MARKER_CLIPBOARD   = `${BASE_URL}/viewer/api/marker/from_clipboard/`;
const API_MARKER_GET_DATA    = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}`;
const API_MARKER_GET_DATA_PRETTY = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}?pretty=true`;
const API_MARKER_PUT_VARS    = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}`;
const API_MARKER_PATCH_GEOM  = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}`;
const API_MARKER_DELETE      = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}`;
const API_VAR_ALTER_WRONG    = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}/variable/`;
const API_MARKER_LOAD_REVIEW = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}/review/`;
const API_MARKER_RESOLVE_CMS = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}/resolve_all_comments/`;
const API_PUT_PAGE_DATA      = (code)      => `${BASE_URL}/viewer/page/${code}/edit/`

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
                console.error(url, 'returned status = ', req.status, req);
            }
        }
    };

    req.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    req.send(JSON.stringify(data));
}

function handlerMessageDivFocus(e) {
    const wrapper = e.target;
    const commentField = wrapper.getElementsByTagName('textarea');
    if (commentField.length > 0)
        commentField[0].focus();
}

function takeMessageToFront(e) {
    const container = e.currentTarget;

    function getZIndex(elem) { return Number(elem.style.zIndex); }
    const maxZIndex = Math.max(...Array.from(
        document.getElementsByClassName('message_container')
        ).map(getZIndex)
    );

    container.style.zIndex = maxZIndex + 1;
}

function handleToggleWrong(marker_uid, variable_key) {
    const toggledStatus = !varWrongnessManager.status(marker_uid, variable_key);
    const data = {'key': variable_key, 'wrong': toggledStatus};
    doApiCall('POST', API_VAR_ALTER_WRONG(marker_uid), data,
        function (rep) {
        varWrongnessManager.sync(rep);
        markerCirclesManager.sync(rep);
    });
}

function deleteMarker(marker_uid, onSuccess) {
    doApiCall('DELETE', API_MARKER_DELETE(marker_uid), null, onSuccess);
}

function createMarker(args, onSuccess) {
    doApiCall('POST', API_MARKER_CREATE, args, onSuccess);
}

function clipMarkers(args, onSuccess) {
    doApiCall('POST', API_MARKER_CLIPBOARD, args, onSuccess);
}
