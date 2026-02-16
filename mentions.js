// src/mentions.js
(function() {
  const target = window.location.href;
  const container = document.getElementById('webmentions');
  if (!container) return;

  fetch(`https://webmention.io/api/mentions.jf2?target=${target}`)
    .then(response => response.json())
    .then(data => {
      if (data.children.length === 0) return;
      
      let html = "<h4>Reactions:</h4><ul>";
      data.children.forEach(entry => {
        const author = entry.author.name || "Anonymous";
        const url = entry.url || "#";
        html += `<li><a href="${url}">${author}</a> mentioned this.</li>`;
      });
      html += "</ul>";
      
      container.innerHTML = html;
    });
})();