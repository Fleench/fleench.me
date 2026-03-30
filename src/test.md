---
template: src/test.html.temp
---
# HI THERE
### Test Ping
<div class="buttons-row">
  <a class="button-88x31" href="/test/?mode=light" data-theme-switch="light">Light mode</a>
  <a class="button-88x31" href="/test/?mode=dark" data-theme-switch="dark">Dark mode</a>
</div>

I am testing my [homepage](https://flench.me/)

And now my blog [test page](https://flench.me/blogs/test/)
But I think it is [broken](https://flench.me/blogs/test)

## Local storage status

<p><strong>Saved theme mode:</strong> <span id="saved-theme-mode">(loading)</span></p>
<p><strong>Pages visited:</strong></p>
<ol id="visited-pages-list"></ol>

<script>
(function () {
  const THEME_STORAGE_KEY = 'flench.themeMode';
  const VISITS_STORAGE_KEY = 'flench.pageVisits';
  const modeEl = document.getElementById('saved-theme-mode');
  const visitsEl = document.getElementById('visited-pages-list');

  if (!modeEl || !visitsEl) {
    return;
  }

  const savedMode = localStorage.getItem(THEME_STORAGE_KEY) || '(not set)';
  modeEl.textContent = savedMode;

  let visits = [];
  try {
    const parsed = JSON.parse(localStorage.getItem(VISITS_STORAGE_KEY) || '[]');
    if (Array.isArray(parsed)) {
      visits = parsed;
    }
  } catch (_error) {
    visits = [];
  }

  if (visits.length === 0) {
    const item = document.createElement('li');
    item.textContent = 'No visits saved yet.';
    visitsEl.appendChild(item);
    return;
  }

  visits
    .slice()
    .reverse()
    .forEach((visit) => {
      const item = document.createElement('li');
      const visitUrl = typeof visit.url === 'string' ? visit.url : '(unknown url)';
      const visitedAt = typeof visit.visitedAt === 'string' ? visit.visitedAt : '(unknown time)';
      item.textContent = `${visitUrl} — ${visitedAt}`;
      visitsEl.appendChild(item);
    });
})();
</script>

# BOO ---test---{}---UP
Yo this is at the bottom
# HI ---left
![](/profile.png)
