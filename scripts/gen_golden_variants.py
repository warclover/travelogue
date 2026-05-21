#!/usr/bin/env python3
"""Generate golden-share / golden-minimal / cover-share (never overwrites golden.html)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "visual-journal"
GOLDEN = TEMPLATE / "golden.html"
SHARE = TEMPLATE / "golden-share.html"
MINIMAL = TEMPLATE / "golden-minimal.html"
COVER = TEMPLATE / "cover-share.html"
CLOSE_DIV = "</" + "div>"


def build_share_html(source: str) -> str:
    html = source
    html = html.replace('href="golden.css"', 'href="journal.css"')
    html = re.sub(
        r'<html lang="zh-CN" data-export="draft">',
        '<html lang="zh-CN" data-export="share" data-layout="mobile">',
        html,
        count=1,
    )
    html = re.sub(
        r"  <title>.*?</title>",
        "  <title>雨后京都</title>",
        html,
        count=1,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'\n  <meta name="description"[^\n]*\n',
        "\n",
        html,
        count=1,
    )
    banner_end = re.escape(CLOSE_DIV)
    html = re.sub(
        rf'(?s)  <div class="golden-banner".*?{banner_end}\n\n',
        "",
        html,
        count=1,
    )
    html = re.sub(r"(?s)\n  <script>.*?</script>\n", "\n", html, count=1)
    html = re.sub(r'\n  <link rel="stylesheet" href="longshot\.css" />\n', "\n", html, count=1)
    html = re.sub(r'\s*data-longshot="[^"]*"', "", html)
    html = re.sub(
        r'(?s)\n  <script src="vendor/html2canvas\.min\.js" defer></script>\n  <script src="longshot\.js" defer></script>\n',
        "\n",
        html,
        count=1,
    )
    html = re.sub(
        r'(?s)\n  <script src="golden-longshot\.js"[^>]*></script>\n',
        "\n",
        html,
        count=1,
    )
    html = re.sub(r'\s*data-editable="[^"]*"', "", html)
    return html


def build_minimal_html() -> str:
    d = "d" + "iv"
    c = "</" + d + ">"
    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-export="draft" data-layout="mobile">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>短途 · Visual Journal 空状态金样例</title>
  <meta name="description" content="hook/lead/voice/caption 省略与 :empty 行为演示" />
  <link rel="stylesheet" href="journal.css" />
</head>
<body>
  <main>
    <article itemscope itemtype="https://schema.org/Trip">
      <header class="cover-hero" data-block="cover-hero">
        <{d} class="cover-hero__media">
          <img src="assets/demo/fallback-w1600.webp"
            srcset="assets/demo/fallback-w800.webp 800w, assets/demo/fallback-w1600.webp 1600w"
            sizes="100vw" alt="封面占位" loading="eager" decoding="async" />
        {c}
        <{d} class="cover-hero__overlay" aria-hidden="true">{c}
        <{d} class="cover-hero__text">
          <h1 itemprop="name">短途</h1>
          <p class="subtitle">一天</p>
        {c}
      </header>

      <{d} class="page">
        <{d} class="trip-meta" data-block="trip-meta">
          <time datetime="2025-05-01/2025-05-01">2025.05.01</time> · 本地
        {c}
        <p class="hook-line" data-block="hook-line"></p>

        <section class="chapter" id="ch-01" data-chapter-id="ch-01" data-pattern="open">
          <header class="chapter-header" data-block="chapter-header">
            <span class="chapter-header__index">01</span>
            <h2>出发</h2>
          </header>
          <figure class="media-card media-card--bleed media-card--fill media-card--overlay"
            data-block="media-card" data-asset-id="asset-min-001">
            <{d} class="media-card__frame">
              <img class="media-card__visual"
                src="assets/demo/fallback-w1600.webp"
                srcset="assets/demo/fallback-w800.webp 800w, assets/demo/fallback-w1600.webp 1600w"
                sizes="100vw" alt="路边" loading="lazy" decoding="async" />
              <{d} class="media-card__overlay-text">
                <h3 class="media-card__title">路边</h3>
              {c}
            {c}
          </figure>
          <figure class="media-card media-card--bleed media-card--fill media-card--overlay"
            data-block="media-card" data-asset-id="asset-min-002">
            <{d} class="media-card__frame">
              <img class="media-card__visual"
                src="assets/demo/fallback-w1600.webp"
                srcset="assets/demo/fallback-w800.webp 800w, assets/demo/fallback-w1600.webp 1600w"
                sizes="100vw" alt="车窗" loading="lazy" decoding="async" />
            {c}
          </figure>
        </section>

        <footer class="footer-cta" data-block="footer-cta">
          <p>Travelogue · Visual Journal</p>
        </footer>
      {c}
    </article>
  </main>
</body>
</html>
"""


def build_cover_share_html() -> str:
    d = "d" + "iv"
    c = "</" + d + ">"
    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-layout="mobile">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>cover-share · preview.jpg 对照</title>
  <link rel="stylesheet" href="journal.css" />
</head>
<body class="cover-share-page">
  <{d} id="cover-share-canvas" class="cover-share" data-block="cover-share" role="img" aria-label="雨后京都分享封面">
    <{d} class="cover-share__media">
      <img src="assets/demo/cover-w1600.webp"
        srcset="assets/demo/cover-w800.webp 800w, assets/demo/cover-w1600.webp 1600w"
        sizes="1080px"
        alt="雨中的京都站"
        loading="eager"
        decoding="async" />
    {c}
    <{d} class="cover-share__overlay" aria-hidden="true">{c}
    <{d} class="cover-share__text">
      <p class="cover-share__place">京都</p>
      <p class="cover-share__dates"><time datetime="2025-04-02/2025-04-06">2025.04.02 – 04.06</time></p>
      <h1 class="cover-share__title">雨后京都</h1>
      <p class="cover-share__hook">鸭川边那阵吹干雨衣的风。</p>
    {c}
  {c}
</body>
</html>
"""


def main() -> None:
    if not GOLDEN.is_file():
        raise SystemExit(f"missing source: {GOLDEN}")
    share = build_share_html(GOLDEN.read_text(encoding="utf-8"))
    SHARE.write_text(share, encoding="utf-8", newline="\n")
    MINIMAL.write_text(build_minimal_html(), encoding="utf-8", newline="\n")
    COVER.write_text(build_cover_share_html(), encoding="utf-8", newline="\n")
    print("OK", SHARE.name, SHARE.stat().st_size, "bytes")
    print("OK", MINIMAL.name)
    print("OK", COVER.name)


if __name__ == "__main__":
    main()
