(function () {
  const sidebar = document.getElementById('left-sidebar');
  const rsidebar = document.getElementById('right-sidebar');
  const toggleButton = document.querySelector('.sidebar-toggle-button');
  const nav = document.getElementById('NAV');

  const isTrulyEmpty = (element) => {
    if (!element) {
      return true;
    }

    for (const node of element.childNodes) {
      if (node.nodeType === Node.ELEMENT_NODE) {
        return false;
      }
      if (node.nodeType === Node.TEXT_NODE && node.textContent.trim() !== '') {
        return false;
      }
    }

    return true;
  };

  if (nav) {
    if (!rsidebar || isTrulyEmpty(rsidebar)) {
      if (rsidebar) {
        rsidebar.style.display = 'none';
      }
      nav.style.marginRight = '0px';
    }

    if (!sidebar || isTrulyEmpty(sidebar)) {
      if (sidebar) {
        sidebar.style.display = 'none';
      }
      if (toggleButton) {
        toggleButton.style.display = 'none';
      }
      nav.style.marginLeft = '0px';
    }
  }

  if (!sidebar || !toggleButton || isTrulyEmpty(sidebar)) {
    return;
  }

  const mobileQuery = window.matchMedia('(max-width: 860px)');

  const setSidebarState = () => {
    if (mobileQuery.matches) {
      toggleButton.hidden = false;
      sidebar.hidden = true;
      toggleButton.setAttribute('aria-expanded', 'false');
      return;
    }

    toggleButton.hidden = true;
    sidebar.hidden = false;
    toggleButton.setAttribute('aria-expanded', 'true');
  };

  toggleButton.addEventListener('click', () => {
    const willExpand = sidebar.hidden;
    sidebar.hidden = !willExpand;
    toggleButton.setAttribute('aria-expanded', willExpand ? 'true' : 'false');
  });

  if (typeof mobileQuery.addEventListener === 'function') {
    mobileQuery.addEventListener('change', setSidebarState);
  } else {
    mobileQuery.addListener(setSidebarState);
  }

  setSidebarState();
})();
