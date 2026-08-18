var academyAnalyticsState = { currentSection: '' };

function analyticsConsentGranted() {
  try {
    return Boolean(window.cc && typeof window.cc.allowedCategory === 'function' &&
      window.cc.allowedCategory('analytics'));
  } catch (e) {
    return false;
  }
}

function pushAcademyEvent(eventName, params) {
  if (!analyticsConsentGranted()) return;
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push(Object.assign({ event: eventName }, params || {}));
}

window.pushAcademyEvent = pushAcademyEvent;

(function () {
  document.querySelectorAll('[data-academy-notify]').forEach(function (link) {
    link.addEventListener('click', function () {
      pushAcademyEvent('notify_me_click', {
        tutorial_name: link.dataset.tutorialName,
        tutorial_slug: link.dataset.tutorialSlug
      });
    });
  });

  var page = document.querySelector('[data-academy-page-status="live"]');
  if (!page) return;

  var tutorialName = page.dataset.tutorialName;
  var tutorialSlug = page.dataset.tutorialSlug;
  var knownTutorials = (page.dataset.academyTutorials || '').split('|');
  var headings = document.querySelectorAll('#page-content h2');
  var seenSections = {};
  var startSeen = false;
  var completeSeen = false;

  function showManualCopyFallback(url) {
    var status = document.querySelector('.academy-share-status');
    var fallback = document.querySelector('.academy-share-copy-fallback');
    if (!fallback) {
      fallback = document.createElement('input');
      fallback.type = 'text';
      fallback.className = 'academy-share-copy-fallback';
      fallback.readOnly = true;
      fallback.setAttribute('aria-label', 'Tutorial link to copy manually');
      if (status && status.parentNode) status.parentNode.insertBefore(fallback, status);
    }
    fallback.value = url;
    fallback.hidden = false;
    fallback.focus();
    fallback.select();
    if (status) status.textContent = 'Copy unavailable. Select and copy the link manually.';
  }

  if (headings.length) {
    var analyticsObserver = new IntersectionObserver(function (entries) {
      entries.filter(function (entry) { return entry.isIntersecting; })
        .sort(function (left, right) {
          return Array.prototype.indexOf.call(headings, left.target) -
            Array.prototype.indexOf.call(headings, right.target);
        })
        .forEach(function (entry) {
          var sectionIndex = Array.prototype.indexOf.call(headings, entry.target);
          var sectionName = entry.target.textContent.trim();
          academyAnalyticsState.currentSection = sectionName;
          if (seenSections[entry.target.id]) return;
          seenSections[entry.target.id] = true;

          if (sectionIndex === 0 && !startSeen) {
            startSeen = true;
            pushAcademyEvent('tutorial_start', {
              tutorial_name: tutorialName,
              tutorial_slug: tutorialSlug
            });
          }
          pushAcademyEvent('tutorial_section', {
            tutorial_name: tutorialName,
            section_name: sectionName,
            section_index: sectionIndex + 1,
            section_total: headings.length
          });
          if (sectionIndex === headings.length - 1 && !completeSeen) {
            completeSeen = true;
            pushAcademyEvent('tutorial_complete', { tutorial_name: tutorialName });
          }
        });
    }, { rootMargin: '0px 0px -60% 0px', threshold: 0 });
    headings.forEach(function (heading) { analyticsObserver.observe(heading); });
  }

  document.addEventListener('click', function (event) {
    var link = event.target.closest('a');
    if (link) {
      var href = link.href;
      var sdkDomains = ['github.com', 'mvnrepository.com', 'pypi.org', 'pkg.go.dev', 'npmjs.com', 'crates.io'];
      var parsedUrl;
      try { parsedUrl = new URL(href, window.location.href); } catch (e) {}
      if (parsedUrl && sdkDomains.indexOf(parsedUrl.hostname) !== -1) {
        pushAcademyEvent('sdk_clickout', {
          tutorial_name: tutorialName,
          sdk_url: href
        });
      }
      if (parsedUrl) {
        var match = parsedUrl.pathname.match(/^\/Academy\/([^/]+)\/?$/);
        if (match && knownTutorials.indexOf(match[1]) !== -1) {
          pushAcademyEvent('tutorial_progression', {
            tutorial_name: tutorialName,
            destination_tutorial: match[1]
          });
        }
      }
    }

    var shareControl = event.target.closest('[data-academy-share]');
    if (shareControl) {
      if (shareControl.dataset.academyShare === 'copy-link') {
        if (!navigator.clipboard || typeof navigator.clipboard.writeText !== 'function') {
          showManualCopyFallback(shareControl.dataset.academyCopyLink);
          return;
        }
        navigator.clipboard.writeText(shareControl.dataset.academyCopyLink).then(function () {
          var status = document.querySelector('.academy-share-status');
          if (status) status.textContent = 'Copied!';
          pushAcademyEvent('tutorial_share', {
            tutorial_name: tutorialName,
            share_platform: 'copy-link',
            section_name: academyAnalyticsState.currentSection,
            share_type: 'end-of-tutorial'
          });
        }).catch(function () {
          showManualCopyFallback(shareControl.dataset.academyCopyLink);
        });
        return;
      }
      pushAcademyEvent('tutorial_share', {
        tutorial_name: tutorialName,
        share_platform: shareControl.dataset.academyShare,
        section_name: academyAnalyticsState.currentSection,
        share_type: 'end-of-tutorial'
      });
    }
  });

  var nativeShare = document.querySelector('[data-academy-native-share]');
  if (nativeShare && navigator.share) {
    page.classList.add('academy-native-share-available');
    nativeShare.addEventListener('click', function () {
      var separator = page.dataset.canonicalUrl.indexOf('?') === -1 ? '?' : '&';
      var shareUrl = page.dataset.canonicalUrl + separator +
        'utm_source=academy-share&utm_medium=social&utm_campaign=' + encodeURIComponent(tutorialSlug);
      navigator.share({ url: shareUrl, title: tutorialName }).then(function () {
        pushAcademyEvent('tutorial_share', {
          tutorial_name: tutorialName,
          share_platform: 'native-share',
          section_name: academyAnalyticsState.currentSection,
          share_type: 'end-of-tutorial'
        });
      }).catch(function () {});
    });
  } else if (nativeShare) {
    nativeShare.hidden = true;
  }
}());

(function () {
  var filters = document.querySelectorAll('[data-academy-filter]');
  var cards = document.querySelectorAll('[data-academy-card]');
  if (!filters.length || !cards.length) return;

  var emptyState = document.querySelector('[data-academy-filter-empty]');

  function applyFilter(selectedTag) {
    var visibleCount = 0;

    filters.forEach(function (candidate) {
      var isSelected = candidate.dataset.academyFilter === selectedTag;
      candidate.classList.toggle('is-selected', isSelected);
      candidate.setAttribute('aria-pressed', isSelected ? 'true' : 'false');
    });

    cards.forEach(function (card) {
      var tags = (card.dataset.tutorialTags || '').split('|');
      var isVisible = selectedTag === 'all' || tags.indexOf(selectedTag) !== -1;
      card.hidden = !isVisible;
      if (isVisible) visibleCount += 1;
    });

    if (emptyState) emptyState.hidden = visibleCount !== 0;
  }

  filters.forEach(function (filter) {
    filter.addEventListener('click', function () {
      applyFilter(filter.dataset.academyFilter);
    });
  });
}());

(function () {
  var stepList = document.getElementById('academy-step-list');
  if (!stepList) return;

  var academyPage = document.querySelector('[data-academy-page-status="live"]');
  if (!academyPage) return;
  var headings = document.querySelectorAll('#page-content h2');
  if (!headings.length) return;

  var slug = academyPage.dataset.tutorialSlug;
  var storageKey = 'academy-progress-' + slug;
  var progress = { current: null, visited: [] };
  try {
    var savedProgress = JSON.parse(localStorage.getItem(storageKey) || 'null');
    if (savedProgress && Array.isArray(savedProgress.visited)) progress = savedProgress;
  } catch (e) {}

  var toggle = document.querySelector('[data-academy-nav-toggle]');
  if (toggle) {
    var panel = document.getElementById(toggle.getAttribute('aria-controls'));
    toggle.addEventListener('click', function () {
      var isExpanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', isExpanded ? 'false' : 'true');
      if (panel) panel.hidden = isExpanded;
    });
  }

  headings.forEach(function (h, i) {
    if (!h.id) h.id = 'step-' + i;
    var li = document.createElement('li');
    li.dataset.target = h.id;
    if (progress.visited.indexOf(h.id) !== -1) li.classList.add('is-visited');
    var link = document.createElement('a');
    link.href = '#' + h.id;
    if (progress.current === h.id) {
      li.classList.add('is-current');
      link.setAttribute('aria-current', 'step');
    }
    var dot = document.createElement('span');
    dot.className = 'academy-step-dot';
    dot.textContent = String(i + 1);
    var label = document.createElement('span');
    label.textContent = h.textContent;
    link.appendChild(dot);
    link.appendChild(label);
    li.appendChild(link);
    stepList.appendChild(li);
  });

  var items = stepList.querySelectorAll('li');

  var observer = new IntersectionObserver(function (entries) {
    var visibleHeadings = entries.filter(function (entry) { return entry.isIntersecting; });
    if (!visibleHeadings.length) return;
    visibleHeadings.sort(function (left, right) {
      return Array.prototype.indexOf.call(headings, left.target) -
        Array.prototype.indexOf.call(headings, right.target);
    });
    var id = visibleHeadings[0].target.id;
    progress.current = id;
    if (progress.visited.indexOf(id) === -1) progress.visited.push(id);
    items.forEach(function (li) {
      var isCurrent = li.dataset.target === id;
      li.classList.toggle('is-current', isCurrent);
      if (isCurrent) li.classList.add('is-visited');
      var link = li.querySelector('a');
      if (isCurrent) link.setAttribute('aria-current', 'step');
      else link.removeAttribute('aria-current');
    });
    try { localStorage.setItem(storageKey, JSON.stringify(progress)); } catch (e) {}
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
        var livePage = document.querySelector('[data-academy-page-status="live"]');
        if (livePage) {
          var codeElement = pre.querySelector('code');
          var languageMatch = codeElement && codeElement.className.match(/language-(\w+)/);
          if (!languageMatch) languageMatch = pre.closest('.listingblock').className.match(/language-(\w+)/);
          pushAcademyEvent('code_copy', {
            tutorial_name: livePage.dataset.tutorialName,
            section_name: academyAnalyticsState.currentSection,
            code_language: languageMatch ? languageMatch[1] : 'unknown'
          });
        }
      });
    });
    content.appendChild(btn);
  });
}());
