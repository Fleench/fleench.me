(function () {
  const sidebar = document.getElementById('left-sidebar');
  const rsidebar = document.getElementById('right-sidebar');
  const toggleButton = document.querySelector('.sidebar-toggle-button');
  if (rsidebar.innerText == "{{ right sidebar }}") {
      rsidebar.style.display = "None"
  }
  if (sidebar.innerText == "{{ left sidebar }}") {
      sidebar.style.display = "None"
      toggleButton.style.display = "None"
      return;
  }
  if (!sidebar || !toggleButton) {
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
