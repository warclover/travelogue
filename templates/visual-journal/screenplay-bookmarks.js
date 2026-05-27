/**
 * Travelogue · present in-show bookmarks (featured grid · trip index)
 */
(function (global) {
  "use strict";

  var LAYOUT_SELECTOR = '.layout-screen[data-block="layout-screen"]';

  function isLayoutScreen(el) {
    return el.matches && el.matches(LAYOUT_SELECTOR);
  }

  function chapterKeyFromHref(href) {
    var id = (href || "").replace(/^#/, "");
    var match = id.match(/(\d+)/);
    return match ? match[1] : id;
  }

  function slideIndexForAsset(assetId, sources) {
    if (!assetId) return -1;
    for (var i = 0; i < sources.length; i++) {
      var el = sources[i];
      if (!isLayoutScreen(el)) continue;
      var ids = (el.getAttribute("data-asset-ids") || "").split(",");
      for (var j = 0; j < ids.length; j++) {
        if (ids[j] === assetId) return i;
      }
    }
    return -1;
  }

  function slideIndexForChapterKey(chapterKey, sources) {
    if (!chapterKey) return -1;
    for (var i = 0; i < sources.length; i++) {
      var el = sources[i];
      if (!isLayoutScreen(el)) continue;
      if (el.getAttribute("data-chapter-index") === chapterKey) return i;
    }
    return -1;
  }

  function wire(root, player) {
    root.addEventListener("click", function (e) {
      if (!player.running) return;
      var card = e.target.closest(".featured-grid__card[data-asset-id]");
      if (card) {
        e.preventDefault();
        e.stopPropagation();
        var idx = slideIndexForAsset(card.getAttribute("data-asset-id"), player.sources);
        if (idx >= 0) player.goTo(idx);
        return;
      }
      var link = e.target.closest('.trip-index__link[href^="#"]');
      if (link) {
        e.preventDefault();
        e.stopPropagation();
        var key = chapterKeyFromHref(link.getAttribute("href"));
        var slideIdx = slideIndexForChapterKey(key, player.sources);
        if (slideIdx >= 0) player.goTo(slideIdx);
      }
    });
  }

  global.TraveloguePresentBookmarks = {
    wire: wire,
    slideIndexForAsset: slideIndexForAsset,
    slideIndexForChapterKey: slideIndexForChapterKey,
  };
})(window);
