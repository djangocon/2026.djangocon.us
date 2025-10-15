/*
  Mobile site navigation
*/
const siteNav = document.getElementById('SiteNav');

if (siteNav) {
  const navToggler = document.getElementById('NavToggler');
  const allMenus = siteNav.querySelectorAll('[data-menu-list]');

  navToggler.addEventListener('click', () => {
    const siteBody = document.getElementById('SiteBody');
    const siteHeader = document.getElementById('SiteHeader');

    console.log('Toggling site navigation');
    console.log(siteNav.classList.contains('hidden'));

    if (siteNav.classList.contains('is-closed')) {
      siteNav.classList.replace('is-closed', 'is-open');
      siteHeader.classList.replace('is-closed', 'is-open');
      navToggler.classList.replace('is-closed', 'is-open');
    } else {
      siteNav.classList.replace('is-open', 'is-closed');
      siteHeader.classList.replace('is-open', 'is-closed');
      navToggler.classList.replace('is-open', 'is-closed');
    }

    /*
      Hide the main content and footer when the mobile menu is open.
      This allows the menu to be scrollable and limits the DOM for screen readers.
    */
    siteBody.classList.toggle('mobile-nav-open');
  });

  const navMenuTriggers = document.querySelectorAll('[data-menu-trigger]');

  navMenuTriggers.forEach(trigger => {
    trigger.addEventListener('click', (evt) => {
      evt.preventDefault();
      const target = trigger.nextElementSibling;

      navMenuTriggers.forEach((trigger) => {
        trigger.setAttribute('aria-expanded', 'false');
      });

      allMenus.forEach((menu) => {
        if (menu !== target) {
          menu.classList.replace('flex', 'hidden');
        }
      });

      if (target.classList.contains('hidden')) {
        target.classList.replace('hidden', 'flex');
        trigger.setAttribute('aria-expanded', 'true');
      } else {
        target.classList.replace('flex', 'hidden');
        trigger.setAttribute('aria-expanded', 'false');
      }
    });
  });

  // Close all menus when the user clicks outside
  document.addEventListener('click', function (evt) {
    if (!siteNav.contains(evt.target) && navToggler !== evt.target) {
      // Close all menus if you click outside of menu
      allMenus.forEach((menu) => {
        menu.classList.replace('flex', 'hidden');
      });

      navMenuTriggers.forEach((trigger) => {
        trigger.setAttribute('aria-expanded', 'false');
      });
    }
  });
}
