(function() {
  const container = document.getElementById('webmentions');

  if (!container) {
    console.error('Webmention Error: Could not find #webmentions element in HTML.');
    return;
  }

  const canonicalHref = document.querySelector("link[rel='canonical']")?.href;

  function normalizeUrl(value) {
    try {
      const url = new URL(value, window.location.origin);
      url.hash = '';
      return url.toString();
    } catch {
      return null;
    }
  }

  function buildTargets() {
    const targets = new Set();

    function addVariant(url) {
      const normalized = normalizeUrl(url?.toString?.() || url);
      if (!normalized) return;

      if (targets.has(normalized)) return;

      const parsed = new URL(normalized);
      parsed.hash = '';
      const canonical = parsed.toString();
      if (targets.has(canonical)) return;
      targets.add(canonical);

      const pathHasTrailingSlash = parsed.pathname.endsWith('/');
      const isRootPath = parsed.pathname === '/';
      const isIndexHtml = parsed.pathname.endsWith('/index.html') || parsed.pathname === '/index.html';

      if (!isRootPath) {
        const slashVariant = new URL(parsed.toString());
        if (pathHasTrailingSlash) {
          slashVariant.pathname = slashVariant.pathname.replace(/\/+$/, '') || '/';
        } else {
          slashVariant.pathname = `${slashVariant.pathname}/`;
        }
        targets.add(slashVariant.toString());
      }

      if (!isIndexHtml) {
        const withIndex = new URL(parsed.toString());
        withIndex.pathname = withIndex.pathname.endsWith('/')
          ? `${withIndex.pathname}index.html`
          : `${withIndex.pathname}/index.html`;
        targets.add(withIndex.toString());
      } else {
        const withoutIndex = new URL(parsed.toString());
        withoutIndex.pathname = withoutIndex.pathname.replace(/\/index\.html$/, '') || '/';
        targets.add(withoutIndex.toString());
      }

      if (parsed.hostname.startsWith('www.')) {
        const withoutWww = new URL(parsed.toString());
        withoutWww.hostname = withoutWww.hostname.replace(/^www\./, '');
        addVariant(withoutWww);
      } else if (parsed.hostname.split('.').length > 1) {
        const withWww = new URL(parsed.toString());
        withWww.hostname = `www.${withWww.hostname}`;
        addVariant(withWww);
      }
    }

    const candidates = [
      window.location.href,
      window.location.origin + window.location.pathname,
      canonicalHref,
    ];

    candidates.forEach(addVariant);

    return Array.from(targets);
  }

  function mentionKey(entry) {
    return entry['wm-id'] || entry.url || `${entry.author?.url || 'anon'}-${entry.published || ''}-${entry['wm-property'] || ''}`;
  }

  const targets = buildTargets();
  console.debug('Webmention targets:', targets);

  Promise.all(
    targets.map((target) =>
      fetch(`https://webmention.io/api/mentions.jf2?target=${encodeURIComponent(target)}`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status} for ${target}`);
          }
          return response.json();
        })
        .then((data) => data.children || [])
        .catch((err) => {
          console.warn('Webmention warning:', err.message);
          return [];
        }),
    ),
  )
    .then((mentionSets) => {
      const mentions = [];
      const seen = new Set();

      mentionSets.flat().forEach((entry) => {
        const key = mentionKey(entry);
        if (seen.has(key)) return;
        seen.add(key);
        mentions.push(entry);
      });

      const countHeader = document.createElement('h4');
      countHeader.innerText = `${mentions.length} Reaction${mentions.length === 1 ? '' : 's'}`;
      countHeader.style.borderBottom = '1px solid #333';
      countHeader.style.paddingBottom = '5px';

      container.innerHTML = '';
      container.appendChild(countHeader);

      if (mentions.length === 0) {
        const noMentions = document.createElement('p');
        noMentions.innerText = 'No reactions found for this URL.';
        container.appendChild(noMentions);
        return;
      }

      const list = document.createElement('ul');
      list.style.listStyle = 'none';
      list.style.padding = '0';

      mentions.forEach((entry) => {
        const authorName = entry.author?.name || 'Anonymous';
        const authorUrl = entry.author?.url || entry.url || '#';
        const content = entry.content?.html || entry.content?.text || '';

        let action = 'interacted';
        if (entry['wm-property'] === 'like-of') action = 'liked';
        if (entry['wm-property'] === 'repost-of') action = 'reposted';
        if (entry['wm-property'] === 'mention-of') action = 'mentioned';

        const li = document.createElement('li');
        li.style.marginBottom = '1rem';
        li.style.padding = '10px';
        li.style.background = '#111';
        li.style.border = '1px solid #222';

        li.innerHTML = `
          <div style="font-size: 0.85rem; margin-bottom: 5px;">
            <a href="${authorUrl}"><strong>${authorName}</strong></a> ${action} this
            <a href="${entry.url}" style="float:right; font-size: 0.7rem; color: #555;">[source]</a>
          </div>
          ${content ? `<div style="font-size: 0.95rem; color: #ccc;">${content}</div>` : ''}
        `;
        list.appendChild(li);
      });

      container.appendChild(list);
    })
    .catch((err) => {
      console.error('Webmention JS Error:', err);
      container.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
    });
})();
