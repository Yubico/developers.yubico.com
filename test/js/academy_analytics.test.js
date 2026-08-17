const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const { JSDOM } = require('jsdom');

const academyScript = fs.readFileSync(
  path.resolve(__dirname, '../../static/js/academy.js'),
  'utf8'
);

function academyPage(status = 'live', consent = false) {
  const isLive = status === 'live';
  const dom = new JSDOM(`
    <main data-academy-page-status="${status}"
          data-tutorial-slug="live-course"
          data-tutorial-name="Build a Live Course"
          data-canonical-url="https://developers.yubico.com/Academy/live-course/"
          data-academy-tutorials="live-course|next-course">
      <ol id="academy-step-list"></ol>
      <div id="page-content">
        <h2 id="first">First section</h2>
        <div class="listingblock language-java"><div class="content"><pre><code class="language-java">code</code></pre></div></div>
        <a class="sdk" href="https://github.com/Yubico/example">SDK</a>
        <a class="progression" href="/Academy/next-course/">Next</a>
        <h2 id="last">Last section</h2>
      </div>
      ${isLive ? '<button data-academy-share="twitter">Share</button><button data-academy-native-share>Share natively</button>' : ''}
      <a data-academy-notify data-tutorial-name="Build a Live Course" data-tutorial-slug="live-course" href="https://www.yubico.com/newsletter/">Notify me</a>
    </main>
  `, { runScripts: 'outside-only', url: 'https://developers.yubico.com/Academy/live-course/' });

  const observerCallbacks = [];
  dom.window.IntersectionObserver = class {
    constructor(callback) { observerCallbacks.push(callback); }
    observe() {}
  };
  dom.window.cc = { allowedCategory: () => consent };
  dom.window.dataLayer = [];
  dom.window.document.addEventListener('click', event => {
    if (event.target.closest('a')) event.preventDefault();
  });
  Object.defineProperty(dom.window.navigator, 'clipboard', {
    value: { writeText: () => Promise.resolve() },
    configurable: true,
  });

  return {
    dom,
    setConsent(value) { consent = value; },
    notify(entries) { observerCallbacks.forEach(callback => callback(entries)); },
    observerCount() { return observerCallbacks.length; },
  };
}

function academyEvents(dom) {
  return dom.window.dataLayer.filter(item => item.event && item.event !== 'gtm.js');
}

test('pushAcademyEvent never pushes before analytics consent', () => {
  const page = academyPage('coming-soon', false);
  page.dom.window.eval(academyScript);

  page.dom.window.pushAcademyEvent('notify_me_click', { tutorial_slug: 'live-course' });

  assert.deepEqual(academyEvents(page.dom), []);
});

test('pre-consent interactions are discarded and never replayed', () => {
  const page = academyPage('live', false);
  page.dom.window.eval(academyScript);
  const first = page.dom.window.document.querySelector('#first');

  page.notify([{ target: first, isIntersecting: true }]);
  assert.deepEqual(academyEvents(page.dom), []);

  page.setConsent(true);
  page.notify([{ target: first, isIntersecting: true }]);
  assert.deepEqual(academyEvents(page.dom), []);
});

test('funnel events are deduplicated and simultaneous headings use document order', () => {
  const page = academyPage('live', true);
  page.dom.window.eval(academyScript);
  const document = page.dom.window.document;
  const first = document.querySelector('#first');
  const last = document.querySelector('#last');

  page.notify([
    { target: last, isIntersecting: true },
    { target: first, isIntersecting: true },
  ]);
  page.notify([
    { target: first, isIntersecting: true },
    { target: last, isIntersecting: true },
  ]);

  assert.deepEqual(academyEvents(page.dom).map(item => item.event), [
    'tutorial_start',
    'tutorial_section',
    'tutorial_section',
    'tutorial_complete',
  ]);
  assert.deepEqual(
    academyEvents(page.dom).filter(item => item.event === 'tutorial_section').map(item => item.section_index),
    [1, 2]
  );
});

test('live click events use the contracted parameters', async () => {
  const page = academyPage('live', true);
  page.dom.window.eval(academyScript);
  const document = page.dom.window.document;
  page.notify([{ target: document.querySelector('#first'), isIntersecting: true }]);

  document.querySelector('.sdk').click();
  document.querySelector('.progression').click();
  document.querySelector('.academy-copy-btn').click();
  document.querySelector('[data-academy-share="twitter"]').click();
  await new Promise(resolve => page.dom.window.setTimeout(resolve, 0));

  const events = academyEvents(page.dom);
  assert.equal(events.find(item => item.event === 'sdk_clickout').sdk_url, 'https://github.com/Yubico/example');
  assert.equal(events.find(item => item.event === 'tutorial_progression').destination_tutorial, 'next-course');
  assert.equal(events.find(item => item.event === 'code_copy').code_language, 'java');
  assert.equal(events.find(item => item.event === 'tutorial_share').share_platform, 'twitter');
});

test('cancelled native sharing emits no share event', async () => {
  const page = academyPage('live', true);
  Object.defineProperty(page.dom.window.navigator, 'share', {
    value: () => Promise.reject(new page.dom.window.DOMException('cancelled', 'AbortError')),
    configurable: true,
  });
  page.dom.window.eval(academyScript);

  page.dom.window.document.querySelector('[data-academy-native-share]').click();
  await new Promise(resolve => page.dom.window.setTimeout(resolve, 0));

  assert.equal(academyEvents(page.dom).some(item => item.event === 'tutorial_share'), false);
});

test('Coming Soon pages bind only notify_me_click', () => {
  const page = academyPage('coming-soon', true);
  page.dom.window.eval(academyScript);
  const document = page.dom.window.document;

  assert.equal(page.observerCount(), 0);
  document.querySelector('.sdk').click();
  document.querySelector('.progression').click();
  document.querySelector('[data-academy-notify]').click();

  assert.deepEqual(JSON.parse(JSON.stringify(academyEvents(page.dom))), [{
    event: 'notify_me_click',
    tutorial_name: 'Build a Live Course',
    tutorial_slug: 'live-course',
  }]);
});
