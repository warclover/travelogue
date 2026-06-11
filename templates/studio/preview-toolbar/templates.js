/**
 * Preview toolbar · DOM templates (transition · O-5).
 */
"use strict";

export var TOOLBAR_HTML =
  '<div class="preview-toolbar__collapsed-strip">' +
  '<a class="preview-toolbar__back preview-toolbar__back--strip preview-toolbar__ctl" href="/" title="返回 Studio 首页">' +
  '<span class="preview-toolbar__ctl__glyph" aria-hidden="true">←</span>返回</a>' +
  '<div class="preview-toolbar__spacer preview-toolbar__spacer--strip" aria-hidden="true"></div>' +
  '<button type="button" class="preview-toolbar__handle" aria-expanded="false">' +
  '<span class="preview-toolbar__handle-icon" aria-hidden="true">▾</span>' +
  '<span class="preview-toolbar__handle-label">显示工具栏</span>' +
  "</button>" +
  "</div>" +
  '<div class="preview-toolbar__body">' +
  '<div class="preview-toolbar__bar">' +
  '<div class="preview-toolbar__left">' +
  '<a class="preview-toolbar__back preview-toolbar__ctl" href="/" title="返回 Studio 首页">' +
  '<span class="preview-toolbar__ctl__glyph" aria-hidden="true">←</span>返回</a>' +
  '<div class="preview-toolbar__identity">' +
  '<span class="preview-toolbar__trip-title"></span>' +
  '<span class="preview-toolbar__trip-meta"></span>' +
  "</div>" +
  "</div>" +
  '<div class="preview-toolbar__center">' +
  '<div class="preview-toolbar__actions"></div>' +
  "</div>" +
  '<div class="preview-toolbar__right">' +
  '<div class="preview-toolbar__reader-zone">' +
  '<div class="preview-toolbar__export-slot"></div>' +
  "</div>" +
  '<div class="preview-toolbar__edit-zone" hidden>' +
  '<button type="button" class="preview-toolbar__apply-layout-main preview-toolbar__ctl" disabled>应用排版</button>' +
  '<div class="preview-toolbar__edit-tools-wrap">' +
  '<button type="button" class="preview-toolbar__edit-tools-btn preview-toolbar__ctl" aria-haspopup="true" aria-expanded="false">编辑工具 ▾</button>' +
  '<div class="preview-toolbar__edit-tools-menu" hidden role="menu">' +
  '<button type="button" class="preview-toolbar__open-edit" role="menuitem">编辑感受与锚点</button>' +
  '<button type="button" class="preview-toolbar__open-cohort" role="menuitem" hidden>旅行主角 · 同框</button>' +
  '<button type="button" class="preview-toolbar__open-structure" role="menuitem">结构与分章</button>' +
  "</div>" +
  "</div>" +
  "</div>" +
  '<div class="preview-toolbar__cluster">' +
  '<button type="button" class="preview-toolbar__menu-btn preview-toolbar__icon-btn" aria-haspopup="true" aria-expanded="false" aria-label="更多操作" title="更多操作">' +
  '<span class="preview-toolbar__icon-btn__glyph preview-toolbar__icon-btn__glyph--more" aria-hidden="true">⋯</span></button>' +
  '<div class="preview-toolbar__more-menu" hidden role="menu">' +
  '<span class="preview-toolbar__llm-slot" role="none"></span>' +
  '<hr class="preview-toolbar__menu-sep preview-toolbar__menu-sep--after-llm" role="separator" />' +
  '<button type="button" class="preview-toolbar__reveal-folder" role="menuitem">在文件夹中显示</button>' +
  '<button type="button" class="preview-toolbar__export-zip" role="menuitem">导出 zip（自行托管）</button>' +
  '<hr class="preview-toolbar__menu-sep preview-toolbar__menu-sep--before-collapse" role="separator" />' +
  '<button type="button" class="preview-toolbar__more-collapse" role="menuitem">收起工具栏</button>' +
  "</div>" +
  "</div>" +
  '<button type="button" class="preview-toolbar__collapse preview-toolbar__icon-btn" aria-expanded="true" aria-label="收起工具栏">' +
  '<span class="preview-toolbar__icon-btn__glyph" aria-hidden="true">▴</span>' +
  "</button>" +
  "</div>" +
  "</div>" +
  '<div class="preview-toolbar__pending-row" hidden>' +
  '<div class="preview-toolbar__pending-banner">' +
  '<span class="preview-toolbar__pending-text">已暂存修改 · 应用排版后生效</span>' +
  '<div class="preview-toolbar__pending-actions">' +
  '<button type="button" class="preview-toolbar__pending-detail-toggle" hidden>查看明细</button>' +
  '<button type="button" class="preview-toolbar__pending-apply">应用排版</button>' +
  "</div>" +
  "</div>" +
  '<div class="preview-toolbar__pending-detail" hidden></div>' +
  "</div>";

export var SHARE_TOOLBAR_HTML =
  '<div class="preview-toolbar__body">' +
  '<div class="preview-toolbar__bar preview-toolbar__bar--minimal">' +
  '<div class="preview-toolbar__spacer" aria-hidden="true"></div>' +
  '<div class="preview-toolbar__cluster">' +
  '<a class="preview-toolbar__back" href="/" title="返回 Studio 首页">← 返回</a>' +
  "</div>" +
  "</div>" +
  "</div>";
