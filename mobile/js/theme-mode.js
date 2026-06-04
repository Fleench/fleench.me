(function () {
  const THEME_STORAGE_KEY = 'flench.themeMode';
  const VISITS_STORAGE_KEY = 'flench.pageVisits';

  const params = new URLSearchParams(window.location.search);
  const requestedMode = (params.get('mode') || '').toLowerCase();
  let activeMode = 'dark';
  if (requestedMode === 'light' || requestedMode === 'dark') {
    activeMode = requestedMode;
  }

  const isLightMode = activeMode === 'light';

  const applyMode = () => {
    if (isLightMode) {
      document.documentElement.setAttribute('data-mode', 'light');
      return;
    }

    document.documentElement.setAttribute('data-mode', 'dark');

    if (!document.querySelector('link[data-theme-stylesheet="dark"]')) {
      const darkStylesheet = document.createElement('link');
      darkStylesheet.rel = 'stylesheet';
      darkStylesheet.href = '/css/dark.css';
      darkStylesheet.setAttribute('data-theme-stylesheet', 'dark');
      document.head.appendChild(darkStylesheet);
    }
  };

  const persistMode = () => {
    localStorage.setItem(THEME_STORAGE_KEY, activeMode);
  };

  const trackPageVisit = () => {
    const visit = {
      url: `${window.location.pathname}${window.location.search}${window.location.hash}`,
      title: document.title,
      visitedAt: new Date().toISOString(),
    };

    let visits = [];

    try {
      const parsed = JSON.parse(localStorage.getItem(VISITS_STORAGE_KEY) || '[]');
      if (Array.isArray(parsed)) {
        visits = parsed;
      }
    } catch (_error) {
      visits = [];
    }

    visits.push(visit);
    localStorage.setItem(VISITS_STORAGE_KEY, JSON.stringify(visits.slice(-200)));
  };

  const keepModeInInternalLinks = () => {
    const anchors = document.querySelectorAll('a[href]');

    anchors.forEach((anchor) => {
      const href = anchor.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) {
        return;
      }

      let url;
      try {
        url = new URL(href, window.location.href);
      } catch (_error) {
        return;
      }

      if (url.origin !== window.location.origin) {
        return;
      }

      if (isLightMode) {
        url.searchParams.delete('theme');
        url.searchParams.set('mode', 'light');
      } else {
        url.searchParams.delete('mode');
        url.searchParams.delete('theme');
      }

      const newHref = href.startsWith('http') ? url.toString() : `${url.pathname}${url.search}${url.hash}`;
      anchor.setAttribute('href', newHref);
    });
  };

  applyMode();
  persistMode();
  trackPageVisit();

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', keepModeInInternalLinks, { once: true });
  } else {
    keepModeInInternalLinks();
  }
})();
