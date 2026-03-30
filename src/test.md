---
template: src/test.html.temp
---
# HI THERE
### Test Ping
I am testing my [homepage](https://flench.me/)

And now my blog [test page](https://flench.me/blogs/test/)
But I think it is [broken](https://flench.me/blogs/test)

## Local storage status

<p><strong>Pages visited:</strong></p>
<ol id="visited-pages-list"></ol>

<script>
(function () {
  const VISITS_STORAGE_KEY = 'flench.pageVisits';
  const visitsEl = document.getElementById('visited-pages-list');

  if (!visitsEl) {
    return;
  }

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
