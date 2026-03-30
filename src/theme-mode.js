(function () {
  const params = new URLSearchParams(window.location.search);
  const requestedMode = (params.get('mode') || params.get('theme') || '').toLowerCase();
  const isDarkMode = requestedMode === 'dark';

  if (isDarkMode) {
    document.documentElement.setAttribute('data-mode', 'dark');

    const darkStylesheet = document.createElement('link');
    darkStylesheet.rel = 'stylesheet';
    darkStylesheet.href = '/dark.css';
    darkStylesheet.setAttribute('data-theme-stylesheet', 'dark');
    document.head.appendChild(darkStylesheet);
  }

  const keepModeInInternalLinks = () => {
    const anchors = document.querySelectorAll('a[href]');

    anchors.forEach((anchor) => {
      const href = anchor.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) {
        return;
      }

      let url;
      try {
        url = new URL(href, window.location.origin);
      } catch (_error) {
        return;
      }

      if (url.origin !== window.location.origin) {
        return;
      }

      if (isDarkMode) {
        if (!url.searchParams.has('mode') && !url.searchParams.has('theme')) {
          url.searchParams.set('mode', 'dark');
        }
      } else {
        url.searchParams.delete('mode');
        url.searchParams.delete('theme');
      }

      const newHref = href.startsWith('http') ? url.toString() : `${url.pathname}${url.search}${url.hash}`;
      anchor.setAttribute('href', newHref);
    });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', keepModeInInternalLinks, { once: true });
  } else {
    keepModeInInternalLinks();
  }
})();
