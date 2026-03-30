import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const script = fs.readFileSync(new URL('../src/theme-mode.js', import.meta.url), 'utf8');

class LocalStorageMock {
  constructor(initial = {}) {
    this.store = new Map(Object.entries(initial));
  }

  getItem(key) {
    return this.store.has(key) ? this.store.get(key) : null;
  }

  setItem(key, value) {
    this.store.set(key, String(value));
  }
}

class Element {
  constructor(tagName) {
    this.tagName = tagName.toUpperCase();
    this.attributes = new Map();
    this.rel = '';
    this.href = '';
  }

  setAttribute(name, value) {
    this.attributes.set(name, String(value));
    if (name === 'href') {
      this.href = String(value);
    }
  }

  getAttribute(name) {
    if (name === 'href') {
      return this.href;
    }
    return this.attributes.has(name) ? this.attributes.get(name) : null;
  }
}

class Anchor extends Element {
  constructor(href, attrs = {}) {
    super('a');
    this.href = href;
    Object.entries(attrs).forEach(([name, value]) => {
      this.setAttribute(name, value);
    });
  }
}

class DocumentMock {
  constructor({ title, anchors, readyState, hasDarkStylesheet }) {
    this.title = title;
    this.readyState = readyState;
    this.documentElement = new Element('html');
    this._anchors = anchors.map((anchor) => {
      if (typeof anchor === 'string') {
        return new Anchor(anchor);
      }
      return new Anchor(anchor.href, anchor.attrs || {});
    });
    this._listeners = new Map();
    this._darkLink = hasDarkStylesheet ? new Element('link') : null;

    this.head = {
      appended: [],
      appendChild: (node) => {
        this.head.appended.push(node);
        if (node.tagName === 'LINK' && node.getAttribute('data-theme-stylesheet') === 'dark') {
          this._darkLink = node;
        }
      },
    };
  }

  createElement(tagName) {
    return new Element(tagName);
  }

  querySelector(selector) {
    if (selector === 'link[data-theme-stylesheet="dark"]') {
      return this._darkLink;
    }
    return null;
  }

  querySelectorAll(selector) {
    if (selector === 'a[href]') {
      return this._anchors;
    }
    return [];
  }

  addEventListener(name, handler) {
    this._listeners.set(name, handler);
  }

  dispatch(name) {
    const handler = this._listeners.get(name);
    if (handler) {
      handler();
      this._listeners.delete(name);
    }
  }
}

function runThemeMode({
  search = '',
  pathname = '/here',
  hash = '',
  title = 'Page Title',
  savedMode,
  visits,
  readyState = 'complete',
  anchors = [],
  hasDarkStylesheet = false,
} = {}) {
  const initialStorage = {};
  if (savedMode !== undefined) {
    initialStorage['flench.themeMode'] = savedMode;
  }
  if (visits !== undefined) {
    initialStorage['flench.pageVisits'] = visits;
  }

  const localStorage = new LocalStorageMock(initialStorage);
  const document = new DocumentMock({ title, anchors, readyState, hasDarkStylesheet });

  const window = {
    location: {
      origin: 'https://fleench.me',
      pathname,
      search,
      hash,
      href: `https://fleench.me${pathname}${search}${hash}`,
    },
  };

  const context = {
    window,
    document,
    localStorage,
    URL,
    URLSearchParams,
    Date,
  };

  vm.runInNewContext(script, context, { filename: 'theme-mode.js' });

  return { document, localStorage };
}

test('defaults to dark mode and injects stylesheet', () => {
  const { document, localStorage } = runThemeMode();

  assert.equal(document.documentElement.getAttribute('data-mode'), 'dark');
  assert.equal(document.head.appended.length, 1);
  assert.equal(document.head.appended[0].href, '/dark.css');
  assert.equal(localStorage.getItem('flench.themeMode'), 'dark');
});

test('uses light mode from mode query parameter', () => {
  const modeResult = runThemeMode({ search: '?mode=light' });
  assert.equal(modeResult.document.documentElement.getAttribute('data-mode'), 'light');
  assert.equal(modeResult.document.head.appended.length, 0);
});

test('invalid mode query parameter falls back to dark default', () => {
  const { document, localStorage } = runThemeMode({ search: '?mode=sepia', savedMode: 'light' });
  assert.equal(document.documentElement.getAttribute('data-mode'), 'dark');
  assert.equal(localStorage.getItem('flench.themeMode'), 'dark');
});

test('keeps light mode in internal links and ignores non-navigational links', () => {
  const { document } = runThemeMode({
    search: '?mode=light',
    anchors: [
      '/post?x=1#section',
      'https://fleench.me/about?foo=bar',
      'https://example.com/',
      '#local',
      'mailto:test@example.com',
      'tel:+1555555',
    ],
  });

  const hrefs = document.querySelectorAll('a[href]').map((a) => a.getAttribute('href'));
  assert.equal(hrefs[0], '/post?x=1&mode=light#section');
  assert.equal(hrefs[1], 'https://fleench.me/about?foo=bar&mode=light');
  assert.equal(hrefs[2], 'https://example.com/');
  assert.equal(hrefs[3], '#local');
  assert.equal(hrefs[4], 'mailto:test@example.com');
  assert.equal(hrefs[5], 'tel:+1555555');
});

test('light mode removes theme query parameter to avoid conflict', () => {
  const { document } = runThemeMode({
    search: '?mode=light',
    anchors: ['/article?theme=dark&x=1'],
  });

  assert.equal(document.querySelectorAll('a[href]')[0].getAttribute('href'), '/article?x=1&mode=light');
});

test('dark mode strips mode and theme query parameters from internal links', () => {
  const { document } = runThemeMode({
    search: '?mode=dark',
    anchors: ['/article?mode=light&theme=light&x=1'],
  });

  assert.equal(document.querySelectorAll('a[href]')[0].getAttribute('href'), '/article?x=1');
});

test('defers link rewriting until DOMContentLoaded when document is loading', () => {
  const { document } = runThemeMode({
    search: '?mode=light',
    readyState: 'loading',
    anchors: ['/article'],
  });

  assert.equal(document.querySelectorAll('a[href]')[0].getAttribute('href'), '/article');
  document.dispatch('DOMContentLoaded');
  assert.equal(document.querySelectorAll('a[href]')[0].getAttribute('href'), '/article?mode=light');
});

test('tracks visits and keeps only the last 200 records', () => {
  const priorVisits = Array.from({ length: 200 }, (_, i) => ({
    url: `/old-${i}`,
    title: `Old ${i}`,
    visitedAt: '2000-01-01T00:00:00.000Z',
  }));

  const { localStorage } = runThemeMode({
    pathname: '/new',
    search: '?q=1',
    hash: '#hash',
    title: 'New Title',
    visits: JSON.stringify(priorVisits),
  });

  const stored = JSON.parse(localStorage.getItem('flench.pageVisits'));
  assert.equal(stored.length, 200);
  assert.equal(stored[0].url, '/old-1');
  assert.equal(stored[199].url, '/new?q=1#hash');
  assert.equal(stored[199].title, 'New Title');
});

test('handles malformed visit history storage', () => {
  const { localStorage } = runThemeMode({ visits: 'not-json' });
  const stored = JSON.parse(localStorage.getItem('flench.pageVisits'));
  assert.equal(stored.length, 1);
});

test('does not duplicate dark stylesheet when one already exists', () => {
  const { document } = runThemeMode({ hasDarkStylesheet: true });
  assert.equal(document.head.appended.length, 0);
});
