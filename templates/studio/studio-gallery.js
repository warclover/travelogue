/**
 * StudioGallery — CMP-HP-16
 * Scroll-snap carousel with featured card, arrow navigation, indicator.
 * IIFE, no framework. <script src="studio-gallery.js" defer>
 */
(function () {
  "use strict";

  /**
   * Initialize a gallery carousel.
   * @param {HTMLElement} carousel - scroll container
   * @param {Object} [opts]
   * @param {HTMLElement} [opts.prevBtn]
   * @param {HTMLElement} [opts.nextBtn]
   * @param {HTMLElement} [opts.indicator]
   */
  window.studioGallery = function (carousel, opts) {
    if (!carousel) return;
    opts = opts || {};

    var cards = carousel.querySelectorAll(".studio__gallery-card");
    if (!cards.length) return;

    var prevBtn = opts.prevBtn;
    var nextBtn = opts.nextBtn;
    var indicator = opts.indicator;

    function getCurrentIndex() {
      var scrollLeft = carousel.scrollLeft;
      var cardWidth = cards[0].offsetWidth + 12; // gap
      var idx = Math.round(scrollLeft / cardWidth);
      return Math.max(0, Math.min(idx, cards.length - 1));
    }

    function scrollToCard(idx) {
      idx = Math.max(0, Math.min(idx, cards.length - 1));
      cards[idx].scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
      updateIndicator(idx);
    }

    function updateIndicator(idx) {
      if (!indicator) return;
      if (idx === undefined) idx = getCurrentIndex();
      indicator.textContent = (idx + 1) + " / " + cards.length;
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", function () {
        scrollToCard(getCurrentIndex() - 1);
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener("click", function () {
        scrollToCard(getCurrentIndex() + 1);
      });
    }

    carousel.addEventListener("scroll", function () {
      updateIndicator();
    }, { passive: true });

    // Keyboard navigation when carousel is focused
    carousel.setAttribute("tabindex", "0");
    carousel.setAttribute("role", "region");
    carousel.setAttribute("aria-label", "样例画廊");
    carousel.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        scrollToCard(getCurrentIndex() - 1);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        scrollToCard(getCurrentIndex() + 1);
      }
    });

    // Touch swipe is handled natively by scroll-snap CSS.
    updateIndicator(0);

    // IntersectionObserver for reveal animation
    var section = carousel.closest(".studio__gallery");
    if (section && "IntersectionObserver" in window) {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-revealed");
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15 });
      observer.observe(section);
    } else if (section) {
      section.classList.add("is-revealed");
    }
  };
})();
