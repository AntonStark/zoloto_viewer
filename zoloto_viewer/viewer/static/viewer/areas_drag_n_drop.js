"use strict";
window.addEventListener('load', function () {
    let dragged;
    let id;
    let index;
    let indexDrop;
    let list;

    function debug() {
        console.log('dragged', dragged);
        console.log('id', id);
        console.log('index', index);
        console.log('indexDrop', indexDrop);
        console.log('list', list);
    }

    const planTable = document.getElementById('plan_table');

    planTable.addEventListener('dragstart', ({target}) => {
        dragged = target;
        id = target.id;
        list = target.parentNode.children;
        for (let i = 0; i < list.length; i += 1) {
            if (list[i] === dragged) {
                index = i;
            }
        }
        // debug();
    });

    planTable.addEventListener('dragover', (event) => {
        event.preventDefault();
    });

    planTable.addEventListener('drop', ({target}) => {
        if (planTable.contains(target)) {
            while (target.tagName !== 'TR') {
                target = target.parentNode;
            }
        }
        if (target.id !== id) {
            dragged.remove(dragged);
            for (let i = 0; i < list.length; i += 1) {
                if (list[i] === target) {
                    indexDrop = i;
                }
            }
            console.log(index, indexDrop);
            if (index > indexDrop) {
                target.before(dragged);
            } else {
                target.after(dragged);
            }
        }
        // debug();
    });
});
