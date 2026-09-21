#!/usr/bin/env python3
"""
AI Daily News - HTML generator
Renders data/categorized_news.json into the daily report (index.html),
archives the previous report and refreshes data/archive_manifest.json.
"""

import glob
import json
import os
import re
from datetime import datetime

from bs4 import BeautifulSoup
from jinja2 import Template

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_FILE = os.path.join(PROJECT_DIR, "index.html")
ARCHIVE_DIR = os.path.join(PROJECT_DIR, "archive")
DATA_DIR = os.path.join(PROJECT_DIR, "data")

# Bump when assets/style.css changes so browsers and the service worker fetch the new file
STYLE_VERSION = "3"

# Issue numbers count days since the first English/Vietnamese issue (Số 1)
ISSUE_START_DATE = datetime(2026, 9, 21)

# Non-headline sections, in display order: (category key, English title, Vietnamese title)
SECTIONS = [
    ("product", "Products", "Sản phẩm mới"),
    ("funding", "Funding & M&A", "Gọi vốn & M&A"),
    ("research", "Research", "Nghiên cứu"),
    ("industry", "Industry & Policy", "Thị trường & Chính sách"),
    ("other", "More News", "Tin khác"),
]

# HTML template - newspaper style, bilingual (English by default, Vietnamese on demand).
# Every visible string is rendered in both languages; CSS shows the active one.
HTML_TEMPLATE = """{%- macro t(en, vi) -%}
<span class="i18n-en" lang="en">{{ en }}</span><span class="i18n-vi" lang="vi">{{ vi }}</span>
{%- endmacro -%}
{%- macro title(item) -%}
{{ t(item.title_en or item.title, item.title_vi or item.title) }}
{%- endmacro -%}
<!DOCTYPE html>
<html lang="en" data-lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>AI Daily News | {{ date_str }}</title>
  <meta name="report-date" content="{{ date_str }}">
  <meta name="description" content="Daily AI news and technology report - Bản tin AI mỗi ngày.">
  <meta name="theme-color" content="#1a1a1a">
  <!-- Apply the saved language before first paint to avoid a flash of the wrong language -->
  <script>
    (function () {
      var lang = "en";
      try { if (localStorage.getItem("aidaily-lang") === "vi") lang = "vi"; } catch (e) {}
      document.documentElement.setAttribute("data-lang", lang);
      document.documentElement.lang = lang;
    })();
  </script>
  <link rel="manifest" href="manifest.webmanifest">
  <link rel="stylesheet" href="assets/style.css?v={{ style_version }}">
  <!-- Icons / PWA -->
  <link rel="icon" type="image/svg+xml" href="icons/icon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png">
  <link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="default">
  <meta name="apple-mobile-web-app-title" content="AI Daily">
</head>
<body>
  <main id="reportStage">
  <div class="container">
    <!-- Masthead -->
    <header class="header">
      <div class="lang-switch" role="group" aria-label="Language / Ngôn ngữ">
        <button type="button" data-set-lang="en" title="English">EN</button>
        <button type="button" data-set-lang="vi" title="Tiếng Việt">VI</button>
      </div>
      <div class="header-top">
        <div class="header-left">{{ t("No. " ~ issue_num, "Số " ~ issue_num) }}</div>
        <div class="header-center">{{ t("AI · ARTIFICIAL INTELLIGENCE · TECHNOLOGY", "AI · TRÍ TUỆ NHÂN TẠO · CÔNG NGHỆ") }}</div>
        <div class="header-right">{{ t(date_en, date_vi) }}</div>
      </div>
      <h1>AI DAILY NEWS</h1>
      <div class="header-bottom">{{ t("DAILY AI NEWS & TECHNOLOGY REPORT", "BẢN TIN AI & CÔNG NGHỆ MỖI NGÀY") }}</div>
    </header>

    {% if categories.headline %}
    <!-- Main headline -->
    <article class="main-headline">
      <div class="headline-tag">◆ {{ t("HEADLINE", "TIN NỔI BẬT") }} ◆</div>
      <h2 class="headline-title"><a href="{{ categories.headline[0].link }}" target="_blank" rel="noopener">{{ title(categories.headline[0]) }}</a></h2>
      <div class="headline-meta">
        <span class="headline-source">{{ categories.headline[0].source }}</span>
        <span>{{ categories.headline[0].pub_date.split(' ')[1] }}</span>
      </div>
    </article>

    {% if categories.headline|length > 1 %}
    <!-- Sub headlines -->
    <div class="sub-headlines">
      {% for item in categories.headline[1:3] %}
      <div class="sub-headline-item">
        <div class="news-title"><a href="{{ item.link }}" target="_blank" rel="noopener">{{ title(item) }}</a></div>
        <div class="news-meta"><span class="news-source">{{ item.source }}</span> | {{ item.pub_date.split(' ')[1] }}</div>
      </div>
      {% endfor %}
    </div>
    {% endif %}
    {% endif %}

    <div class="divider"></div>

    {% for key, title_en, title_vi in sections %}
    {% if categories[key] %}
    <section class="section">
      <h3 class="section-title">{{ t(title_en, title_vi) }}</h3>
      <div class="news-grid">
        {% for item in categories[key] %}
        <div class="news-item">
          <div class="news-title"><a href="{{ item.link }}" target="_blank" rel="noopener">{{ title(item) }}</a></div>
          <div class="news-meta"><span class="news-source">{{ item.source }}</span> | {{ item.pub_date.split(' ')[1] }}</div>
        </div>
        {% endfor %}
      </div>
    </section>
    {% endif %}
    {% endfor %}

    <!-- Quote of the day -->
    <section class="quote-section">
      <div class="quote">{{ t(quote_en, quote_vi) }}</div>
      <div class="author">— {{ quote_author }}</div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer-content">
        <span class="copyright">© {{ year }} AI Daily News</span>
        <span class="brand">AI DAILY NEWS</span>
        <span class="time">{{ t("Published " ~ gen_time, "Phát hành " ~ gen_time) }}</span>
      </div>
    </footer>
  </div>
  </main>

  <!-- Bottom navigation: previous / archive / next / today -->
  <nav class="report-nav" id="reportNav" data-label-en="Issue navigation" data-label-vi="Điều hướng bản tin">
    <button class="rn-btn" id="navPrev">‹ {{ t("Previous", "Trước") }}</button>
    <button class="rn-btn rn-review" id="navReview">📜 {{ t("Archive", "Lưu trữ") }}</button>
    <button class="rn-btn" id="navNext">{{ t("Next", "Sau") }} ›</button>
    <button class="rn-btn rn-today" id="navToday">📰 {{ t("Today", "Hôm nay") }}</button>
  </nav>

  <div class="history-overlay" id="historyOverlay" role="dialog" aria-modal="true" data-label-en="Report archive" data-label-vi="Lưu trữ bản tin">
    <div class="hpanel">
      <div class="hpanel-head">
        <div>
          <div class="hpanel-title">{{ t("Report archive", "Lưu trữ bản tin") }}</div>
          <div class="hpanel-sub" id="hmStats"></div>
        </div>
        <button class="hpanel-x" id="ovClose" data-label-en="Close" data-label-vi="Đóng">✕</button>
      </div>
      <div class="hpanel-scroll">
        <div class="hm">
          <div class="hm-weekdays">
            <span>{{ t("M", "T2") }}</span><span>{{ t("T", "T3") }}</span><span>{{ t("W", "T4") }}</span><span>{{ t("T", "T5") }}</span><span>{{ t("F", "T6") }}</span><span>{{ t("S", "T7") }}</span><span>{{ t("S", "CN") }}</span>
          </div>
          <div class="hm-right">
            <div class="hm-months" id="hmMonths"></div>
            <div class="hm-weeks" id="hmWeeks"></div>
          </div>
        </div>
        <input class="tl-search" id="tlSearch" type="search" data-ph-en="🔍 Search titles / sources…" data-ph-vi="🔍 Tìm tiêu đề / nguồn…" autocomplete="off">
        <div id="tlList"></div>
      </div>
    </div>
  </div>

{% raw %}
  <script src="assets/vendor/page-flip.browser.js"></script>
  <script>
  (function () {
    "use strict";
    var BASE = location.pathname.indexOf("/archive/") !== -1 ? "../" : "./";
    var UNIT = 19, GAP = 4; // matches CSS: 15px cell + 4px gap
    var MAX_PAGE_WIDTH = 820;

    // Strings created from JS (static text is rendered in both languages in the HTML)
    var MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July",
                     "August", "September", "October", "November", "December"];
    var T = {
      en: {
        loading: "Loading…",
        loadFailed: "Failed to load",
        manifestFailed: "Could not load the archive, please reload the page",
        stats: function (n, a, b) { return "📊 " + n + " issues · " + a + " → " + b; },
        now: "now",
        issue: function (n) { return "No. " + n; },
        noMatch: "No matching issues",
        untitled: "(untitled)",
        monthShort: function (m) { return MONTHS_EN[m - 1].slice(0, 3); },
        monthLong: function (m, y) { return MONTHS_EN[m - 1] + " " + y; },
        date: function (d) { return d.slice(4, 6) + "/" + d.slice(6, 8); }
      },
      vi: {
        loading: "Đang tải…",
        loadFailed: "Tải thất bại",
        manifestFailed: "Không tải được danh sách, hãy tải lại trang",
        stats: function (n, a, b) { return "📊 " + n + " số · " + a + " → " + b; },
        now: "nay",
        issue: function (n) { return "Số " + n; },
        noMatch: "Không có số báo phù hợp",
        untitled: "(không có tiêu đề)",
        monthShort: function (m) { return "Th" + m; },
        monthLong: function (m, y) { return "Tháng " + m + "/" + y; },
        date: function (d) { return d.slice(6, 8) + "/" + d.slice(4, 6); }
      }
    };

    var manifest = null;
    var items = [];      // sorted by date ascending (book page i = items[i])
    var dateIndex = {};  // date -> index in items
    var curIdx = -1;

    // Book state (StPageFlip); null when the book is not active
    var pageFlip = null;
    var pages = [];      // one element per issue
    var loaded = [];     // per page: undefined | "pending" | true
    var bookSize = null;

    function $(id) { return document.getElementById(id); }
    function u(p) { return BASE + p; }
    function lang() { return document.documentElement.getAttribute("data-lang") === "vi" ? "vi" : "en"; }
    function tr() { return T[lang()]; }
    function dash(d) { return d.slice(0, 4) + "-" + d.slice(4, 6) + "-" + d.slice(6, 8); }
    function pad(n) { return n < 10 ? "0" + n : "" + n; }
    function ymd(dt) { return "" + dt.getFullYear() + pad(dt.getMonth() + 1) + pad(dt.getDate()); }
    function itemTitle(it) { return (lang() === "vi" ? it.title_vi : "") || it.title || tr().untitled; }
    function reducedMotion() {
      return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    // ----- Language -----
    function applyLabels() {
      var l = lang();
      document.querySelectorAll("[data-label-" + l + "]").forEach(function (el) {
        el.setAttribute("aria-label", el.getAttribute("data-label-" + l));
      });
      document.querySelectorAll("[data-ph-" + l + "]").forEach(function (el) {
        el.setAttribute("placeholder", el.getAttribute("data-ph-" + l));
      });
      document.querySelectorAll("[data-set-lang]").forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-set-lang") === l ? "true" : "false");
      });
    }

    function setLang(l) {
      l = l === "vi" ? "vi" : "en";
      document.documentElement.setAttribute("data-lang", l);
      document.documentElement.lang = l;
      try { localStorage.setItem("aidaily-lang", l); } catch (e) {}
      applyLabels();
      if ($("historyOverlay").classList.contains("open") && manifest) {
        renderStats(manifest);
        renderHeatmap();
        renderTimeline($("tlSearch").value);
      }
    }

    // ----- Archive manifest -----
    function entryPath(date) {
      return date === manifest.meta.today ? u("index.html") : u("archive/" + date + ".html");
    }

    function ensure(cb) {
      if (manifest) { cb(manifest); return; }
      fetch(u("data/archive_manifest.json"), { cache: "no-cache" })
        .then(function (r) { return r.json(); })
        .then(function (m) {
          manifest = m;
          items = (m.items || []).slice().sort(function (a, b) {
            return a.date < b.date ? -1 : a.date > b.date ? 1 : 0;
          });
          dateIndex = {};
          items.forEach(function (it, i) { dateIndex[it.date] = i; });
          cb(m);
        })
        .catch(function (e) {
          console.error("[history] manifest load failed", e);
          var s = $("hmStats"); if (s) s.textContent = tr().manifestFailed;
        });
    }

    function openOverlay() {
      var ov = $("historyOverlay");
      if (!ov) return;
      ov.classList.add("open");
      $("hmStats").textContent = tr().loading;
      ensure(function (m) {
        renderStats(m);
        renderHeatmap();
        renderTimeline("");
      });
    }

    function closeOverlay() {
      var ov = $("historyOverlay");
      if (ov) ov.classList.remove("open");
    }

    function renderStats(m) {
      var el = $("hmStats");
      if (!el || !m) return;
      var meta = m.meta || {};
      el.textContent = tr().stats(meta.count || 0,
        meta.first ? dash(meta.first) : "—",
        meta.last ? dash(meta.last) : tr().now);
    }

    function renderHeatmap() {
      var weeksHost = $("hmWeeks"), monthsHost = $("hmMonths");
      if (!weeksHost || !monthsHost || !items.length) return;
      weeksHost.innerHTML = "";
      monthsHost.innerHTML = "";

      var byDate = {};
      items.forEach(function (it) { byDate[it.date] = it; });

      var first = items[0].date, last = items[items.length - 1].date;
      var start = new Date(+first.slice(0, 4), +first.slice(4, 6) - 1, +first.slice(6, 8));
      var end = new Date(+last.slice(0, 4), +last.slice(4, 6) - 1, +last.slice(6, 8));
      var dow = (start.getDay() + 6) % 7; // 0 = Monday
      start.setDate(start.getDate() - dow);

      var cols = [];
      var cur = new Date(start.getTime());
      while (cur <= end) {
        var cells = [];
        for (var r = 0; r < 7; r++) {
          var ds = ymd(cur);
          cells.push({ date: ds, item: byDate[ds] || null });
          cur.setDate(cur.getDate() + 1);
        }
        cols.push(cells);
      }

      // Month labels: run-length of each week's first-day month, width aligned to week columns
      var months = [];
      cols.forEach(function (c, i) {
        var mk = c[0].date.slice(0, 6);
        if (i === 0 || mk !== cols[i - 1][0].date.slice(0, 6)) months.push({ mk: mk, count: 1 });
        else months[months.length - 1].count++;
      });
      months.forEach(function (mm) {
        var el = document.createElement("div");
        el.className = "hm-month";
        el.textContent = tr().monthShort(+mm.mk.slice(4, 6));
        el.style.width = (mm.count * UNIT - GAP) + "px";
        monthsHost.appendChild(el);
      });

      cols.forEach(function (c) {
        var col = document.createElement("div");
        col.className = "hm-col";
        c.forEach(function (cell) {
          var d = document.createElement("div");
          d.className = "hm-cell" + (cell.item ? " has" : "");
          if (cell.item) {
            d.title = dash(cell.date) + " · " + tr().issue(cell.item.issue || "?") + " · " + itemTitle(cell.item);
            d.addEventListener("click", function () { pickDate(cell.date); });
          }
          col.appendChild(d);
        });
        weeksHost.appendChild(col);
      });
    }

    function renderTimeline(q) {
      var host = $("tlList");
      if (!host) return;
      host.innerHTML = "";
      if (!items.length) return;
      var ql = (q || "").trim().toLowerCase();
      var desc = items.slice().reverse();
      var groups = {}, order = [];
      desc.forEach(function (it) {
        var mk = it.date.slice(0, 6);
        if (!groups[mk]) { groups[mk] = []; order.push(mk); }
        var hay = (it.title || "") + " " + (it.title_vi || "") + " " + (it.source || "");
        if (!ql || hay.toLowerCase().indexOf(ql) >= 0) groups[mk].push(it);
      });

      if (!order.some(function (mk) { return groups[mk].length; })) {
        var empty = document.createElement("div");
        empty.className = "tl-empty";
        empty.textContent = tr().noMatch;
        host.appendChild(empty);
        return;
      }

      order.forEach(function (mk) {
        var list = groups[mk];
        if (!list.length) return;
        var g = document.createElement("div");
        g.className = "tl-group";
        var h = document.createElement("div");
        h.className = "tl-month";
        h.textContent = tr().monthLong(+mk.slice(4, 6), mk.slice(0, 4));
        g.appendChild(h);
        list.forEach(function (it) {
          var row = document.createElement("div");
          row.className = "tl-item";
          row.tabIndex = 0;
          var dEl = document.createElement("span"); dEl.className = "tl-date"; dEl.textContent = tr().date(it.date); row.appendChild(dEl);
          var iEl = document.createElement("span"); iEl.className = "tl-issue"; iEl.textContent = tr().issue(it.issue || "?"); row.appendChild(iEl);
          var tEl = document.createElement("span"); tEl.className = "tl-title"; tEl.textContent = itemTitle(it); row.appendChild(tEl);
          var aEl = document.createElement("span"); aEl.className = "tl-arrow"; aEl.textContent = "›"; row.appendChild(aEl);
          var open = function () { pickDate(it.date); };
          row.addEventListener("click", open);
          row.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); }
          });
          g.appendChild(row);
        });
        host.appendChild(g);
      });
    }

    function updateNav() {
      var prev = $("navPrev"), next = $("navNext");
      if (prev) prev.disabled = curIdx <= 0;
      if (next) next.disabled = curIdx >= items.length - 1;
    }

    // ----- Book (StPageFlip): one issue per page, oldest first -----
    function placeholder(text) {
      var e = document.createElement("div");
      e.className = "report-loading";
      e.textContent = text;
      return e;
    }

    // Fetch an issue's .container into its page (once)
    function loadPage(i) {
      if (i < 0 || i >= items.length || loaded[i]) return;
      loaded[i] = "pending";
      fetch(entryPath(items[i].date), { cache: "no-cache" })
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.text();
        })
        .then(function (html) {
          var c = new DOMParser().parseFromString(html, "text/html").querySelector(".container");
          if (!c) throw new Error("no .container");
          pages[i].innerHTML = "";
          pages[i].appendChild(document.importNode(c, true));
          loaded[i] = true;
        })
        .catch(function (e) {
          console.error("[book] page load failed", items[i].date, e);
          pages[i].innerHTML = "";
          pages[i].appendChild(placeholder(tr().loadFailed));
          loaded[i] = undefined; // retry next time
        });
    }

    function loadAround(i) {
      loadPage(i);
      loadPage(i - 1);
      loadPage(i + 1);
    }

    function measure() {
      var stage = $("reportStage");
      var navH = navEl ? navEl.offsetHeight : 0;
      return {
        w: Math.min(stage.clientWidth || window.innerWidth, MAX_PAGE_WIDTH),
        h: Math.max(320, window.innerHeight - navH)
      };
    }

    function createBook(startIdx) {
      var stage = $("reportStage");
      var size = measure();
      bookSize = size;
      stage.style.height = size.h + "px";

      var book = document.createElement("div");
      book.id = "book";
      book.style.width = size.w + "px";
      book.style.height = size.h + "px";
      stage.innerHTML = "";
      stage.appendChild(book);

      // Start from clean page elements (StPageFlip styles them while drawing)
      pages.forEach(function (p) { p.removeAttribute("style"); p.className = "book-page"; });

      pageFlip = new St.PageFlip(book, {
        width: size.w,
        height: size.h,
        size: "stretch",
        // Portrait (one page at a time) is used while the block is narrower than 2 x minWidth
        minWidth: Math.floor(size.w / 2) + 1,
        maxWidth: size.w,
        minHeight: 100,
        maxHeight: size.h,
        usePortrait: true,
        autoSize: false,            // keep the block at our size so wide screens stay one page
        showCover: false,
        startPage: startIdx,
        flippingTime: reducedMotion() ? 1 : 800,
        drawShadow: !reducedMotion(),
        maxShadowOpacity: 0.45,
        mobileScrollSupport: true,  // vertical swipes scroll the page instead of turning it
        swipeDistance: 30,
        showPageCorners: true,
        disableFlipByClick: true    // a tap only turns the page from a corner
      });
      pageFlip.loadFromHTML(pages);
      pageFlip.on("flip", function (e) { onPageChange(e.data); });

      // StPageFlip completes a finger/mouse-driven turn only once the corner passes the
      // spine (the far edge in portrait), so short drags spring back. Complete the turn
      // once it is about 40% done instead. Same logic as the library's stopMove (v2.0.7).
      var flipController = pageFlip.getFlipController();
      flipController.stopMove = function () {
        if (this.calc === null) return;
        var pos = this.calc.getPosition();
        var rect = this.getBoundsRect();
        var y = this.calc.getCorner() === "bottom" ? rect.height : 0;
        if (pos.x <= rect.pageWidth * 0.6) this.animateFlippingTo(pos, { x: -rect.pageWidth, y: y }, true);
        else this.animateFlippingTo(pos, { x: rect.pageWidth, y: y }, false);
      };
    }

    function buildBook() {
      if (!window.St || !St.PageFlip || items.length < 2 || curIdx < 0) return;
      var current = $("reportStage").querySelector(".container");
      pages = items.map(function (it, i) {
        var p = document.createElement("div");
        p.className = "book-page";
        if (i === curIdx && current) {
          p.appendChild(current);
          loaded[i] = true;
        } else {
          p.appendChild(placeholder(tr().loading));
        }
        return p;
      });
      document.documentElement.classList.add("book-mode");
      createBook(curIdx);
      loadAround(curIdx);
    }

    // Rebuild the book when the viewport size changes noticeably (e.g. rotation)
    var resizeTimer = null;
    function onResize() {
      if (!pageFlip) return;
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () {
        var size = measure();
        if (Math.abs(size.w - bookSize.w) < 30 && Math.abs(size.h - bookSize.h) < 60) return;
        var idx = pageFlip.getCurrentPageIndex();
        pageFlip.destroy();
        createBook(idx);
      }, 250);
    }

    function onPageChange(i) {
      curIdx = i;
      updateNav();
      document.title = "AI Daily News | " + dash(items[i].date);
      loadAround(i);
    }

    // Turn to a given issue (animated when the book is active, page navigation otherwise)
    function goTo(i) {
      if (i < 0 || i >= items.length || i === curIdx) return;
      if (!pageFlip) { location.href = entryPath(items[i].date); return; }
      loadAround(i);
      // StPageFlip routes programmatic flips through its click handler, which
      // disableFlipByClick blocks outside the corners; lift it for this call
      var settings = pageFlip.getSettings();
      settings.disableFlipByClick = false;
      try {
        if (i === curIdx + 1) pageFlip.flipNext();
        else if (i === curIdx - 1) pageFlip.flipPrev();
        else pageFlip.flip(i);
      } finally {
        settings.disableFlipByClick = true;
      }
    }

    function navPrev() { ensure(function () { goTo(curIdx - 1); }); }
    function navNext() { ensure(function () { goTo(curIdx + 1); }); }
    function navToday() { ensure(function (m) { if (dateIndex[m.meta.today] != null) goTo(dateIndex[m.meta.today]); }); }

    // Pick a day from the archive panel: close the panel and turn to that issue
    function pickDate(date) {
      closeOverlay();
      ensure(function () { if (dateIndex[date] != null) goTo(dateIndex[date]); });
    }

    // PWA: resolve manifest / icon paths against BASE and register the service worker
    var manifestLink = document.querySelector('link[rel="manifest"]');
    if (manifestLink) manifestLink.href = u("manifest.webmanifest");
    var appleIcon = document.querySelector('link[rel="apple-touch-icon"]');
    if (appleIcon) appleIcon.href = u("icons/apple-touch-icon.png");
    if ("serviceWorker" in navigator) {
      window.addEventListener("load", function () {
        navigator.serviceWorker.register(u("sw.js")).catch(function () {});
      });
    }

    // Event bindings
    var navEl = $("reportNav");
    $("navToday").addEventListener("click", navToday);
    $("navPrev").addEventListener("click", navPrev);
    $("navNext").addEventListener("click", navNext);
    $("navReview").addEventListener("click", openOverlay);
    $("ovClose").addEventListener("click", closeOverlay);
    $("historyOverlay").addEventListener("click", function (e) { if (e.target === this) closeOverlay(); });
    $("tlSearch").addEventListener("input", function (e) { renderTimeline(e.target.value); });
    // Delegated: the language switch lives inside each page
    document.addEventListener("click", function (e) {
      var b = e.target.closest ? e.target.closest("[data-set-lang]") : null;
      if (b) setLang(b.getAttribute("data-set-lang"));
    });
    window.addEventListener("resize", onResize);

    // Quick horizontal swipes. StPageFlip decides a short touch by where the finger
    // lifts (and its own swipe check misses swipes slower than 250 ms), which can turn
    // the wrong way, so quick swipes turn by their direction here. Slower drags are left
    // to the library, which folds the page under the finger. The capture listener on
    // window runs before the library's own touchend handler.
    var SWIPE_MAX_MS = 350;
    var swipeStart = null;
    $("reportStage").addEventListener("touchstart", function (e) {
      var t = e.touches[0];
      swipeStart = e.touches.length === 1 ? { x: t.clientX, y: t.clientY, time: Date.now() } : null;
    }, { passive: true, capture: true });
    window.addEventListener("touchend", function (e) {
      if (!pageFlip || !swipeStart) return;
      var t = e.changedTouches[0];
      var dx = t.clientX - swipeStart.x, dy = Math.abs(t.clientY - swipeStart.y);
      var quick = Date.now() - swipeStart.time < SWIPE_MAX_MS;
      swipeStart = null;
      if (quick && Math.abs(dx) > 30 && dy < 60) {
        setTimeout(function () {
          // Skip if the library already started turning (a swipe it recognised itself)
          if (pageFlip && pageFlip.getState() !== "flipping") goTo(curIdx + (dx < 0 ? 1 : -1));
        }, 0);
      }
    }, true);

    document.addEventListener("keydown", function (e) {
      var overlayOpen = $("historyOverlay").classList.contains("open");
      if (e.key === "Escape" && overlayOpen) { closeOverlay(); return; }
      if (overlayOpen || e.altKey || e.ctrlKey || e.metaKey) return;
      var tag = (e.target.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      if (e.key === "ArrowLeft") navPrev();
      else if (e.key === "ArrowRight") navNext();
    });

    applyLabels();

    // Startup: load the manifest, locate this page's issue, then open the book on it
    ensure(function (m) {
      var here = document.querySelector('meta[name="report-date"]');
      var hereDate = here ? here.content.replace(/-/g, "") : m.meta.today;
      curIdx = dateIndex[hereDate];
      if (curIdx == null) curIdx = items.length - 1;
      updateNav();
      buildBook();
    });
  })();
  </script>
{% endraw %}
</body>
</html>
"""

# Quote of the day: (English, Vietnamese translation, author)
QUOTES = [
    ("AI is the new electricity.",
     "AI là dòng điện mới của thời đại.",
     "Andrew Ng"),
    ("The future is already here — it's just not very evenly distributed.",
     "Tương lai đã đến — chỉ là chưa được phân bổ đồng đều.",
     "William Gibson"),
    ("The best way to predict the future is to invent it.",
     "Cách tốt nhất để dự đoán tương lai là tạo ra nó.",
     "Alan Kay"),
    ("Any sufficiently advanced technology is indistinguishable from magic.",
     "Mọi công nghệ đủ tiên tiến đều không khác gì phép thuật.",
     "Arthur C. Clarke"),
    ("We can only see a short distance ahead, but we can see plenty there that needs to be done.",
     "Ta chỉ nhìn thấy một quãng ngắn phía trước, nhưng ở đó đã có rất nhiều việc cần làm.",
     "Alan Turing"),
    ("The question of whether a computer can think is no more interesting than the question of whether a submarine can swim.",
     "Hỏi máy tính có biết suy nghĩ không cũng chẳng thú vị hơn hỏi tàu ngầm có biết bơi không.",
     "Edsger W. Dijkstra"),
    ("Machine intelligence is the last invention that humanity will ever need to make.",
     "Trí tuệ máy móc là phát minh cuối cùng mà nhân loại cần phải làm ra.",
     "Nick Bostrom"),
    ("AI won't replace you, but a person using AI will.",
     "AI sẽ không thay thế bạn, nhưng người biết dùng AI thì có thể.",
     "Common saying"),
]

WEEKDAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAYS_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]


def generate_html(categories, now=None, issue_num=None):
    """Render the report HTML for `now` (default: the current time).

    `issue_num` defaults to the number derived from ISSUE_START_DATE.
    """
    now = now or datetime.now()
    if issue_num is None:
        issue_num = (now - ISSUE_START_DATE).days + 1
    # Pick the quote by date so re-running on the same day gives the same page
    quote_en, quote_vi, quote_author = QUOTES[now.toordinal() % len(QUOTES)]

    # autoescape: titles come from external feeds
    template = Template(HTML_TEMPLATE, autoescape=True)
    return template.render(
        style_version=STYLE_VERSION,
        date_str=now.strftime("%Y-%m-%d"),
        date_en=f"{WEEKDAYS_EN[now.weekday()]}, {MONTHS_EN[now.month - 1]} {now.day}, {now.year}",
        date_vi=f"{WEEKDAYS_VI[now.weekday()]}, {now.strftime('%d/%m/%Y')}",
        gen_time=now.strftime("%H:%M"),
        year=now.year,
        issue_num=issue_num,
        categories=categories,
        sections=SECTIONS,
        quote_en=quote_en,
        quote_vi=quote_vi,
        quote_author=quote_author,
    )


def save_html(html):
    """Write today's report to index.html."""
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ HTML saved: {INDEX_FILE}")
    return INDEX_FILE


def to_archive_paths(html):
    """Point a report's relative asset links (href/src) one level up, for pages stored in archive/."""
    return re.sub(r'(href|src)="(assets/|icons/|manifest\.webmanifest)', r'\g<1>="../\g<2>', html)


def read_report_date(html):
    """Return the report date (YYYYMMDD) of a report page, or None.

    Prefers <meta name="report-date">, then falls back to the first
    YYYY-MM-DD in <title> (older issues use a Chinese title).
    """
    m = re.search(r'<meta name="report-date" content="(\d{4})-(\d{2})-(\d{2})"', html)
    if not m:
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        if title:
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})", title.group(1))
    return "".join(m.groups()) if m else None


def archive_previous():
    """Copy the current index.html to archive/ before it is overwritten.

    Skipped when index.html is already today's report, so re-running the
    workflow on the same day does not archive an early draft of today.
    """
    if not os.path.exists(INDEX_FILE):
        return

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    date = read_report_date(html)

    if not date:
        print("⚠️ Could not read the date of index.html; not archived")
        return
    if date == datetime.now().strftime("%Y%m%d"):
        return

    # Always overwrite: index.html holds the final version of that day, while an
    # existing archive file may be an early draft from an older same-day re-run
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    archive_file = os.path.join(ARCHIVE_DIR, f"{date}.html")
    with open(archive_file, "w", encoding="utf-8") as f:
        f.write(to_archive_paths(html))
    print(f"✓ Archived: {archive_file}")


def _bilingual_text(node) -> tuple[str, str]:
    """Return (English, Vietnamese) text of a node rendered with i18n spans.

    Pages without i18n spans return the node's plain text for both.
    """
    en = node.select_one(".i18n-en")
    vi = node.select_one(".i18n-vi")
    if en is None and vi is None:
        text = node.get_text(strip=True)
        return text, text
    en_text = en.get_text(strip=True) if en else ""
    vi_text = vi.get_text(strip=True) if vi else ""
    return en_text or vi_text, vi_text or en_text


def _parse_report_for_manifest(path: str, date_hint: str) -> dict | None:
    """Extract the manifest fields from one report page (missing fields become empty strings)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None

    soup = BeautifulSoup(content, "html.parser")
    date = read_report_date(content) or date_hint

    # Issue number: digits in .header-left ("No. N" / "Số N")
    issue = ""
    left = soup.select_one(".header-left")
    if left:
        m = re.search(r"(\d+)", left.get_text())
        if m:
            issue = m.group(1)

    # Main headline: title (English + Vietnamese) / link / source
    title, title_vi, link, source = "", "", "", ""
    a = soup.select_one(".main-headline .headline-title a")
    if a:
        title, title_vi = _bilingual_text(a)
        link = a.get("href", "") or ""
    src = soup.select_one(".main-headline .headline-source")
    if src:
        source = src.get_text(strip=True)

    # Fallback for older templates without .main-headline: use the first news item
    if not title:
        first_a = soup.select_one(".news-item .news-title a")
        first_t = soup.select_one(".news-item .news-title")
        node = first_a or first_t
        if node:
            title, title_vi = _bilingual_text(node)
            if first_a:
                link = first_a.get("href", "") or ""
        first_src = soup.select_one(".news-item .news-source")
        if first_src and not source:
            source = first_src.get_text(strip=True)

    quote = ""
    q = soup.select_one(".quote-section .quote")
    if q:
        quote = _bilingual_text(q)[0]

    return {
        "date": date,
        "issue": issue,
        "title": title,
        "title_vi": title_vi,
        "link": link,
        "source": source,
        "quote": quote,
    }


def generate_manifest() -> None:
    """Scan index.html + archive/*.html and write data/archive_manifest.json.

    A static site cannot list directories, so the archive UI relies on this
    manifest. It is fully rebuilt on every run.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    items: list[dict] = []

    # Today (index.html) - the date is corrected from the page itself
    if os.path.exists(INDEX_FILE):
        e = _parse_report_for_manifest(INDEX_FILE, today)
        if e:
            items.append(e)

    # Archived issues (file name is the date)
    for f in sorted(glob.glob(os.path.join(ARCHIVE_DIR, "*.html"))):
        date_hint = os.path.splitext(os.path.basename(f))[0]
        e = _parse_report_for_manifest(f, date_hint)
        if e:
            items.append(e)

    # Dedupe by date (index.html wins over an archive of the same day), then sort ascending
    seen: set[str] = set()
    deduped: list[dict] = []
    for it in items:
        if not it["date"] or it["date"] in seen:
            continue
        seen.add(it["date"])
        deduped.append(it)
    deduped.sort(key=lambda x: x["date"])

    manifest = {
        "meta": {
            "today": today,
            "count": len(deduped),
            "first": deduped[0]["date"] if deduped else "",
            "last": deduped[-1]["date"] if deduped else "",
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
        "items": deduped,
    }

    out = os.path.join(DATA_DIR, "archive_manifest.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False)
    print(f"✓ Archive manifest written: {out} ({len(deduped)} issues)")


def main():
    print("=" * 50)
    print("🤖 AI Daily News - generate HTML")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print()

    cat_file = os.path.join(DATA_DIR, "categorized_news.json")
    if not os.path.exists(cat_file):
        print("✗ News data not found, run fetch_news.py first")
        try:
            generate_manifest()
        except Exception as exc:
            print(f"⚠️ Failed to build archive manifest: {exc}")
        return

    with open(cat_file, "r", encoding="utf-8") as f:
        categories = json.load(f)

    archive_previous()
    save_html(generate_html(categories))

    # Refresh the archive manifest (scans index.html + archive/)
    try:
        generate_manifest()
    except Exception as exc:
        print(f"⚠️ Failed to build archive manifest: {exc}")

    print("\n✓ Daily report generated!")


if __name__ == "__main__":
    main()
