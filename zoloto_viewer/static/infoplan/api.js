"use strict";

const BASE_URL = 'http://localhost:8000/viewer/api/';
const API_MARKER_GET_DATA       = (marker_uid) => BASE_URL + `marker/${marker_uid}`;
const API_MARKER_LOAD_REVIEW    = (marker_uid) => BASE_URL + `marker/${marker_uid}/review/`;
const API_VARIABLE_ALTER_WRONG  = (marker_uid) => BASE_URL + `marker/${marker_uid}/variable/`;

function handlerMessBlur(marker_uid) {
    // todo send req

    return () => messageBoxManager.hide(marker_uid);
}

function handleToggleWrong(marker_uid, variable_key) {
    // console.debug('handleToggleWrong', marker_uid, variable_key);
    let req = new XMLHttpRequest();
    req.open('POST', API_VARIABLE_ALTER_WRONG(marker_uid));
    req.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    req.onreadystatechange = function() {
        if (req.readyState === XMLHttpRequest.DONE) {
            if (req.status === 200) {
                // console.debug(req, 'modifyView');
                const rep = JSON.parse(req.responseText);
                varWrongnessManager.sync(rep);
                markerCirclesManager.sync(rep);
            }
            else {
                console.error(req);
            }
        }
    };
    const toggledStatus = !varWrongnessManager.status(marker_uid, variable_key);
    req.send(JSON.stringify({'key': variable_key, 'wrong': toggledStatus}));
}

function handleClickMarkerCircle(circleElement) {
    const elemData = circleElement.dataset;
    markerCirclesManager.register(circleElement);
    messageBoxManager.show(elemData.markerUid);
}
