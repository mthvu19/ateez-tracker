/* ATEEZ Tracker – front-end (doc du lieu tu data/*.json do GitHub Actions cap nhat) */
(function () {
  'use strict';

  var CATS = {
    schedule: { label: 'Schedule', bg: '#E6EDFF', fg: '#1F3FB0' },
    release: { label: 'Release', bg: '#EDE7FF', fg: '#5A2DB8' },
    tour: { label: 'Concert/Tour', bg: '#FFE9DA', fg: '#9A4310' },
    merch: { label: 'Album/Merch', bg: '#E3F4EC', fg: '#1C6B47' },
    charts: { label: 'Charts & Records', bg: '#FFF4CC', fg: '#7A5A00' },
    sns: { label: 'SNS', bg: '#FCE7F3', fg: '#9D174D' },
    video: { label: 'Video', bg: '#E2F3F7', fg: '#17606F' },
    press: { label: 'Press', bg: '#EEF0F3', fg: '#3D4656' },
    official: { label: 'Official Announcement', bg: '#ECECEC', fg: '#3D3F46' },
    funfact: { label: 'Fun Facts', bg: '#FBF0D2', fg: '#7A5A00' }
  };
  var CAT_ORDER = ['schedule', 'release', 'tour', 'merch', 'charts', 'sns', 'video', 'press', 'official', 'funfact'];
  var MEMBERS = ['Hongjoong', 'Seonghwa', 'Yunho', 'Yeosang', 'San', 'Mingi', 'Wooyoung', 'Jongho'];
  var TIER = { official: 'Official', fan: 'Fan update', news: 'Press' };
  var WD = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  var DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var KST = 9 * 3600e3, VN = 7 * 3600e3, DAY = 86400e3;

  var ICONS = {
    today: '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    news: '<path d="M4 6h16M4 12h16M4 18h10"/>',
    photos: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 17l-5-5-9 7"/>',
    funfacts: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9V16h7v-2.1A6 6 0 0 0 12 3z"/>',
    saved: '<path d="M6 3h12v18l-6-4-6 4z"/>'
  };
  var VIEWS = [['today', 'Today'], ['calendar', 'Calendar'], ['news', 'All News'], ['photos', 'Photos'], ['funfacts', 'Fun Facts'], ['saved', 'Saved']];

  var S = {
    items: [], events: [], facts: [], meta: {},
    cat: 'all', member: null, q: '', limit: 40,
    calMonth: null, calDay: null,
    saved: loadSaved()
  };

  // ---------- helpers ----------
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function safeUrl(u) { return /^https?:\/\//i.test(u || '') ? u : '#'; }
  function icon(name, size) {
    return '<svg width="' + (size || 18) + '" height="' + (size || 18) + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + ICONS[name] + '</svg>';
  }
  function t(s) { return s ? new Date(s).getTime() : NaN; }
  function shift(ms, off) { return new Date(ms + off); } // dung getUTC* tren ket qua
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function hm(ms, off) { var d = shift(ms, off); return pad(d.getUTCHours()) + ':' + pad(d.getUTCMinutes()); }
  function dm(ms, off) { var d = shift(ms, off); return d.getUTCDate() + '/' + (d.getUTCMonth() + 1); }
  function dayKey(ms, off) { var d = shift(ms, off); return d.getUTCFullYear() + '-' + pad(d.getUTCMonth() + 1) + '-' + pad(d.getUTCDate()); }
  function dayLabel(key) {
    var p = key.split('-'), d = new Date(Date.UTC(+p[0], +p[1] - 1, +p[2]));
    var today = dayKey(Date.now(), VN), yest = dayKey(Date.now() - DAY, VN);
    var base = DOW[d.getUTCDay()] + ' ' + (+p[2]) + '/' + (+p[1]);
    if (key === today) return 'Today · ' + base;
    if (key === yest) return 'Yesterday · ' + base;
    return base + (+p[0] !== new Date().getFullYear() ? '/' + p[0] : '');
  }
  function ago(ms) {
    var m = Math.round((Date.now() - ms) / 60000);
    if (m < 1) return 'just now';
    if (m < 60) return m + ' min ago';
    var h = Math.round(m / 60);
    if (h < 48) return h + 'h ago';
    return Math.round(h / 24) + ' days ago';
  }
  function dday(ms) {
    var a = Date.parse(dayKey(ms, KST)), b = Date.parse(dayKey(Date.now(), KST));
    var n = Math.round((a - b) / DAY);
    return n <= 0 ? 'D-DAY' : 'D-' + n;
  }
  function loadSaved() { try { return JSON.parse(localStorage.getItem('ateez-saved') || '{}'); } catch (e) { return {}; } }
  function persistSaved() { try { localStorage.setItem('ateez-saved', JSON.stringify(S.saved)); } catch (e) { /* bo qua */ } }
  function title(it) { return it.title_vi || it.title; }
  function summary(it) {
    if (it.summary_vi) return it.summary_vi;
    var txt = (it.text || '').replace(/^(안녕하세요\.?|Hello[.,]?)\s*/i, '').replace(/^(KQ\s*엔터테인먼트입니다\.?|This is KQ Entertainment\.?)\s*/i, '');
    if (txt.indexOf(it.title) === 0) txt = txt.slice(it.title.length);
    txt = txt.trim();
    return txt.length > 260 ? txt.slice(0, 259) + '…' : txt;
  }
  function matches(it) {
    if (S.member && (it.members || []).indexOf(S.member) < 0) return false;
    if (S.q) {
      var hay = (title(it) + ' ' + it.title + ' ' + (it.summary_vi || '') + ' ' + (it.text || '') + ' ' + (it.members || []).join(' ')).toLowerCase();
      if (hay.indexOf(S.q) < 0) return false;
    }
    return true;
  }
  function eventMatches(e) {
    if (S.member && e.members && e.members.length && e.members.indexOf(S.member) < 0) return false;
    if (S.q && (e.label + ' ' + e.title).toLowerCase().indexOf(S.q) < 0) return false;
    return true;
  }
  function deadlineOf(e) { return t(e.end) || t(e.start); }

  // ---------- pieces ----------
  function catChip(c) {
    var x = CATS[c] || CATS.official;
    return '<span class="cat" style="background:' + x.bg + ';color:' + x.fg + '">' + esc(x.label) + '</span>';
  }
  function card(it) {
    var ms = t(it.published), saved = !!S.saved[it.id];
    var mems = (it.members || []).map(function (m) { return '<span class="mem">' + esc(m) + '</span>'; }).join('');
    var imgs = (it.images || []).slice(0, 4).map(function (u) {
      return '<a href="' + esc(safeUrl(it.url)) + '" target="_blank" rel="noopener"><img loading="lazy" src="' + esc(safeUrl(u)) + '" alt=""></a>';
    }).join('');
    var sum = summary(it);
    return '<article class="card">' +
      '<div class="time"><b>' + (isNaN(ms) ? '—' : hm(ms, KST)) + '</b><span>KST · ' + (isNaN(ms) ? '' : hm(ms, VN) + ' VN') + '</span></div>' +
      '<div class="body">' +
      '<div class="tags">' + catChip(it.category) + mems + '<span class="tier ' + esc(it.tier) + '">' + esc(TIER[it.tier] || it.tier) + '</span></div>' +
      '<h3>' + esc(title(it)) + '</h3>' +
      (it.title_vi && it.title_vi !== it.title ? '<p style="font-size:12px;color:var(--muted)">' + esc(it.title) + '</p>' : '') +
      (sum ? '<p>' + esc(sum) + '</p>' : '') +
      (imgs ? '<div class="thumbs">' + imgs + '</div>' : '') +
      '<div class="actions"><a href="' + esc(safeUrl(it.url)) + '" target="_blank" rel="noopener">Open original ↗</a>' +
      '<button type="button" class="save" data-save="' + esc(it.id) + '" aria-pressed="' + saved + '">' + icon('saved', 15) + (saved ? 'Saved' : 'Save') + '</button></div>' +
      '</div></article>';
  }
  function feed(list, withFilters, heading) {
    var counts = {};
    list.forEach(function (it) { counts[it.category] = (counts[it.category] || 0) + 1; });
    var shown = S.cat === 'all' ? list : list.filter(function (it) { return it.category === S.cat; });
    var html = '<section class="sec" aria-labelledby="feedT"><div class="sec-head"><h2 id="feedT">' + heading + '</h2>';
    if (withFilters) {
      html += '<div class="chips" role="group" aria-label="Filter by category">' +
        '<button type="button" class="chip-btn" data-cat="all" aria-pressed="' + (S.cat === 'all') + '">All<span class="c">' + list.length + '</span></button>' +
        CAT_ORDER.filter(function (c) { return counts[c] || S.cat === c; }).map(function (c) {
          return '<button type="button" class="chip-btn" data-cat="' + c + '" aria-pressed="' + (S.cat === c) + '">' + esc(CATS[c].label) + '<span class="c">' + (counts[c] || 0) + '</span></button>';
        }).join('') + '</div>';
    }
    html += '</div>';
    if (!shown.length) return html + '<div class="empty">Chưa có tin nào trong mục này.</div></section>';
    var groups = [], idx = {};
    shown.slice(0, S.limit).forEach(function (it) {
      var k = dayKey(t(it.published), VN);
      if (!idx[k]) { idx[k] = { key: k, items: [] }; groups.push(idx[k]); }
      idx[k].items.push(it);
    });
    groups.forEach(function (g) {
      html += '<div class="day"><span class="eyebrow">' + esc(dayLabel(g.key)) + '</span>' + g.items.map(card).join('') + '</div>';
    });
    if (shown.length > S.limit) html += '<button type="button" class="more" data-more="1">Load more (' + (shown.length - S.limit) + ')</button>';
    return html + '</section>';
  }
  function highlightList() {
    var now = Date.now(), horizon = now + (S.meta.highlight_days || 30) * DAY;
    return S.events.filter(function (e) {
      var d = deadlineOf(e);
      return d >= now && t(e.start) <= horizon && eventMatches(e);
    }).sort(function (a, b) { return deadlineOf(a) - deadlineOf(b); });
  }
  function highlight() {
    var list = highlightList().slice(0, 8);
    var html = '<section class="sec" aria-labelledby="hlT"><div class="sec-head"><h2 id="hlT">Highlight</h2><span class="note">KST · VN = KST − 2h</span></div>';
    if (!list.length) return html + '<div class="empty">Không có mốc nào trong 30 ngày tới.</div></section>';
    html += '<div class="hl-grid">' + list.map(function (e) {
      var d = deadlineOf(e), urgent = d - Date.now() < 2 * DAY;
      var startMs = t(e.start), endMs = t(e.end);
      var when = e.end ? (startMs > Date.now() ? dm(startMs, KST) + ' ' + hm(startMs, KST) + ' → ' : 'Hạn ') + dm(endMs, KST) + ' · ' + hm(endMs, KST) + ' KST'
        : dm(startMs, KST) + (e.has_time === false ? '' : ' · ' + hm(startMs, KST) + ' KST (' + hm(startMs, VN) + ' VN)');
      return '<a class="hl' + (urgent ? ' urgent' : '') + '" href="' + esc(safeUrl(e.url)) + '" target="_blank" rel="noopener">' +
        '<span class="dday">' + dday(d) + '</span><span class="t">' + esc(e.label) + '</span>' +
        '<span class="w">' + esc(when) + '</span><span class="n">' + esc(e.title) + '</span></a>';
    }).join('') + '</div></section>';
    return html;
  }
  function photoItems() {
    var out = [];
    S.items.forEach(function (it) {
      if (it.source === 'youtube' || it.category === 'charts' || !matches(it)) return;
      (it.images || []).forEach(function (u) { out.push({ u: u, it: it }); });
    });
    return out;
  }
  function photoGrid(list) {
    return '<div class="ph-grid">' + list.map(function (p) {
      var ms = t(p.it.published);
      return '<a class="ph" href="' + esc(safeUrl(p.it.url)) + '" target="_blank" rel="noopener"><img loading="lazy" src="' + esc(safeUrl(p.u)) + '" alt="">' +
        '<span class="m">' + esc((p.it.members || []).join(', ') || 'ATEEZ') + '</span><span class="s">' + esc(TIER[p.it.tier] || '') + ' · ' + (isNaN(ms) ? '' : dm(ms, VN) + ' ' + hm(ms, VN)) + '</span></a>';
    }).join('') + '</div>';
  }
  function photosSection(n) {
    var list = photoItems();
    if (!list.length) return '';
    return '<section class="sec" aria-labelledby="phT"><div class="sec-head"><h2 id="phT">Photos</h2><a href="#photos">See all ›</a></div>' + photoGrid(list.slice(0, n)) + '</section>';
  }
  function factItems() {
    var auto = S.items.filter(function (it) { return it.category === 'funfact' && matches(it); }).map(function (it) {
      return { kind: 'Fan update', text: summary(it) || title(it), meta: (it.members || []).join(', '), url: it.url, date: it.published };
    });
    var manual = S.facts.filter(function (f) { return !S.member || (f.members || []).indexOf(S.member) >= 0; });
    return manual.concat(auto);
  }
  function factCard(f) {
    return '<a class="ff" href="' + esc(safeUrl(f.url)) + '" target="_blank" rel="noopener"><span class="k">' + esc(f.kind || 'Fun Fact') + '</span>' +
      '<span class="x">' + esc(f.text) + '</span>' + (f.meta ? '<span class="meta">' + esc(f.meta) + '</span>' : '') + '</a>';
  }

  // ---------- aside ----------
  function monthEvents(y, m) {
    var map = {};
    S.events.forEach(function (e) {
      if (!eventMatches(e)) return;
      [e.start, e.end].forEach(function (s) {
        if (!s) return;
        var k = dayKey(t(s), KST), p = k.split('-');
        if (+p[0] === y && +p[1] === m + 1) { (map[+p[2]] = map[+p[2]] || []).push(e); }
      });
    });
    return map;
  }
  function curMonth() {
    if (!S.calMonth) { var d = shift(Date.now(), KST); S.calMonth = [d.getUTCFullYear(), d.getUTCMonth()]; }
    return S.calMonth;
  }
  function miniCal() {
    var ym = curMonth(), y = ym[0], m = ym[1], map = monthEvents(y, m);
    var first = new Date(Date.UTC(y, m, 1)).getUTCDay(), off = (first + 6) % 7, days = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
    var todayK = dayKey(Date.now(), KST);
    var cells = WD.map(function (w) { return '<span class="wd">' + w + '</span>'; }).join('');
    for (var i = 0; i < off; i++) cells += '<span></span>';
    for (var d = 1; d <= days; d++) {
      var k = y + '-' + pad(m + 1) + '-' + pad(d), has = !!map[d];
      cells += '<button type="button" data-day="' + k + '" class="' + (has ? 'has ' : '') + (k === todayK ? 'today' : '') + '" aria-label="' + d + ' ' + MONTHS[m] + (has ? ', ' + map[d].length + ' events' : '') + '">' + d + '<i></i></button>';
    }
    return '<section class="box" aria-labelledby="calT"><div class="box-head"><h2 id="calT">' + MONTHS[m] + ' ' + y + '</h2><div>' +
      '<button type="button" class="navbtn" data-mon="-1" aria-label="Previous month">‹</button> <button type="button" class="navbtn" data-mon="1" aria-label="Next month">›</button></div></div>' +
      '<div class="cal">' + cells + '</div></section>';
  }
  function upcoming() {
    var now = Date.now();
    var list = S.events.filter(function (e) { return t(e.start) >= now && eventMatches(e); }).slice(0, 8);
    var html = '<section class="box" aria-labelledby="upT"><h2 id="upT">Upcoming</h2>';
    if (!list.length) return html + '<span class="status">Chưa có mốc nào sắp tới.</span></section>';
    return html + list.map(function (e) {
      var ms = t(e.start);
      return '<a class="up" href="' + esc(safeUrl(e.url)) + '" target="_blank" rel="noopener"><b>' + dm(ms, KST) + '</b><span><span class="a">' + esc(e.label) + '</span><span class="b">' + esc(e.title) + (e.has_time === false ? '' : ' · ' + hm(ms, KST) + ' KST') + '</span></span></a>';
    }).join('') + '</section>';
  }
  function factsBox() {
    var list = factItems().slice(0, 3);
    var html = '<section class="box" aria-labelledby="ffT"><div class="box-head"><h2 id="ffT">Fun Facts</h2><a href="#funfacts" style="font-size:13px;font-weight:600;text-decoration:none">More ›</a></div>';
    if (!list.length) return html + '<span class="status">Thêm fun fact vào <code>docs/data/funfacts.json</code> hoặc chờ fan account đăng throwback/TMI.</span></section>';
    return html + list.map(factCard).join('') + '</section>';
  }
  function statusBox() {
    var src = S.meta.sources || {}, names = { kq: 'KQ Web', youtube: 'YouTube', news: 'Báo', x: 'X' };
    var rows = Object.keys(names).filter(function (k) { return src[k]; }).map(function (k) {
      var s = src[k];
      return '<span class="' + (s.ok ? '' : 'bad') + '">' + names[k] + ': ' + (s.ok ? 'OK · ' + ago(t(s.at)) : 'lỗi · ' + esc(s.error || '')) + '</span>';
    }).join('');
    return rows ? '<section class="box"><h2>Sources</h2><div class="status">' + rows + '</div></section>' : '';
  }
  function renderAside(view) {
    var a = document.getElementById('aside');
    a.innerHTML = view === 'today' ? miniCal() + upcoming() + factsBox() + statusBox() : '';
  }

  // ---------- views ----------
  function viewToday() {
    var list = S.items.filter(matches);
    return highlight() + photosSection(6) + feed(list, true, 'News');
  }
  function viewNews() { return feed(S.items.filter(matches), true, 'All News'); }
  function viewPhotos() {
    var list = photoItems();
    return '<section class="sec"><div class="sec-head"><h2>Photos</h2><span class="note">' + list.length + ' ảnh</span></div>' +
      (list.length ? photoGrid(list.slice(0, 120)) : '<div class="empty">Chưa có ảnh.</div>') + '</section>';
  }
  function viewFacts() {
    var list = factItems();
    return '<section class="sec"><div class="sec-head"><h2>Fun Facts</h2></div>' +
      (list.length ? '<div class="hl-grid">' + list.map(factCard).join('') + '</div>' : '<div class="empty">Chưa có fun fact. Thêm vào <code>docs/data/funfacts.json</code>.</div>') + '</section>';
  }
  function viewSaved() {
    var list = S.items.filter(function (it) { return S.saved[it.id]; });
    return list.length ? feed(list, false, 'Saved') : '<section class="sec"><div class="sec-head"><h2>Saved</h2></div><div class="empty">Bấm “Save” trên một tin để lưu lại ở đây (lưu trên trình duyệt này).</div></section>';
  }
  function viewCalendar() {
    var ym = curMonth(), y = ym[0], m = ym[1], map = monthEvents(y, m);
    var first = new Date(Date.UTC(y, m, 1)).getUTCDay(), off = (first + 6) % 7, days = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
    var todayK = dayKey(Date.now(), KST);
    if (!S.calDay || S.calDay.slice(0, 7) !== y + '-' + pad(m + 1)) {
      S.calDay = todayK.slice(0, 7) === y + '-' + pad(m + 1) ? todayK : y + '-' + pad(m + 1) + '-01';
    }
    var cells = WD.map(function (w) { return '<span class="wd">' + w + '</span>'; }).join('');
    for (var i = 0; i < off; i++) cells += '<span class="d off"></span>';
    for (var d = 1; d <= days; d++) {
      var k = y + '-' + pad(m + 1) + '-' + pad(d), evs = map[d] || [];
      cells += '<button type="button" class="d' + (k === todayK ? ' today' : '') + (k === S.calDay ? ' sel' : '') + '" data-day="' + k + '" aria-label="' + d + ' ' + MONTHS[m] + ', ' + evs.length + ' events"><span class="n">' + d + '</span>' +
        evs.slice(0, 3).map(function (e) { return '<span class="ev">' + esc(e.label) + '</span>'; }).join('') +
        (evs.length > 3 ? '<span class="ev">+' + (evs.length - 3) + '</span>' : '') + '</button>';
    }
    var sel = S.calDay.split('-'), selEvents = (map[+sel[2]] || []).slice().sort(function (a, b) { return t(a.start) - t(b.start); });
    var list = selEvents.length ? selEvents.map(function (e) {
      var isEnd = e.end && dayKey(t(e.end), KST) === S.calDay && dayKey(t(e.start), KST) !== S.calDay;
      var ms = isEnd ? t(e.end) : t(e.start);
      return '<a class="evcard" href="' + esc(safeUrl(e.url)) + '" target="_blank" rel="noopener" style="text-decoration:none;color:inherit"><div class="tm"><b>' + (e.has_time === false && !isEnd ? 'All day' : hm(ms, KST)) + '</b><span>' + (e.has_time === false && !isEnd ? '' : 'KST · ' + hm(ms, VN) + ' VN') + '</span></div>' +
        '<div class="info">' + catChip(e.category) + '<span class="l">' + (isEnd ? 'Hết hạn: ' : '') + esc(e.label) + '</span><span class="s">' + esc(e.title) + '</span></div></a>';
    }).join('') : '<div class="empty">Không có mốc nào trong ngày này.</div>';
    return '<section class="sec"><div class="sec-head"><h2>' + MONTHS[m] + ' ' + y + '</h2><div>' +
      '<button type="button" class="navbtn" data-mon="-1" aria-label="Previous month">‹</button> <button type="button" class="navbtn" data-mon="1" aria-label="Next month">›</button></div></div>' +
      '<div class="bigcal">' + cells + '</div></section>' +
      '<section class="sec"><div class="sec-head"><h2 style="font-size:18px">' + esc(dayLabel(S.calDay)) + '</h2></div><div class="daylist">' + list + '</div></section>';
  }

  function currentView() {
    var h = (location.hash || '#today').slice(1);
    return VIEWS.some(function (v) { return v[0] === h; }) ? h : 'today';
  }
  function render() {
    var view = currentView();
    var main = document.getElementById('main');
    main.className = 'main' + (view === 'today' ? '' : ' wide');
    main.innerHTML = { today: viewToday, calendar: viewCalendar, news: viewNews, photos: viewPhotos, funfacts: viewFacts, saved: viewSaved }[view]();
    renderAside(view);
    var navHtml = function (short) {
      return VIEWS.filter(function (v) { return !short || v[0] !== 'news'; }).map(function (v) {
        return '<a href="#' + v[0] + '"' + (v[0] === view ? ' aria-current="page"' : '') + '>' + icon(v[0], short ? 22 : 18) + v[1] + '</a>';
      }).join('');
    };
    document.getElementById('menu').innerHTML = navHtml(false);
    document.getElementById('bottomNav').innerHTML = navHtml(true);
    document.getElementById('memberPills').innerHTML = MEMBERS.map(function (m) {
      return '<button type="button" class="pill" data-member="' + m + '" aria-pressed="' + (S.member === m) + '">' + m + '</button>';
    }).join('');
  }

  // ---------- events ----------
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-cat],[data-member],[data-more],[data-save],[data-mon],[data-day]');
    if (!b) return;
    if (b.dataset.cat) { S.cat = b.dataset.cat; S.limit = 40; }
    else if (b.dataset.member) { S.member = S.member === b.dataset.member ? null : b.dataset.member; }
    else if (b.dataset.more) { S.limit += 40; }
    else if (b.dataset.save) {
      if (S.saved[b.dataset.save]) delete S.saved[b.dataset.save]; else S.saved[b.dataset.save] = Date.now();
      persistSaved();
    } else if (b.dataset.mon) {
      var ym = curMonth(), m = ym[1] + (+b.dataset.mon);
      S.calMonth = [ym[0] + Math.floor(m / 12), (m + 12) % 12];
    } else if (b.dataset.day) {
      S.calDay = b.dataset.day;
      var p = b.dataset.day.split('-'); S.calMonth = [+p[0], +p[1] - 1];
      if (currentView() !== 'calendar') { location.hash = '#calendar'; return; }
    }
    render();
  });
  var timer;
  document.getElementById('search').addEventListener('input', function (e) {
    clearTimeout(timer);
    timer = setTimeout(function () {
      S.q = e.target.value.trim().toLowerCase(); S.limit = 40;
      if (S.q && ['today', 'news'].indexOf(currentView()) < 0) location.hash = '#news'; else render();
    }, 200);
  });
  window.addEventListener('hashchange', function () { render(); window.scrollTo(0, 0); });

  // ---------- load ----------
  function getJSON(path, fallback) {
    return fetch(path + '?t=' + Date.now(), { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : fallback; }).catch(function () { return fallback; });
  }
  function load() {
    return Promise.all([
      getJSON('data/items.json', { items: [] }), getJSON('data/events.json', { events: [] }),
      getJSON('data/meta.json', {}), getJSON('data/funfacts.json', { facts: [] })
    ]).then(function (r) {
      S.items = r[0].items || []; S.events = r[1].events || []; S.meta = r[2] || {}; S.facts = r[3].facts || [];
      var up = t(S.meta.updated || r[0].updated);
      document.getElementById('updatedText').textContent = isNaN(up) ? 'Chưa có dữ liệu' : 'Updated ' + ago(up);
      document.getElementById('updated').classList.toggle('stale', isNaN(up) || Date.now() - up > 3 * 3600e3);
      render();
    });
  }
  var d = shift(Date.now(), VN);
  document.getElementById('todayDate').textContent = DOW[d.getUTCDay()] + ', ' + d.getUTCDate() + ' ' + MONTHS[d.getUTCMonth()].slice(0, 3) + ' ' + d.getUTCFullYear();
  load();
  setInterval(load, 10 * 60e3);
})();
