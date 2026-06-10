/**
 * Travelogue · breath image scrub (cinematic · pure photo screens)
 * Soft fade-rise + subtle scale settle + gentle scroll drift (no clip-path wipe).
 */
(function (global) {
  "use strict";

  function smoothstep(p) {
    if (p <= 0) return 0;
    if (p >= 1) return 1;
    return p * p * (3 - 2 * p);
  }

  function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
  }

  function slotProgress(enterRaw, index, count) {
    if (count <= 1) return smoothstep(enterRaw);
    if (enterRaw >= 1) return 1;
    var delay = index * Math.min(0.07, 0.35 / count);
    var span = 1 - delay * 0.55;
    if (span <= 0.1) span = 0.1;
    return smoothstep((enterRaw - delay) / span);
  }

  function shouldUnifySlotMotion(screen, slots) {
    var hint = screen.getAttribute("data-layout-hint") || "";
    if (hint.indexOf("person-") === 0) return true;
    var pattern = screen.getAttribute("data-pattern") || "";
    if (pattern.indexOf("mosaic") !== -1) return true;
    if (/^screen-portrait-(2|3|4|6|9|grid-8)$/.test(pattern)) return true;
    var grid = screen.querySelector(".layout-screen__grid");
    if (grid) {
      var gridClass = grid.className || "";
      if (
        gridClass.indexOf("--2col") !== -1 ||
        gridClass.indexOf("--3col") !== -1 ||
        gridClass.indexOf("--3x2") !== -1
      ) {
        return true;
      }
    }
    for (var i = 0; i < slots.length; i++) {
      var img = slots[i].querySelector("img");
      if (img && img.classList.contains("layout-slot__img--contain")) {
        return true;
      }
    }
    return false;
  }

  function clearStyles() {
    Array.prototype.forEach.call(
      document.querySelectorAll(".breath-image-slot"),
      function (slot) {
        slot.classList.remove("breath-image-slot");
        var img = slot.querySelector("img");
        if (img) {
          img.style.transform = "";
          img.style.opacity = "";
        }
      }
    );
  }

  function studioMotionBudget() {
    var body = document.body;
    var html = document.documentElement;
    if (
      body &&
      (body.getAttribute("data-preview-toolbar") === "on" ||
        html.getAttribute("data-preview-toolbar") === "on")
    ) {
      return { liftSingle: 12, liftMulti: 8, scaleSingle: 0.035, scaleMulti: 0.02 };
    }
    return { liftSingle: 8, liftMulti: 8, scaleSingle: 0.02, scaleMulti: 0.02 };
  }

  function rhythmNeighborDamp(screen, vh) {
    var next = screen.nextElementSibling;
    while (next) {
      if (next.matches && next.matches('[data-block="breath-pause-screen"]')) {
        return 0;
      }
      if (next.matches && next.matches('[data-block="layout-screen"]')) {
        break;
      }
      next = next.nextElementSibling;
    }
    var rect = screen.getBoundingClientRect();
    if (rect.bottom > vh * 0.88) {
      return clamp((vh * 0.98 - rect.bottom) / (vh * 0.1), 0, 1);
    }
    return 1;
  }

  function setupCinematicImages(gsap, ScrollTrigger, registerTrigger) {
    if (
      global.matchMedia &&
      global.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return;
    }
    clearStyles();
    var budget = studioMotionBudget();

    Array.prototype.forEach.call(
      document.querySelectorAll('.layout-screen[data-block="layout-screen"]'),
      function (screen) {
        var slots = Array.prototype.slice.call(
          screen.querySelectorAll(".layout-slot")
        );
        if (!slots.length) return;

        slots.forEach(function (slot) {
          slot.classList.add("breath-image-slot");
        });

        var multi = slots.length > 1;
        var unifyMotion = shouldUnifySlotMotion(screen, slots);

        registerTrigger(
          ScrollTrigger.create({
            trigger: screen,
            start: "top 98%",
            end: "bottom 2%",
            scrub: 1.15,
            onUpdate: function () {
              var rect = screen.getBoundingClientRect();
              var vh = global.innerHeight || 1;

              /* Enter: screen rises through lower viewport (long, gentle zone) */
              var enterStart = vh * 0.96;
              var enterEnd = vh * 0.52;
              var enterRaw = clamp(
                (enterStart - rect.top) / (enterStart - enterEnd),
                0,
                1
              );

              var scaleMax = multi ? budget.scaleMulti : budget.scaleSingle;
              var liftMax = multi ? budget.liftMulti : budget.liftSingle;
              var driftMax = multi ? 6 : 8;
              var rhythmDamp = rhythmNeighborDamp(screen, vh);

              /* Drift: subtle float while screen crosses viewport center */
              var centerY = rect.top + rect.height * 0.5;
              var driftNorm = clamp((vh * 0.5 - centerY) / (vh * 0.85), -1, 1);

              slots.forEach(function (slot, i) {
                var slotP = unifyMotion
                  ? smoothstep(enterRaw)
                  : slotProgress(enterRaw, i, slots.length);
                var img = slot.querySelector("img");
                if (!img) return;

                var scale = 1 + (1 - slotP) * scaleMax * rhythmDamp;
                var lift = (1 - slotP) * liftMax * rhythmDamp;
                var driftMix = smoothstep(clamp((slotP - 0.72) / 0.28, 0, 1));
                var driftY = driftNorm * driftMax * driftMix * rhythmDamp;
                var opacity = 0.86 + slotP * 0.14;

                img.style.transform =
                  "translate3d(0," +
                  (lift + driftY).toFixed(2) +
                  "px,0) scale(" +
                  scale.toFixed(4) +
                  ")";
                img.style.opacity = opacity.toFixed(3);
              });
            },
          })
        );
      }
    );
  }

  global.TravelogueImageBreath = {
    setup: setupCinematicImages,
    clear: clearStyles,
  };
})(window);
