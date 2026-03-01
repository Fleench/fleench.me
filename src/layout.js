(function () {
  const sidebar = document.getElementById('left-sidebar');
  const rsidebar = document.getElementById('right-sidebar');
  const toggleButton = document.querySelector('.sidebar-toggle-button');
  const nav = document.getElementById("NAV");
  if (!rsidebar) {
      nav.style.marginRight = "0px";
  }
  else if (rsidebar.innerText == "") {
      rsidebar.style.display = "None";
      nav.style.marginRight = "0px";
  }
  if (!sidebar) {
	console.log("No Left Sidebar");
	if (toggleButton) {
	    toggleButton.style.display = "None";
	    }
	console.log("Issue Here")
    nav.style.marginLeft = "0px";
  }
  else if (sidebar.innerText == "" ) {

      sidebar.style.display = "None";
      if (toggleButton) {
          toggleButton.style.display = "None";
          }
      nav.style.marginLeft = "0px";
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
