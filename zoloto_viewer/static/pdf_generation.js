function pdfRequest(url) {
    console.log('pdfRequest', url);

    function onResponse(rep) {
        console.log(rep);
    }
    let req = new XMLHttpRequest();
    req.open('POST', url);
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

    // todo обновлять время генерации и ссылки после ответа сервера
    //  (а также время после котрого показать ссылку для обновления)
    req.send();
}

function pdfRefreshLinkController() {
    const targetLink = document.getElementById('pdf_generation_link');
    const targetDate = new Date(targetLink.dataset.activateAfter);
    const nowDate = new Date();
    const after = nowDate > targetDate;
    if (after)
        targetLink.style.visibility = 'visible';
    else
        targetLink.style.visibility = 'hidden';
    console.debug(nowDate, targetDate, after);
}
window.addEventListener('load', pdfRefreshLinkController);

const EVERY_MINUTE = 60 * 1000;
window.setInterval(pdfRefreshLinkController, EVERY_MINUTE);
