const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const { JSDOM } = require('jsdom');

const priorityNavigationScript = fs.readFileSync(
  path.resolve(__dirname, '../../static/js/priority-navigation.js'),
  'utf8'
);

function navigationPage({ mobile = false, availableWidth = 260 } = {}) {
  const dom = new JSDOM(`
    <nav data-priority-nav>
      <a class="navbar-brand" href="/">Yubico Developers</a>
      <button class="navbar-toggler">Menu</button>
      <div class="navbar-collapse" id="navbarToggler">
        <ul data-priority-items>
          <li data-priority-item><a class="nav-link" href="/one/">One</a></li>
          <li data-priority-item><a class="nav-link active" aria-current="page" href="/active/">Active</a></li>
          <li data-priority-item><a class="nav-link" href="/three/">Three</a></li>
          <li data-priority-item><a class="nav-link" href="/four/">Four</a></li>
          <li data-priority-more hidden><button>More</button><ul data-priority-overflow></ul></li>
        </ul>
      </div>
      <div id="search-box">Search</div>
    </nav>
  `, { runScripts: 'outside-only', url: 'https://developers.yubico.com/active/' });

  const document = dom.window.document;
  const list = document.querySelector('[data-priority-items]');
  Object.defineProperty(list, 'clientWidth', { get: () => availableWidth });
  Object.defineProperty(list, 'scrollWidth', {
    get: () => {
      const visibleItems = Array.from(
        list.querySelectorAll(':scope > [data-priority-item]:not([hidden])')
      ).length;
      const more = list.querySelector('[data-priority-more]');
      return (visibleItems * 80) + (more.hidden ? 0 : 60);
    },
  });

  dom.window.matchMedia = () => ({ matches: mobile });
  dom.window.requestAnimationFrame = callback => callback();
  let resize;
  dom.window.ResizeObserver = class {
    constructor(callback) { resize = callback; }
    observe() {}
  };

  dom.window.eval(priorityNavigationScript);
  document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));

  return { dom, resize: () => resize() };
}

test('desktop navigation keeps the active section visible and moves only links that do not fit into More', () => {
  const { dom } = navigationPage();
  const document = dom.window.document;
  const visible = Array.from(
    document.querySelectorAll('[data-priority-item]:not([hidden]) .nav-link'),
    link => link.textContent
  );
  const overflow = Array.from(
    document.querySelectorAll('[data-priority-overflow] > li:not([hidden]) .dropdown-item'),
    link => link.textContent
  );

  assert.deepEqual(visible, ['One', 'Active']);
  assert.deepEqual(overflow, ['Three', 'Four']);
  assert.equal(document.querySelector('[data-priority-more]').hidden, false);
  assert.equal(document.querySelector('#search-box').closest('.navbar-collapse'), null);

  const moreButton = document.querySelector('[data-priority-more] > button');
  const overflowMenu = document.querySelector('[data-priority-overflow]');
  assert.equal(overflowMenu.hidden, true);
  moreButton.click();
  assert.equal(moreButton.getAttribute('aria-expanded'), 'true');
  assert.equal(overflowMenu.hidden, false);
});

test('mobile navigation restores every link to the hamburger while search remains outside it', () => {
  const { dom } = navigationPage({ mobile: true });
  const document = dom.window.document;

  assert.equal(document.querySelectorAll('[data-priority-item]:not([hidden])').length, 4);
  assert.equal(document.querySelector('[data-priority-more]').hidden, true);
  assert.equal(document.querySelector('#search-box').closest('.navbar-collapse'), null);
});
