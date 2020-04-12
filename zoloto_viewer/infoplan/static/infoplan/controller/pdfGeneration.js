function onPdfRefreshSuccess(rep) {
    const origUrl = rep['pdf_original'];
    const reviewedUrl = rep['pdf_reviewed'];
    const creationTime = rep['pdf_created_time'];
    const refreshTimeout = rep['pdf_refresh_timeout'];
    console.log(origUrl, reviewedUrl, creationTime, refreshTimeout);

    const linkPdfRefresh = document.getElementById('pdf_generation_link');
    linkPdfRefresh.dataset.activateAfter = refreshTimeout;
    const labelPdfCreated = linkPdfRefresh.previousElementSibling;
    labelPdfCreated.textContent = creationTime;

    const linkPdfOriginal = document.getElementById('pdf_original_link');
    linkPdfOriginal.href = origUrl;
    const linkPdfReviewed = document.getElementById('pdf_reviewed_link');
    linkPdfReviewed.href = reviewedUrl;
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
    // console.debug(nowDate, targetDate, after);
}
const EVERY_MINUTE = 60 * 1000;
window.setInterval(pdfRefreshLinkController, EVERY_MINUTE);
window.addEventListener('load', pdfRefreshLinkController);  // to set proper style on load

const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.type === "attributes") {
            pdfRefreshLinkController();
        }
    });
});
function setupObserver() {
    const linkPdfRefresh = document.getElementById('pdf_generation_link');
    observer.observe(linkPdfRefresh, {
        attributes: true
    });
}
window.addEventListener('load', setupObserver);
