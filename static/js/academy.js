(function () {
  var stepList = document.getElementById('academy-step-list');
  if (!stepList) return;

  var headings = document.querySelectorAll('#page-content h2');
  if (!headings.length) return;

  var STORAGE_KEY = 'academy-visited-' + window.location.pathname;
  var visited = {};
  try { visited = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch (e) {}

  // Build step dots from H2 headings
  headings.forEach(function (h, i) {
    if (!h.id) h.id = 'step-' + i;
    var li = document.createElement('li');
    li.dataset.target = h.id;
    if (visited[h.id]) li.classList.add('is-visited');
    var dot = document.createElement('span');
    dot.className = 'academy-step-dot';
    dot.textContent = String(i + 1);
    var label = document.createElement('span');
    label.textContent = h.textContent;
    li.appendChild(dot);
    li.appendChild(label);
    li.addEventListener('click', function () { h.scrollIntoView({ behavior: 'smooth' }); });
    stepList.appendChild(li);
  });

  var items = stepList.querySelectorAll('li');

  // IntersectionObserver: highlight current section, mark visited
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var id = entry.target.id;
      items.forEach(function (li) {
        var isCurrent = li.dataset.target === id;
        li.classList.toggle('is-current', isCurrent);
        if (isCurrent) { li.classList.add('is-visited'); visited[id] = 1; }
      });
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(visited)); } catch (e) {}
    });
  }, { rootMargin: '0px 0px -60% 0px', threshold: 0 });

  headings.forEach(function (h) { observer.observe(h); });
}());

// Copy-to-clipboard for code blocks
(function () {
  if (!navigator.clipboard) return;
  document.querySelectorAll('#page-content .listingblock pre').forEach(function (pre) {
    var content = pre.parentElement;
    var btn = document.createElement('button');
    btn.className = 'academy-copy-btn';
    btn.setAttribute('aria-label', 'Copy code');
    btn.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">' +
        '<path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />' +
      '</svg>' +
      '<span class="academy-copy-label">Copy</span>';
    btn.addEventListener('click', function () {
      var code = pre.querySelector('code') ? pre.querySelector('code').innerText : pre.innerText;
      navigator.clipboard.writeText(code).then(function () {
        btn.classList.add('academy-copy-btn--copied');
        btn.querySelector('.academy-copy-label').textContent = 'Copied!';
        setTimeout(function () {
          btn.classList.remove('academy-copy-btn--copied');
          btn.querySelector('.academy-copy-label').textContent = 'Copy';
        }, 1500);
      });
    });
    content.appendChild(btn);
  });
}());
