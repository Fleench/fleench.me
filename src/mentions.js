(function() {
  const container = document.getElementById('webmentions');
  
  // 1. Check if the container exists immediately
  if (!container) {
    console.error("Webmention Error: Could not find #webmentions element in HTML.");
    return;
  }

  // 2. Setup the target URL
  let target = window.location.href.split('#')[0];
  if (!target.endsWith('/')) target += '/';

  fetch(`https://webmention.io/api/mentions.jf2?target=${encodeURIComponent(target)}`)
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(data => {
      const mentions = data.children || [];
      
      // 3. Create the Counter Header
      const countHeader = document.createElement('h4');
      countHeader.innerText = `${mentions.length} Reaction${mentions.length === 1 ? '' : 's'}`;
      countHeader.style.borderBottom = "1px solid #333";
      countHeader.style.paddingBottom = "5px";
      
      // Clear "Loading" text and add the counter
      container.innerHTML = '';
      container.appendChild(countHeader);

      if (mentions.length === 0) {
        const noMentions = document.createElement('p');
        noMentions.innerText = "No reactions found for this URL.";
        container.appendChild(noMentions);
        return;
      }

      // 4. Build the List
      const list = document.createElement('ul');
      list.style.listStyle = "none";
      list.style.padding = "0";

      mentions.forEach(entry => {
        // Resilient Parsing: Use Optional Chaining for everything
        const authorName = entry.author?.name || "Anonymous";
        const authorUrl = entry.author?.url || entry.url || "#";
        const content = entry.content?.html || entry.content?.text || "";
        
        let action = "interacted";
        if (entry['wm-property'] === 'like-of') action = "liked";
        if (entry['wm-property'] === 'repost-of') action = "reposted";
        if (entry['wm-property'] === 'mention-of') action = "mentioned";

        const li = document.createElement('li');
        li.style.marginBottom = "1rem";
        li.style.padding = "10px";
        li.style.background = "#111";
        li.style.border = "1px solid #222";

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
    .catch(err => {
      console.error("Webmention JS Error:", err);
      container.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
    });
})();
