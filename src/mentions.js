(function() {
  const container = document.getElementById('webmentions');
  if (!container) return;

  // 1. Get the current page URL (stripping trailing slashes for consistency if needed)
  // Add this line before your fetch
  let target = window.location.href;
  if (!target.endsWith('/')) {
      target += '/';
  }

fetch(`https://webmention.io/api/mentions.jf2?target=${encodeURIComponent(target)}`)
  // 2. Fetch from Webmention.io
  fetch(`https://webmention.io/api/mentions.jf2?target=${encodeURIComponent(target)}`)
    .then(response => response.json())
    .then(data => {
      const mentions = data.children || [];
      
      if (mentions.length === 0) {
        container.innerHTML = '<p class="no-mentions">No webmentions yet. Be the first!</p>';
        return;
      }

      let html = '<ul class="mention-list">';
      
      mentions.forEach(entry => {
        // Safe fallbacks for missing data
        const authorName = entry.author?.name || "Anonymous";
        const authorUrl = entry.author?.url || "#";
        const authorPhoto = entry.author?.photo || ""; // You could add a default pixel art avatar here
        const published = entry.published ? new Date(entry.published).toLocaleDateString() : "";
        const sourceUrl = entry.url || "#";
        
        // Decide what to show (Logic: If it has text, show it. If not, it's likely just a "Like" or "Repost")
        const content = entry.content?.html || entry.content?.text || "";
        const isLike = entry['wm-property'] === 'like-of';
        const isRepost = entry['wm-property'] === 'repost-of';

        let actionText = "mentioned this";
        if (isLike) actionText = "liked this";
        if (isRepost) actionText = "reposted this";

        html += `
          <li class="mention-card">
            <div class="mention-header">
              ${authorPhoto ? `<img src="${authorPhoto}" alt="${authorName}" class="mention-avatar">` : ''}
              <a href="${authorUrl}" target="_blank" rel="nofollow"><strong>${authorName}</strong></a>
              <span class="mention-action">${actionText}</span>
              <a href="${sourceUrl}" class="mention-date">${published}</a>
            </div>
            ${content ? `<div class="mention-body">${content}</div>` : ''}
          </li>
        `;
      });

      html += '</ul>';
      container.innerHTML = html;
    })
    .catch(err => {
      console.error("Error fetching webmentions:", err);
      container.innerHTML = '<p>Unable to load mentions.</p>';
    });
})();