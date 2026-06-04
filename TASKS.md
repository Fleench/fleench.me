# Migration Tasks

Track migration from the old `.html.temp` / `.element` block system to regular HTML / `.ghtml` chunks for `gen-ssg`.

Status key:
- `[ ]` Not started
- `[~]` In progress
- `[x]` Migrated

## Pages

Completed routes currently built in `dist`:

- [x] `/` from `src/index.md` -> `src/index.ghtml`
- [x] `/about/` from `src/about.md` -> `src/about.ghtml`
- [x] `/ai/` from `src/ai.md` -> `src/ai.ghtml`
- [x] `/blogs/` from `src/blogs.md` -> `src/blogs_all.ghtml`
- [x] `/blogs/2026/01/01/` from `src/blogs/2026/01/01.md` -> `src/blogs.ghtml`
- [x] `/blogs/2026/01/11/` from `src/blogs/2026/01/11.md` -> `src/blogs.ghtml`
- [x] `/blogs/test/` from `src/blogs/test.md` -> `src/blogs.ghtml`
- [x] `/changelog/` from `src/changelog.md` -> `src/changelog.ghtml`
- [x] `/do-not-link/now/` from `src/do-not-link/now.md` -> `src/do-not-link/now.ghtml`
- [x] `/guestbook/` from `src/guestbook.md` -> `src/guestbook.ghtml`
- [x] `/mobile/` from `src/mobile.md` -> `src/mobile.ghtml`
- [x] `/notes/` from `src/notes.md` -> `src/notes_all.ghtml`
- [x] `/notes/2026-02-17/1657/` from `src/notes/2026-02-17/1657.md` -> `src/notes.ghtml`
- [x] `/notes/2026-02-17/1703/` from `src/notes/2026-02-17/1703.md` -> `src/notes.ghtml`
- [x] `/notes/2026-02-17/1738/` from `src/notes/2026-02-17/1738.md` -> `src/notes.ghtml`
- [x] `/notes/2026-02-17/1801/` from `src/notes/2026-02-17/1801.md` -> `src/notes.ghtml`
- [x] `/notes/2026-02-17/2054/` from `src/notes/2026-02-17/2054.md` -> `src/notes.ghtml`
- [x] `/notes/2026-02-17/2125/` from `src/notes/2026-02-17/2125.md` -> `src/notes.ghtml`
- [x] `/notes/2026-02-18/0000/` from `src/notes/2026-02-18/0000.md` -> `src/notes.ghtml`
- [x] `/notes/2026-02-18/1504/` from `src/notes/2026-02-18/1504.md` -> `src/notes.ghtml`
- [x] `/notes/2026-02-19/1125/` from `src/notes/2026-02-19/1125.md` -> `src/notes.ghtml`
- [x] `/notes/2026-02-23/2250/` from `src/notes/2026-02-23/2250.md` -> `src/notes.ghtml`
- [x] `/notes/2026-02-24/1512/` from `src/notes/2026-02-24/1512.md` -> `src/notes.ghtml`
- [x] `/notes/2026-02-26/1555/` from `src/notes/2026-02-26/1555.md` -> `src/notes.ghtml`
- [x] `/notes/2026-03-05/2251/` from `src/notes/2026-03-05/2251.md` -> `src/notes.ghtml`
- [x] `/notes/2026-03-10/0125/` from `src/notes/2026-03-10/0125.md` -> `src/notes.ghtml`
- [x] `/notes/2026-03-10/2018/` from `src/notes/2026-03-10/2018.md` -> `src/notes.ghtml`
- [x] `/notes/2026-03-11/1246/` from `src/notes/2026-03-11/1246.md` -> `src/notes.ghtml`
- [x] `/notes/2026-03-24/2352/` from `src/notes/2026-03-24/2352.md` -> `src/notes.ghtml`
- [x] `/notes/2026-03-28/0336/` from `src/notes/2026-03-28/0336.md` -> `src/notes.ghtml`
- [x] `/notes/2026-03-31/1430/` from `src/notes/2026-03-31/1430.md` -> `src/notes.ghtml`
- [x] `/notes/2026-04-01/1354/` from `src/notes/2026-04-01/1354.md` -> `src/notes.ghtml`
- [x] `/test/` from `src/test.md` -> `src/test.ghtml`
- [x] `/test2/` from `src/test2.md` -> `src/test2.ghtml`
- [x] `/todo/` from `src/todo.md` -> `src/todo.ghtml`
- [x] `/year-review/` from `src/year-review.md` -> `src/year-review.ghtml`
- [~] `/404/` from `src/404.md` currently builds as `/404.html` via `src/404.ghtml`

Routes present in `legacy dist` but missing from current `dist`:

- [ ] `/404/` from `src/404.md`
- [ ] `/holtbot_updates/` from `src/holtbot_updates.md`
- [ ] `/mobile/about/` from `src/about.md`
- [ ] `/mobile/blogs/` from `src/blogs.md`
- [ ] `/mobile/blogs/2026/01/01/` from `src/blogs/2026/01/01.md`
- [ ] `/mobile/blogs/2026/01/11/` from `src/blogs/2026/01/11.md`
- [ ] `/mobile/blogs/test/` from `src/blogs/test.md`
- [ ] `/mobile/notes/` from `src/notes.md`
- [ ] `/mobile/notes/2026-02-17/1657/` from `src/notes/2026-02-17/1657.md`
- [ ] `/mobile/notes/2026-02-17/1703/` from `src/notes/2026-02-17/1703.md`
- [ ] `/mobile/notes/2026-02-17/1738/` from `src/notes/2026-02-17/1738.md`
- [ ] `/mobile/notes/2026-02-17/1801/` from `src/notes/2026-02-17/1801.md`
- [ ] `/mobile/notes/2026-02-17/2054/` from `src/notes/2026-02-17/2054.md`
- [ ] `/mobile/notes/2026-02-17/2125/` from `src/notes/2026-02-17/2125.md`
- [ ] `/mobile/notes/2026-02-18/0000/` from `src/notes/2026-02-18/0000.md`
- [ ] `/mobile/notes/2026-02-18/1504/` from `src/notes/2026-02-18/1504.md`
- [ ] `/mobile/notes/2026-02-19/1125/` from `src/notes/2026-02-19/1125.md`
- [ ] `/mobile/notes/2026-02-23/2250/` from `src/notes/2026-02-23/2250.md`
- [ ] `/mobile/notes/2026-02-24/1512/` from `src/notes/2026-02-24/1512.md`
- [ ] `/mobile/notes/2026-02-26/1555/` from `src/notes/2026-02-26/1555.md`
- [ ] `/mobile/notes/2026-03-05/2251/` from `src/notes/2026-03-05/2251.md`
- [ ] `/mobile/notes/2026-03-10/0125/` from `src/notes/2026-03-10/0125.md`
- [ ] `/mobile/notes/2026-03-10/2018/` from `src/notes/2026-03-10/2018.md`
- [ ] `/mobile/notes/2026-03-11/1246/` from `src/notes/2026-03-11/1246.md`
- [ ] `/mobile/notes/2026-03-24/2352/` from `src/notes/2026-03-24/2352.md`
- [ ] `/mobile/notes/2026-03-28/0336/` from `src/notes/2026-03-28/0336.md`
- [ ] `/mobile/notes/2026-03-31/1430/` from `src/notes/2026-03-31/1430.md`
- [ ] `/mobile/notes/2026-04-01/1354/` from `src/notes/2026-04-01/1354.md`
- [ ] `/mobile/year-review/25-26/` from `src/year-review/25-26.md`
- [ ] `/now/` from `src/now.md`
- [ ] `/plans/now/` from `src/plans/now.md`
- [ ] `/site-map/` from `src/site-map.md`
- [ ] `/year-review/25-26/` from `src/year-review/25-26.md`

## Templates

- [x] `src/templates/ai.html.temp` -> `src/templates/ai.html`
- [x] `src/templates/blog.html.temp` -> `src/templates/blog.html`
- [x] `src/templates/blogs-full.html.temp` -> `src/templates/blogs-full.html`
- [x] `src/templates/default.html.temp` -> `src/templates/default.html`
- [x] `src/templates/guestbook.html.temp` -> `src/templates/guestbook.html`
- [x] `src/templates/index.html.temp` -> `src/templates/index.html`
- [x] `src/templates/mobile-in.html.temp` -> `src/templates/mobile-in.html`
- [x] `src/templates/mobile.html.temp` -> `src/templates/mobile.html`
- [ ] `src/templates/mobile/mobile-blog-full.html.temp`
- [x] `src/templates/mobile/mobile-blog.html.temp` -> `src/templates/mobile/mobile-blog.html`
- [ ] `src/templates/mobile/mobile-note-full.html.temp`
- [x] `src/templates/mobile/mobile-note.html.temp` -> `src/templates/mobile/mobile-note.html`
- [ ] `src/templates/mobile/mobile-school-year-review.html.temp`
- [x] `src/templates/note-full.html.temp` -> `src/templates/note-full.html`
- [x] `src/templates/note.html.temp` -> `src/templates/note.html`
- [ ] `src/templates/now.html.temp`
- [x] `src/templates/page.html.temp` -> `src/templates/page.html`
- [x] `src/templates/replace.html.temp` -> `src/templates/replace.html`
- [x] `src/templates/reply.html.temp` -> `src/templates/reply.html`
- [ ] `src/templates/school-year-review.html.temp`
- [ ] `src/templates/site-map.html.temp`
- [x] `src/templates/test.html.temp` -> `src/templates/test.html`
- [x] `src/templates/year-review-redirect.html.temp` -> `src/templates/year-review-redirect.html`

## Elements

- [x] `src/elements/author.element` -> `src/elements/author.html`
- [x] `src/elements/blogs.py` -> `plugins/blogs.gplug`
- [x] `src/elements/built.py` -> `plugins/built.gplug`
- [x] `src/elements/footer.element` -> `src/elements/footer.html` + `plugins/footer.gplug`
- [x] `src/elements/head.element` -> `src/elements/head.html`
- [x] `src/elements/m-nav.element` -> `src/elements/m-nav.html`
- [x] `src/elements/map.py` -> `plugins/map.gplug`
- [x] `src/elements/marquee.element` -> `src/elements/marquee.html`
- [x] `src/elements/nav.element` -> `src/elements/nav.html`
- [x] `src/elements/notes.py` -> `plugins/notes.gplug`
- [x] `src/elements/rate.py` -> `plugins/rate.gplug`
- [x] `src/elements/spotify.py` -> `plugins/spotify.gplug`
- [x] `src/elements/test.py` -> `plugins/test.gplug`

## Migration Notes

- Replace old `~{block name}~...~{endblock}~` regions with normal placeholder elements using stable IDs.
- Use bare-ID `gHoist` targets for migrated chunks when the destination has a unique `id`.
- Keep dotted `gHoist` paths only where duplicate IDs/classes or structural targeting make that clearer.
- Convert static `.element` files to regular HTML fragments or GenHTML helper functions.
- Convert dynamic `.py` elements to `gen-ssg` plugin methods or page/helper functions.
