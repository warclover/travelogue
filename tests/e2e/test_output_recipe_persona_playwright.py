"""Output Recipe V1 · 用户 persona 页面功能测试（Playwright）。

对照 docs/ACCEPTANCE-OUTPUT-RECIPE-V1.md §4–5 手测项，以及客户端
templates/studio/js/output-recipe.js。在导出门面尚未完全接线时，先验证：
  - Band → CTA / needsIntent 合同（H-A-01/02/07）
  - Ambiguous 意图卡三选一 + 选择并导出 / 先选不导出（H-A-03/04 · H-B-01）
  - 九宫格文案仅绑定 moments_grid（H-B-01/03 · AC-OR-11b）
  - flag 关闭回退（H-A-08）
  - 书架 Ambiguous fallback 文案（H-A-06）
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e.test_studio_home_v2_ac_playwright import _goto_v2, _wait_visible
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


def _prepare_page(page, base: str, query: str = "dev=1&studioFixture=empty") -> None:
    """抑制首启能力卡，避免挡住意图卡 / CTA 点击。"""
    page.add_init_script(
        """
        try {
          localStorage.setItem('travelogue.desktop.capabilityCard.v1', '1');
        } catch (e) {}
        """
    )
    _goto_v2(page, base, query)
    page.evaluate(
        """
        () => {
          const el = document.getElementById('studio-capability-card-root');
          if (el) el.hidden = true;
        }
        """
    )


def _load_recipe(page, *, enabled: bool = True) -> None:
    page.evaluate(
        """
        async ({ enabled }) => {
          const mod = await import('/__studio/js/output-recipe.js');
          mod.applyOutputRecipeConfig({
            outputRecipe: {
              enabled,
              bands: { sparseMax: 9, ambiguousMax: 30, narrativeChapterHintAt: 50 },
            },
          });
          window.__outputRecipe = mod;
        }
        """,
        {"enabled": enabled},
    )


def _resolve(page, kept_n: int, trip_id: str = "t1", entrypoint: str = "preview"):
    return page.evaluate(
        """
        ({ keptN, tripId, entrypoint }) =>
          window.__outputRecipe.resolveClientRecipe(keptN, tripId, entrypoint)
        """,
        {"keptN": kept_n, "tripId": trip_id, "entrypoint": entrypoint},
    )


def _force_click(page, selector: str) -> None:
    page.locator(selector).evaluate("el => el.click()")


# ---------------------------------------------------------------------------
# Persona 1 · 极简分享者（1–9）
# ---------------------------------------------------------------------------


def test_persona_sparse_default_cta_wechat_chat(studio_server) -> None:
    """H-A-01 · Sparse 主 CTA「导出长图 · 发微信群」，一次点击路径语义。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _prepare_page(page, studio_server["base"])
        _load_recipe(page, enabled=True)

        for n in (1, 5, 9):
            r = _resolve(page, n)
            assert r["band"] == "sparse"
            assert r["needsIntent"] is False
            assert r["intent"] == "chat_longshot"
            assert r["platform"] == "wechat_chat"
            assert r["ctaLabel"] == "导出长图 · 发微信群"
            assert "九宫格" not in (r["ctaLabel"] or "")

        browser.close()


# ---------------------------------------------------------------------------
# Persona 2 · 周末近郊（10–30）· 意图卡
# ---------------------------------------------------------------------------


def test_persona_ambiguous_preview_needs_intent_card(studio_server) -> None:
    """H-A-02 · Ambiguous 预览首次导出需要意图卡。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _prepare_page(page, studio_server["base"])
        _load_recipe(page, enabled=True)

        r = _resolve(page, 18, entrypoint="preview")
        assert r["band"] == "ambiguous"
        assert r["needsIntent"] is True
        assert r["ctaLabel"] == "选择并导出"
        assert any("精选了 18 张" in h for h in (r["userHints"] or []))

        browser.close()


def test_persona_ambiguous_intent_card_three_options_and_export(studio_server) -> None:
    """H-A-03/04 · H-B-01 · 意图卡含发群 / 九宫格 / 长图连读；选择并导出。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _prepare_page(page, studio_server["base"])
        _load_recipe(page, enabled=True)

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

        intents = page.eval_on_selector_all(
            "[data-output-intent]",
            "els => els.map(e => e.getAttribute('data-output-intent'))",
        )
        assert intents == ["chat_longshot", "moments_grid", "moments_scroll"]

        labels = page.eval_on_selector_all(
            "[data-output-intent] strong",
            "els => els.map(e => e.textContent)",
        )
        assert "微信群 · 长图" in labels
        assert "朋友圈 · 九宫格" in labels
        assert "朋友圈 · 长图连读" in labels

        # USR-02 · 微信群长图为唯一选项 primary
        chat_weight = page.locator('[data-output-intent="chat_longshot"]').get_attribute(
            "data-intent-weight"
        )
        assert chat_weight == "primary"
        assert "推荐" in page.locator('[data-output-intent="chat_longshot"]').inner_text()

        # 选长图连读 → 选择并导出（confirm 按钮带 data-output-recipe-confirm）
        _force_click(page, '[data-output-intent="moments_scroll"]')
        _force_click(page, '[data-output-recipe-confirm="export"]')
        page.wait_for_function("() => window.__intentResult !== null", timeout=5_000)
        result = page.evaluate("() => window.__intentResult")
        assert result == {"intent": "moments_scroll", "exportNow": True}

        browser.close()


def test_persona_ambiguous_grid_label_only_for_moments_grid(studio_server) -> None:
    """AC-OR-11b / H-B-03 · 「九宫格」仅出现在 moments_grid 选项。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _prepare_page(page, studio_server["base"])
        _load_recipe(page, enabled=True)

        page.evaluate(
            "async () => { window.__outputRecipe.showAmbiguousIntentCard(12); }"
        )
        page.wait_for_selector('[data-output-recipe-intent="1"]')

        scroll_html = page.locator('[data-output-intent="moments_scroll"]').inner_html()
        grid_html = page.locator('[data-output-intent="moments_grid"]').inner_html()
        assert "九宫格" not in scroll_html
        assert "长图连读" in scroll_html
        assert "九宫格" in grid_html
        assert "有几张发几张" in grid_html

        _force_click(page, '[data-output-intent="moments_grid"]')
        _force_click(page, '[data-output-recipe-intent="1"] button.studio__btn--ghost.studio__btn--sm')
        page.wait_for_selector('[data-output-recipe-intent="1"]', state="detached")

        # session 未写时 resolve 仍 needsIntent；先写 session 再验 CTA
        page.evaluate(
            """
            () => window.__outputRecipe.writeSessionIntent('amb-grid', 'moments_grid')
            """
        )
        r = _resolve(page, 12, trip_id="amb-grid", entrypoint="preview")
        assert r["intent"] == "moments_grid"
        assert r["platform"] == "moments_grid"
        assert r["ctaLabel"] == "导出朋友圈 · 九宫格"
        assert any("1:1" in h for h in (r["userHints"] or []))

        browser.close()


def test_persona_ambiguous_shelf_fallback_no_intent_card(studio_server) -> None:
    """H-A-06 · Ambiguous 书架无 intent → 发群路径 + 弱提示。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _prepare_page(page, studio_server["base"])
        _load_recipe(page, enabled=True)

        r = _resolve(page, 22, entrypoint="shelf")
        assert r["band"] == "ambiguous"
        assert r["needsIntent"] is False
        assert r["intent"] == "chat_longshot"
        assert r["ctaLabel"] == "导出长图 · 发微信群"
        assert any("预览" in h for h in (r["userHints"] or []))

        browser.close()


# ---------------------------------------------------------------------------
# Persona 3 · 摄影旅行（≥50）
# ---------------------------------------------------------------------------


def test_persona_narrative_deep_chapter_default(studio_server) -> None:
    """H-A-07 · ≥50 按章默认；整卷二次确认钩子存在。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _prepare_page(page, studio_server["base"])
        _load_recipe(page, enabled=True)

        r40 = _resolve(page, 40)
        assert r40["band"] == "narrative"
        assert r40["ctaLabel"] == "按章导出长图 · 发微信群"
        assert r40["needsIntent"] is False

        r55 = _resolve(page, 55)
        assert r55["band"] == "narrative"
        assert any("按章节拆成多张" in h for h in (r55["userHints"] or []))

        need_confirm = page.evaluate(
            """
            () => ({
              full: window.__outputRecipe.needsFullExportConfirm(55, 'full', 'wechat_chat'),
              chapter: window.__outputRecipe.needsFullExportConfirm(55, 'chapter', 'wechat_chat'),
              shallow: window.__outputRecipe.needsFullExportConfirm(40, 'full', 'wechat_chat'),
            })
            """
        )
        assert need_confirm["full"] is True
        assert need_confirm["chapter"] is False
        assert need_confirm["shallow"] is False

        browser.close()


# ---------------------------------------------------------------------------
# Persona 4 · flag 关闭回退
# ---------------------------------------------------------------------------


def test_persona_flag_off_no_intent_card(studio_server) -> None:
    """H-A-08 · flag 关闭：无意图卡语义，回退固定 chat。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _prepare_page(page, studio_server["base"])
        _load_recipe(page, enabled=False)

        r = _resolve(page, 18, entrypoint="preview")
        assert r["needsIntent"] is False
        assert r["intent"] == "chat_longshot"
        assert r["platform"] == "wechat_chat"
        assert r["source"] == "flag_disabled"
        assert r["ctaLabel"] == "导出长图"

        browser.close()


# ---------------------------------------------------------------------------
# Persona 5 · 回访用户 · 首页书架冒烟（非 Recipe 接线）
# ---------------------------------------------------------------------------


def test_persona_returning_user_homepage_shelf_loads(studio_server) -> None:
    """回访用户：书架 fixture 可打开首页，次按钮打开 Import Wizard。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        _prepare_page(page, studio_server["base"], "dev=1&studioFixture=multi")
        _wait_visible(page, "v2-frame")

        body_html = page.content()
        assert "data-homepage-variant" in body_html

        cta = page.locator("#v2-cta").inner_text()
        assert "继续制作《京都" in cta
        page.locator("#v2-cta-secondary").click()
        _wait_visible(page, "v2-wizard-root")
        assert page.locator("#v2-wizard-step-pick").is_visible()

        browser.close()
