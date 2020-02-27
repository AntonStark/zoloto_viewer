"use strict";

const BASE_URL = 'http://localhost:8000';
const API_MARKER_GET_DATA    = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}`;
const API_VAR_ALTER_WRONG    = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}/variable/`;
const API_MARKER_LOAD_REVIEW = (markerUid) => `${BASE_URL}/viewer/api/marker/${markerUid}/review/`;

function doApiCall(method, url, data, onResponse) {
    let req = new XMLHttpRequest();
    req.open(method, url);

    req.onreadystatechange = function() {
        if (req.readyState === XMLHttpRequest.DONE) {
            if (req.status === 200) {
                const rep = JSON.parse(req.responseText);
                // console.debug(rep);
                onResponse(rep);
            }
            else {
                console.error(url, 'returned status = ', req.status, req);
            }
        }
    };

    req.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    req.send(JSON.stringify(data));
}

function handlerMessBlur(marker_uid) {
    const box = messageBoxManager.get(marker_uid);
    if (box !== undefined) {
        if (box.dataset.btnClicked) {
            delete box.dataset.btnClicked;
            return;
        }
    }

    const variables = varWrongnessManager.data(marker_uid);
    let comment = messageBoxManager.read(marker_uid);
    if (comment === undefined) {
        console.error('method for comment returned undefined', marker_uid);
        comment = '';
    }

    const data = {
        variables: variables,
        comment: comment,
        exit_type: 'blur',
    };
    doApiCall('POST', API_MARKER_LOAD_REVIEW(marker_uid), data,
         (rep) => markerCirclesManager.sync(rep));

    messageBoxManager.hide(marker_uid);
}

function handlerConfirmBtmClick(marker_uid) {
    const box = messageBoxManager.get(marker_uid);
    if (box !== undefined) {    // to distinguish click form blur in blur handler
        box.dataset.btnClicked = 'true';
    }

    const variables = varWrongnessManager.data(marker_uid);
    let comment = messageBoxManager.read(marker_uid);
    if (comment === undefined) {
        console.error('method for comment returned undefined', marker_uid);
        comment = '';
    }

    const data = {
        variables: variables,
        comment: comment,
        exit_type: 'button',
    };
    doApiCall('POST', API_MARKER_LOAD_REVIEW(marker_uid), data,
        (rep) => markerCirclesManager.sync(rep));

    messageBoxManager.hide(marker_uid);
}

function handlerMessageDivFocus(e) {
    const wrapper = e.target;
    const commentField = wrapper.getElementsByTagName('textarea');
    if (commentField.length > 0)
        commentField[0].focus();
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

function handleClickMarkerCircle(circleElement) {
    const markerElement = circleElement.parentNode.previousElementSibling;
    messageBoxManager.reg(markerElement);
    markerCirclesManager.register(circleElement);

    messageBoxManager.hideAll();
    messageBoxManager.show(circleElement.dataset.markerUid);
}
