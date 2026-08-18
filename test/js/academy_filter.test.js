const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const { JSDOM } = require('jsdom');

const academyScript = fs.readFileSync(
  path.resolve(__dirname, '../../static/js/academy.js'),
  'utf8'
);

test('technology filters show matching tutorials and All restores every card', () => {
  const dom = new JSDOM(`
    <button data-academy-filter="all" aria-pressed="true">All</button>
    <button data-academy-filter="WebAuthn" aria-pressed="false">WebAuthn</button>
    <button data-academy-filter="FIPS" aria-pressed="false">FIPS</button>
    <article data-academy-card data-tutorial-tags="WebAuthn">
      <button data-academy-filter="WebAuthn" aria-pressed="false">WebAuthn</button>
    </article>
    <article data-academy-card data-tutorial-tags="FIPS|PIV"></article>
    <p data-academy-filter-empty hidden>No tutorials match.</p>
  `, { runScripts: 'outside-only', url: 'https://developers.yubico.com/Academy/' });

  dom.window.eval(academyScript);

  const filters = dom.window.document.querySelectorAll('[data-academy-filter]');
  const cards = dom.window.document.querySelectorAll('[data-academy-card]');
  const startedAt = performance.now();
  filters[1].click();
  assert.ok(performance.now() - startedAt < 100);
  assert.equal(cards[0].hidden, false);
  assert.equal(cards[1].hidden, true);
  assert.equal(filters[1].getAttribute('aria-pressed'), 'true');
  assert.equal(filters[3].getAttribute('aria-pressed'), 'true');
  assert.equal(filters[0].getAttribute('aria-pressed'), 'false');

  filters[3].click();
  assert.equal(cards[0].hidden, false);
  assert.equal(cards[1].hidden, true);
  assert.equal(filters[1].getAttribute('aria-pressed'), 'true');
  assert.equal(filters[3].getAttribute('aria-pressed'), 'true');

  filters[0].click();
  assert.equal(cards[0].hidden, false);
  assert.equal(cards[1].hidden, false);
});
