"""Share-Ready Optimization V1 · W0 e2e（AC-SR-02 / AC-SR-01 冒烟）。

对照 docs/ACCEPTANCE-SHARE-READY-OPTIMIZATION-V1.md。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e.test_studio_home_v2_ac_playwright import _goto_v2
from tests.integration.studio.test_studio_server import _free_port, _start_studio_server
from travelogue.web.studio_jobs import reset_job_store

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


@pytest.fixture(autouse=True)
def _reset_jobs() -> None:
    reset_job_store()


@pytest.fixture
def studio_server(tmp_path: Path):
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        yield {"base": base}
    finally:
        server.shutdown()
        server.server_close()


def _prepare_page(page, base: str) -> None:
    page.add_init_script(
        """
        try {
          localStorage.setItem('travelogue.desktop.capabilityCard.v1', '1');
        } catch (e) {}
        """
    )
    _goto_v2(page, base, "dev=1&studioFixture=empty")
    page.evaluate(
        """
        () => {
          const el = document.getElementById('studio-capability-card-root');
          if (el) el.hidden = true;
        }
        """
    )


def _load_recipe(page) -> None:
    page.evaluate(
        """
        async () => {
          const mod = await import('/__studio/js/output-recipe.js');
          mod.applyOutputRecipeConfig({
            outputRecipe: {
              enabled: true,
              bands: { sparseMax: 9, ambiguousMax: 30, narrativeChapterHintAt: 50 },
            },
          });
          window.__outputRecipe = mod;
        }
        """
    )


def test_ac_sr_02_server_kept_n_wins_over_sparse_dom(studio_server) -> None:
    """AC-SR-02 · 服务端 kept_n=18（Ambiguous）时，即使 DOM 估数为 Sparse 仍需意图卡。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _prepare_page(page, studio_server["base"])
        _load_recipe(page)

        # DOM 估数偏少（Sparse）不得覆盖服务端 Band
        dom_sparse = page.evaluate(
            "() => window.__outputRecipe.resolveClientRecipe(3, 'ha-dom', 'preview')"
        )
        assert dom_sparse["band"] == "sparse"
        assert dom_sparse["needsIntent"] is False

        tip = page.evaluate(
            """
            () => window.__outputRecipe.tipRecipeFromServerPayload(
              {
                ok: true,
                keptN: 18,
                recipe: {
                  band: 'ambiguous',
                  needs_intent: true,
                  kept_n: 18,
                  cta_label: '选择并导出',
                  user_hints: ['这趟精选了 18 张，你想怎么发？'],
                },
              },
              'ha-dom',
              'preview'
            )
            """
        )
        assert tip["band"] == "ambiguous"
        assert tip["needsIntent"] is True
        assert tip["keptN"] == 18
        assert tip["ctaLabel"] == "选择并导出"
        assert page.evaluate("() => window.__outputRecipe.getCachedKeptN('ha-dom')") == 18

        page.evaluate(
            """
            async () => {
              window.__intentResult = null;
              window.__outputRecipe.showAmbiguousIntentCard(18).then((r) => {
                window.__intentResult = r;
              });
            }
            """
        )
        page.wait_for_selector('[data-output-recipe-intent="1"]', timeout=10_000)
        title = page.locator('[data-output-recipe-intent="1"] h3').inner_text()
        assert "精选了 18 张" in title
        assert "kept_n" not in title.lower()
        assert page.locator('[data-output-intent="chat_longshot"]').get_attribute(
            "data-intent-weight"
        ) == "primary"

        browser.close()


def test_ac_sr_01_showcase_frames_not_placeholder(studio_server) -> None:
    """AC-SR-01 / 01b · 首页样品非 PLACEHOLDER；「示例」徽标可见。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _prepare_page(page, studio_server["base"])

        page.wait_for_selector(".v2-carousel__slide-img, .v2-phone__img, [data-demo-flag]", timeout=15_000)
        dims = page.evaluate(
            """
            async () => {
              const imgs = [...document.querySelectorAll(
                '.v2-carousel__slide-img, .v2-phone img, .v2-bento img[src*=\"demo-showcase\"]'
              )];
              await Promise.all(imgs.map((img) => {
                if (img.complete) return Promise.resolve();
                return new Promise((res) => {
                  img.onload = () => res();
                  img.onerror = () => res();
                });
              }));
              return imgs.map((img) => ({
                src: img.currentSrc || img.src || '',
                w: img.naturalWidth || 0,
                h: img.naturalHeight || 0,
              }));
            }
            """
        )
        real = [d for d in dims if d["w"] > 0]
        assert real, f"no showcase images loaded: {dims}"
        for d in real:
            assert "PLACEHOLDER" not in d["src"], d
            assert d["w"] >= 200, d

        flags = page.locator("[data-demo-flag]:not([hidden])")
        assert flags.count() >= 1
        assert "示例" in flags.first.inner_text()

        browser.close()
