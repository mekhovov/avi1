document.addEventListener('keydown', function(event) {
    switch(event.key) {
        case 'ArrowUp':
            console.log('Up arrow pressed');
            break;
        case 'ArrowDown':
            console.log('Down arrow pressed');
            break;
        case 'ArrowLeft':
            console.log('Left arrow pressed');
            break;
        case 'ArrowRight':
            console.log('Right arrow pressed');
            break;
        default:
            // Do nothing for other keys
            break;
    }
});
