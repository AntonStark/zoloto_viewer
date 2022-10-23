function encodeClipboardContent(markerUidArray) {
    // for marker create call (POST /markers/) need object
    //  {
    //    project: uuid,
    //    page: string code,
    //    layer: string title,
    //    position: {
    //      center_x: int,
    //      center_y: int,
    //      rotation: int
    //    }
    //  }
    // and for setup infoplan (PUT /markers/<uuid>/) that object:
    //  {
    //    infoplan: [
    //      {side: 1, variables: ['a', 'b']},
    //    ]
    //  }
    // DECISION: send minimal required info to backend, copy with specific endpoint
    const content = {
        'clipboard_uuid': markerUidArray,
    }
    return JSON.stringify(content);
}

function decodeClipboardContent(content_string) {
    const parsedClipboard = JSON.parse(content_string)
    return parsedClipboard.clipboard_uuid;
}
