"use strict";

const API_PING               = `${BASE_URL}/viewer/api/ping/`;
const API_MARKER_CREATE      = `${BASE_URL}/viewer/api/marker/`;
const API_MARKER_CLIPBOARD   = `${BASE_URL}/viewer/api/marker/from_clipboard/`;
const API_MARKER_GET_DATA_MANY    = `${BASE_URL}/viewer/api/marker/fetch_many/`;
const API_MARKER_SUBMIT_DATA_MANY = `${BASE_URL}/viewer/api/marker/submit_many/`;
const API_MARKER_GET_DATA    = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}`;
const API_MARKER_GET_DATA_PRETTY = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}?pretty=true`;
const API_MARKER_PUT_VARS    = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}`;
const API_MARKER_PATCH_GEOM  = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}`;
const API_MARKER_DELETE      = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}`;
const API_VAR_ALTER_WRONG    = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}/variable/`;
const API_MARKER_LOAD_REVIEW = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}/review/`;
const API_MARKER_RESOLVE_CMS = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}/resolve_all_comments/`;
const API_MARKER_CAPTION_ONE = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}/caption/`;
const API_MARKERS_CAPTION    = (code)      => `${BASE_URL}/viewer/api/markers/caption/?floor=${code}`;
const API_PUT_PAGE_DATA      = (code)      => `${BASE_URL}/viewer/page/${code}/edit/`

function doApiCall(method, url, data, onResponse, onError=undefined, configure=undefined) {
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

    if (configure) {
        if (configure.timeout) {
            req.timeout = configure.timeout;
        }
    }

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

function requestCaptionsPlacement(floor_code, onSuccess) {
    doApiCall('GET', API_MARKERS_CAPTION(floor_code), null, onSuccess);
}

function updateCaptionPlacement(markerUid, offset, rotation, onSuccess) {
    let payload = {data: {}}
    if (offset !== undefined && offset !== null) {
        payload.data.offset = offset;
    }
    if (rotation !== undefined && rotation !== null) {
        payload.data.rotation = rotation;
    }
    doApiCall('PUT', API_MARKER_CAPTION_ONE(markerUid), payload, onSuccess);
}

function handleFileDownloadWithRetryAfter(uri, firstTry=true) {
    const method = 'HEAD';
    let req = new XMLHttpRequest();
    req.open(method, uri);

    function onSuccess(req) {
        // console.debug('onSuccess');
        window.open(uri);
    }
    function onRetry(req) {
        if (firstTry) {
            alert('На подготовку файла потребуется некоторое время.\n' +
                'Файл откроется в новой вкладке в течении пары минут\n' +
                'или повторите запрос позднее.');
        }
        const waitSeconds = req.getResponseHeader('Retry-After')
        // console.debug('retry after', waitSeconds);
        const timeout = waitSeconds * 1000;
        setTimeout(handleFileDownloadWithRetryAfter, timeout, uri, false);
    }
    function onError(req) {
        console.log('handleFileDownloadWithRetry', 'unknown error', req);
    }
    req.onreadystatechange = function() {
        if (req.readyState === XMLHttpRequest.DONE) {
            if (req.status === 200) {
                onSuccess(req);
            } else if (req.status === 323) {
                onRetry(req);
            } else onError(req);
        }
    };

    // console.debug('handleFileDownloadWithRetry', method, uri);
    req.send();
}
