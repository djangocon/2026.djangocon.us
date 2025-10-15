console.log("Navbar removal script starting");
(function() {
    function isInIframe() {
        try {
            return window.self !== window.top;
        } catch (e) {
            return true;
        }
    }

    function removeNavbar() {
        if (!isInIframe()) {
            console.log('Page is not in an iframe, keeping navbar');
            return;
        }

        console.log('Page is in an iframe, attempting to remove navbar');
        var navbar = document.querySelector('nav');
        if (navbar) {
            console.log('Navbar found, removing');
            navbar.remove();
        } else {
            console.log('Navbar not found');
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', removeNavbar);
    } else {
        removeNavbar();
    }
})();
console.log("Navbar removal script ended");
