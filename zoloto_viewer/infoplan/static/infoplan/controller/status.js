/*
апи вызов дергает пинг апи
success handler – set success (green)
error handler - set error (red)

главный метод
перед запросом - set pending (yellow)
потом вызов к апи

при иницилизации интерфейса зарегать главный метов в setInterval(20)
* */

function StatusComponent() {
    let markElem;
    function init() {
        markElem = document.getElementsByClassName('actions_status')[0];
        setMarkPending();
    }

    function setMarkPending() {
        if (markElem) {
            markElem.style.color = 'gold';
        }
    }
    function setMarkSuccess() {
        if (markElem) {
            markElem.style.color = 'green';
        }
    }
    function setMarkError() {
        if (markElem) {
            markElem.style.color = 'red';
        }
    }

    return {
        init: init,
        setSuccess: setMarkSuccess,
        setError: setMarkError,
        setPending: setMarkPending,
    }
}

function checkApiStatus() {
    statusComponent.setPending();
    doApiCall('GET', API_PING, null, statusComponent.setSuccess, statusComponent.setError, {timeout: 3000});
}
