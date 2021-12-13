const MessBuilder = () => {
    function buildHeader(data) {
        const markerNumber = data.number;
        let header = document.createElement('div');
        header.textContent = markerNumber;
        return header;
    }
    function buildCommentElem(commentObj) {
        const comment = commentObj.content;
        let commentBlock = document.createElement('div');
        commentBlock.textContent = comment;
        if (commentObj.resolved) commentBlock.setAttribute('style', 'color: lightgrey;');
        return commentBlock;
    }
    function buildCommentBlock(data) {
        const [hasComment, comments] = [data.has_comment, data.comments];
        const label = ( hasComment ? 'Комментарии' : 'Комментариев нет');
        const placeholder = ( hasComment ? 'Добавить комментарий' : 'Можно не заполнять');

        let commentLabel = document.createElement('span');
        commentLabel.setAttribute('style', 'font-size: 10px;');
        commentLabel.textContent = label;

        let commentsBlock = document.createElement('div');
        commentsBlock.append(...comments.map(c => this._buildCommentElem(c)))

        let commentInput = document.createElement('textarea');
        commentInput.setAttribute('class', 'comment_field');
        commentInput.setAttribute('placeholder', placeholder);
        commentInput.setAttribute('onkeyup', 'event.stopPropagation()');

        let commentDiv = document.createElement('div');
        commentDiv.append(
            commentLabel,
            commentsBlock,
            commentInput
        );
        return commentDiv;
    }
    function buildConfirmBtn(data) {
        let btnLink = document.createElement('a');
        btnLink.setAttribute('class', 'message_confirm_btn');
        btnLink.textContent = 'Проверено';
        btnLink.addEventListener('click',
            () => handlerConfirmBtnClick(data.marker));
        return btnLink;
    }

    function buildInfoplanBlock(data) {

    }

    function render(data) {
        const boxDiv = document.createElement('div');
        boxDiv.setAttribute('class', 'message_box');
        boxDiv.append(
            this._buildHeader(data),
            this._buildInfoplanBlock(data),
            this._buildCommentBlock(data),
            this._buildConfirmBtn(data)
        );
        return boxDiv;
    }

    return {
        _buildHeader: buildHeader,
        _buildCommentElem: buildCommentElem,
        _buildCommentBlock: buildCommentBlock,
        _buildConfirmBtn: buildConfirmBtn,
        _buildInfoplanBlock: buildInfoplanBlock,
        render: render,
    }
}
