const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const { JSDOM } = require('jsdom');

const academyScript = fs.readFileSync(
  path.resolve(__dirname, '../../static/js/academy.js'),
  'utf8'
);

function navigationPage(slug = 'live-course') {
  const dom = new JSDOM(`
    <main data-academy-page-status="live" data-tutorial-slug="${slug}">
      <button data-academy-nav-toggle aria-expanded="false" aria-controls="academy-step-panel">Tutorial progress</button>
      <div id="academy-step-panel" hidden>
        <ol id="academy-step-list"></ol>
      </div>
      <div id="page-content">
        <h2 id="configure">Configure the project</h2>
        <h2 id="verify">Verify the result</h2>
      </div>
    </main>
  `, { runScripts: 'outside-only', url: `https://developers.yubico.com/Academy/${slug}/` });

  let observerCallback;
  dom.window.IntersectionObserver = class {
    constructor(callback) { observerCallback = callback; }
    observe() {}
  };
  return { dom, notify: entries => observerCallback(entries) };
}

test('section navigation uses anchors and persists current and visited state by slug', () => {
  const { dom, notify } = navigationPage();
  dom.window.eval(academyScript);

  const document = dom.window.document;
  const links = document.querySelectorAll('#academy-step-list a');
  assert.deepEqual(Array.from(links, link => link.getAttribute('href')), [
    '#configure',
    '#verify',
  ]);

  notify([{ target: document.querySelector('#verify'), isIntersecting: true }]);
  assert.equal(links[1].getAttribute('aria-current'), 'step');
  assert.ok(links[1].closest('li').classList.contains('is-visited'));
  assert.deepEqual(
    JSON.parse(dom.window.localStorage.getItem('academy-progress-live-course')),
    { current: 'verify', visited: ['verify'] }
  );
});

test('mobile progress disclosure exposes its controlled panel', () => {
  const { dom } = navigationPage();
  dom.window.eval(academyScript);
  const toggle = dom.window.document.querySelector('[data-academy-nav-toggle]');
  const panel = dom.window.document.querySelector('#academy-step-panel');

  toggle.click();
  assert.equal(toggle.getAttribute('aria-expanded'), 'true');
  assert.equal(panel.hidden, false);
});

test('progress restores after reload and remains isolated between tutorial slugs', () => {
  const first = navigationPage('live-course');
  first.dom.window.localStorage.setItem(
    'academy-progress-live-course',
    JSON.stringify({ current: 'configure', visited: ['configure'] })
  );
  first.dom.window.eval(academyScript);
  assert.equal(
    first.dom.window.document.querySelector('a[href="#configure"]').getAttribute('aria-current'),
    'step'
  );

  const second = navigationPage('different-course');
  second.dom.window.eval(academyScript);
  assert.equal(second.dom.window.document.querySelector('[aria-current="step"]'), null);
});

test('navigation still initializes when localStorage throws', () => {
  const { dom } = navigationPage();
  Object.defineProperty(dom.window, 'localStorage', {
    get() { throw new Error('storage unavailable'); },
  });

  assert.doesNotThrow(() => dom.window.eval(academyScript));
  assert.equal(dom.window.document.querySelectorAll('#academy-step-list a').length, 2);
});
