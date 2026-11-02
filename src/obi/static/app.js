// Remember the language a visitor picks, and load YouTube only when they ask for a video.
(function () {
  "use strict";

  document.addEventListener("click", function (event) {
    var langLink = event.target.closest("[data-set-lang]");
    if (langLink) {
      try { localStorage.setItem("obi.lang", langLink.dataset.setLang); } catch (e) {}
      return;
    }

    var poster = event.target.closest("a[data-youtube]");
    if (!poster || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey) return;
    event.preventDefault();

    var params = new URLSearchParams({ autoplay: "1", rel: "0" });
    if (poster.dataset.start) params.set("start", poster.dataset.start);
    if (poster.dataset.end) params.set("end", poster.dataset.end);

    var frame = document.createElement("iframe");
    frame.className = "video-frame";
    frame.src = "https://www.youtube-nocookie.com/embed/" +
      encodeURIComponent(poster.dataset.youtube) + "?" + params.toString();
    frame.title = poster.dataset.title;
    frame.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
    frame.allowFullscreen = true;
    frame.referrerPolicy = "strict-origin-when-cross-origin";
    poster.replaceWith(frame);
    frame.focus();
  });
})();
