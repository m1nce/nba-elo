(function () {
    var draggedTeam = null;

    document.addEventListener('dragstart', function (e) {
        var tile = e.target.closest('[data-team]');
        if (tile) draggedTeam = tile.getAttribute('data-team');
    });

    document.addEventListener('dragover', function (e) {
        if (e.target.closest('[data-slot]')) e.preventDefault();
    });

    document.addEventListener('dragenter', function (e) {
        var slot = e.target.closest('[data-slot]');
        if (slot) slot.classList.add('drag-over');
    });

    document.addEventListener('dragleave', function (e) {
        var slot = e.target.closest('[data-slot]');
        if (slot && !slot.contains(e.relatedTarget)) slot.classList.remove('drag-over');
    });

    document.addEventListener('drop', function (e) {
        var slot = e.target.closest('[data-slot]');
        if (!slot || !draggedTeam) return;
        e.preventDefault();
        slot.classList.remove('drag-over');

        var slotName = slot.getAttribute('data-slot');
        var payload  = JSON.stringify({ slot: slotName, team: draggedTeam });

        // Update the hidden Dash input with a React-compatible synthetic event
        var input = document.getElementById('dnd-event');
        if (!input) return;
        var setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        setter.call(input, payload);
        input.dispatchEvent(new Event('input', { bubbles: true }));
    });
})();
