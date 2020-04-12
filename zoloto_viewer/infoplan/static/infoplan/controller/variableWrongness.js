"use strict";
function ControllerVariableWrongness() {
    const WRONG_VARIABLE_CLASS = 'wrong_variable';
    let variablesItemsIndex = {};       // { marker_uid -> { key -> Item} }
    let variablesWrongnessIndex = {};       // { marker_uid -> { key -> isWrong} }

    function _setVariableWrongness(varItem, wantedStatus) {
        if (varItem.classList.contains(WRONG_VARIABLE_CLASS) !== wantedStatus)
            varItem.classList.toggle(WRONG_VARIABLE_CLASS);
    }

    function registerVariableItem(markerUid, key, item, isWrong) {
        if (variablesItemsIndex[markerUid] === undefined)
            variablesItemsIndex[markerUid] = {};
        variablesItemsIndex[markerUid][key] = item;

        if (variablesWrongnessIndex[markerUid] === undefined)
            variablesWrongnessIndex[markerUid] = {};
        variablesWrongnessIndex[markerUid][key] = isWrong;
        _setVariableWrongness(variablesItemsIndex[markerUid][key], isWrong);
    }
    function updateWrongStatus(markerVarData) {
        const [markerUid, varData] = [markerVarData.marker, markerVarData.variable];
        const [key, wrong] = [varData.key, varData.wrong];

        if (variablesItemsIndex[markerUid] && variablesItemsIndex[markerUid][key]) {
            variablesWrongnessIndex[markerUid][key] = wrong;
            _setVariableWrongness(variablesItemsIndex[markerUid][key], wrong);
        }
    }
    function isWrong(markerUid, key) {
        if (variablesWrongnessIndex[markerUid] && variablesWrongnessIndex[markerUid][key])
            return variablesWrongnessIndex[markerUid][key];
        else
            return undefined;
    }
    function allMarkerVars(markerUid) {
        const mData = variablesWrongnessIndex[markerUid];
        if (!mData)
            return undefined;

        return Object.entries(mData)
            .map((pair) => ({'key': pair[0], 'wrong': pair[1]}));
    }

    return {
        register: registerVariableItem,
        sync    : updateWrongStatus,
        status  : isWrong,
        data    : allMarkerVars,
    }
}
