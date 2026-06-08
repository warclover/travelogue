/**
 * Travelogue · breath text highlight (PRD-EXPERIENCE appendix B · P1)
 * Scroll-scrub word/character reveal for hook-line and data-breath-highlight blocks.
 */
(function (global) {
  "use strict";

  var tweens = [];

  function readingScroll() {
    return (global.__TRAVELOGUE_READING__ || {}).scroll || {};
  }

  function usesHighlight() {
    return (
      readingScroll().breath === "cinematic" &&
      readingScroll().breathEngine === "gsap" &&
      global.gsap &&
      global.ScrollTrigger
    );
  }

  function prefersReducedMotion() {
    return (
      global.matchMedia &&
      global.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  function splitUnits(text) {
    var units = [];
    var latin = "";
    for (var i = 0; i < text.length; i++) {
      var ch = text[i];
      if (/[ \t\n\r]/.test(ch)) continue;
      if (/[A-Za-z0-9]/.test(ch)) {
        latin += ch;
      } else {
        if (latin) {
          units.push(latin);
          latin = "";
        }
        units.push(ch);
      }
    }
    if (latin) units.push(latin);
    return units;
  }

  function wrapElement(el) {
    var text = (el.textContent || "").trim();
    var units = splitUnits(text);
    if (units.length < 2) return null;

    el.textContent = "";
    el.classList.add("breath-highlight");
    var spans = [];
    units.forEach(function (unit) {
      var span = document.createElement("span");
      span.className = "breath-highlight__unit";
      span.style.display = "inline";
      span.textContent = unit;
      spans.push(span);
      el.appendChild(span);
    });
    return spans;
  }

  function killTweens() {
    tweens.forEach(function (tw) {
      if (tw && typeof tw.kill === "function") tw.kill();
    });
    tweens = [];
  }

  function destroy() {
    killTweens();
    Array.prototype.forEach.call(
      document.querySelectorAll(".breath-highlight"),
      function (el) {
        var text = "";
        Array.prototype.forEach.call(
          el.querySelectorAll(".breath-highlight__unit"),
          function (span) {
            text += span.textContent;
          }
        );
        el.textContent = text;
        el.classList.remove("breath-highlight");
      }
    );
  }

  function init() {
    destroy();
    if (!usesHighlight()) return;
    if (prefersReducedMotion()) return;

    var gsap = global.gsap;
    var ScrollTrigger = global.ScrollTrigger;
    gsap.registerPlugin(ScrollTrigger);

    var selector =
      '.hook-line[data-block="hook-line"], [data-breath-highlight="true"]';
    Array.prototype.forEach.call(document.querySelectorAll(selector), function (el) {
      if (el.querySelector(".breath-highlight__unit")) return;
      var spans = wrapElement(el);
      if (!spans) return;

      gsap.set(spans, { opacity: 0.08, y: 10 });

      tweens.push(
        gsap.to(spans, {
          opacity: 1,
          y: 0,
          stagger: Math.max(0.06, 1.35 / spans.length),
          ease: "none",
          scrollTrigger: {
            trigger: el,
            start: "top 88%",
            end: "top 22%",
            scrub: 0.85,
          },
        })
      );
    });

    if (typeof ScrollTrigger.refresh === "function") {
      ScrollTrigger.refresh();
    }
  }

  global.TravelogueHighlight = {
    init: init,
    destroy: destroy,
  };
})(window);
