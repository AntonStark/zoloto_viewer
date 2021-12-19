function ControllerAreasList() {
    let pageCodesArray = [];
    let pageLinksArray = [];

    function init() {
        const areasBox = document.getElementsByClassName('areas-box side_box_list')[0];
        for (const pageLI of areasBox.children) {
            const pageLink = pageLI.firstElementChild.href;
            const pageCode = pageLink.split('/').at(-2);
            // console.log(pageLink, pageCode);
            pageCodesArray.push(pageCode);
            pageLinksArray.push(pageLink);
        }
    }

    function toUpperArea(currentCode) {
        const i = pageCodesArray.indexOf(currentCode);
        if (i < 0) {
            return
        }
        const upper = i - 1;
        if (upper < 0) {
            return;     // no upper page
        }
        location.href = pageLinksArray[upper];
    }

    function toLowerArea(currentCode) {
        const i = pageCodesArray.indexOf(currentCode);
        if (i < 0) {
            return
        }
        const lower = i + 1;
        if (lower >= pageCodesArray.length) {
            return;     // no lower page
        }
        location.href = pageLinksArray[lower];
    }

    return {
        init: init,
        toUpperArea: toUpperArea,
        toLowerArea: toLowerArea,
    }
}
