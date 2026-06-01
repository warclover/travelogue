/**
 * Travelogue · present URL hash deep links (#present/N)
 */
(function (global) {
  "use strict";

  function presentConfig() {
    return (global.__TRAVELOGUE_READING__ || {}).present || {};
  }

  function enabled() {
    var cfg = presentConfig();
    if (typeof cfg.deepLink === "boolean") {
      return cfg.deepLink;
    }
    return true;
  }

  function parse() {
    var match = (global.location.hash || "").match(/^#present\/(\d+)$/i);
    if (!match) return null;
    var slide = parseInt(match[1], 10);
    if (!slide || slide < 1) return null;
    return slide - 1;
  }

  function set(index) {
    if (!enabled()) return;
    var hash = "#present/" + (index + 1);
    if (global.location.hash !== hash) {
      global.history.replaceState(null, "", hash);
    }
  }

  function clear() {
    if (!enabled()) return;
    if (/^#present\/\d+$/i.test(global.location.hash || "")) {
      var base = global.location.pathname + global.location.search;
      global.history.replaceState(null, "", base);
    }
  }

  global.TraveloguePresentHash = {
    enabled: enabled,
    parse: parse,
    set: set,
    clear: clear,
  };
})(window);
