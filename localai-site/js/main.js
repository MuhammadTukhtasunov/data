/* [COMPANY NAME] — minimal vanilla JS. No dependencies, no tracking, no external requests. */
(function () {
  "use strict";

  /* Mobile nav toggle */
  var toggle = document.querySelector(".nav-toggle");
  var menu = document.getElementById("nav-menu");
  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var open = menu.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    menu.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        menu.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* Footer year */
  var year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());

  /* Live external-request counter — the trust badge.
     Counts every resource this page actually loaded and reports how many
     came from a different origin. On this site the answer is 0. */
  function countExternal() {
    var el = document.getElementById("ext-count");
    if (!el || !("performance" in window)) return;
    var here = location.origin;
    var entries = performance.getEntriesByType("resource");
    var external = entries.filter(function (r) {
      return r.name.indexOf(here) !== 0;
    }).length;
    var total = entries.length + 1; /* +1 for the document itself */
    el.textContent = String(external);
    var sub = document.querySelector(".badge-sub");
    if (sub && external === 0) {
      sub.textContent =
        "All " + total + " requests served from this site’s own domain. " +
        "Measured live in your browser — no cookies, no analytics, no trackers.";
    }
  }
  if (document.readyState === "complete") countExternal();
  else window.addEventListener("load", function () { setTimeout(countExternal, 0); });

  /* Contact form: if the Formspree endpoint placeholder hasn't been replaced
     yet, don't let the form submit into a 404 — show a helpful note instead. */
  var form = document.querySelector(".contact-form");
  if (form && (form.getAttribute("action") || "").indexOf("[") !== -1) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var status = form.querySelector(".form-status");
      if (status) {
        status.hidden = false;
        status.textContent =
          "Form endpoint not configured yet — please email me directly instead.";
      }
    });
  }
})();
