(function () {
  'use strict';

  const mobileQuery = window.matchMedia('(max-width: 767.98px)');

  function initializePriorityNavigation(nav) {
    if (nav.dataset.priorityNavReady === 'true') return;

    const list = nav.querySelector('[data-priority-items]');
    const more = nav.querySelector('[data-priority-more]');
    const overflow = nav.querySelector('[data-priority-overflow]');
    if (!list || !more || !overflow) return;

    const moreButton = more.querySelector('button');

    nav.dataset.priorityNavReady = 'true';
    const items = Array.from(list.querySelectorAll(':scope > [data-priority-item]'));
    const overflowItems = items.map(item => {
      const sourceLink = item.querySelector('.nav-link');
      const overflowItem = document.createElement('li');
      const overflowLink = sourceLink.cloneNode(true);
      overflowLink.className = 'dropdown-item';
      overflowItem.appendChild(overflowLink);
      overflowItem.hidden = true;
      overflow.appendChild(overflowItem);
      return overflowItem;
    });

    function closeOverflow() {
      overflow.hidden = true;
      moreButton.setAttribute('aria-expanded', 'false');
    }

    moreButton.addEventListener('click', () => {
      const willOpen = overflow.hidden;
      closeOverflow();
      if (willOpen) {
        overflow.hidden = false;
        moreButton.setAttribute('aria-expanded', 'true');
      }
    });

    document.addEventListener('click', event => {
      if (!more.contains(event.target)) closeOverflow();
    });

    more.addEventListener('keydown', event => {
      if (event.key !== 'Escape') return;
      closeOverflow();
      moreButton.focus();
    });

    function layout() {
      closeOverflow();
      items.forEach(item => { item.hidden = false; });
      overflowItems.forEach(item => { item.hidden = true; });
      more.hidden = true;

      if (mobileQuery.matches || list.clientWidth === 0) return;
      if (list.scrollWidth <= list.clientWidth) return;

      more.hidden = false;
      while (list.scrollWidth > list.clientWidth) {
        const visible = items.filter(item => !item.hidden);
        const nonActive = visible.filter(item => !item.querySelector('[aria-current="page"]'));
        const item = nonActive.at(-1) || visible.at(-1);
        if (!item) break;

        const index = items.indexOf(item);
        item.hidden = true;
        overflowItems[index].hidden = false;
      }

      more.hidden = overflowItems.every(item => item.hidden);
    }

    let layoutFrame;
    function scheduleLayout() {
      if (layoutFrame) window.cancelAnimationFrame(layoutFrame);
      layoutFrame = window.requestAnimationFrame(() => {
        layoutFrame = null;
        layout();
      });
    }

    if ('ResizeObserver' in window) {
      const observer = new ResizeObserver(scheduleLayout);
      observer.observe(nav);
      observer.observe(list);
    } else {
      window.addEventListener('resize', scheduleLayout);
    }
    mobileQuery.addEventListener?.('change', scheduleLayout);
    document.fonts?.ready.then(scheduleLayout);
    window.addEventListener('load', scheduleLayout);
    scheduleLayout();
  }

  function initializeAll() {
    document.querySelectorAll('[data-priority-nav]').forEach(initializePriorityNavigation);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAll, { once: true });
  } else {
    initializeAll();
  }
}());
