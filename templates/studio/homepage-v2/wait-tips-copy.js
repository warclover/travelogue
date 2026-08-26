/**
 * Wait Tips V1 · 冻结文案表（PRD §4 v0.1.3 / 文档包 v0.2.0）
 * 字面为契约源；改文案须同步 PRD + 单测。
 */
export var COPY_VERSION = "0.2.1";

export var DISMISS_KEY = "travelogue.waitTips.dismissed";
export var VERSION_KEY = "travelogue.waitTips.version";

/** @type {{ id: string, category: string, tone: string, label: string, title: string, body: string }[]} */
export var WAIT_TIPS_CARDS = [
  {
    id: "WT-01",
    category: "结果",
    tone: "outcome",
    label: "马上就好",
    title: "可翻的画册，可发的长图",
    body: "先在大屏慢慢看；喜欢了，再存一张发群用的长图。",
  },
  {
    id: "WT-02",
    category: "信任",
    tone: "trust",
    label: "安心",
    title: "回忆，只放在你身边",
    body: "不上传云端，在本机悄悄成册。私密，是画册该有的样子。",
  },
  {
    id: "WT-03",
    category: "能力",
    tone: "capability",
    label: "省心",
    title: "分章配文排版，交给它",
    body: "选好这一趟的照片就行，不用先一张张归类。",
  },
  {
    id: "WT-04",
    category: "下一步",
    tone: "next",
    label: "小提示",
    title: "先看画册，再存长图",
    body: "打开预览慢慢看；满意了，再点「长图」收下。",
  },
  {
    id: "WT-05",
    category: "试用",
    tone: "trial",
    label: "想先试试",
    title: "没有照片？先用示例",
    body: "向导里一键试用，流程和自己的相册一模一样。",
  },
  {
    id: "WT-06",
    category: "试用",
    tone: "trial",
    label: "选片诀窍",
    title: "一本画册，一个文件夹",
    body: "同一次出行放一起就好，不必事先精挑细选。",
  },
];

/**
 * 作品集导入轮播：去掉「配文」口径，且本表不得出现「文案 / 正在写」。
 * 游记六张字面不变（WAIT_TIPS 合同）。
 */
var PORTFOLIO_WAIT_TIP_OVERRIDES = {
  "WT-01": {
    title: "可翻的一本，页图也能带走",
    body: "先在大屏慢慢翻；满意了，再导出这一本或页图。",
  },
  "WT-03": {
    title: "分章排版，交给它",
    body: "选好这一趟的照片就行，不用先一张张归类。",
  },
  "WT-04": {
    title: "先打开这一本，再导出",
    body: "预览里慢慢看；满意了，再点「导出作品集」。",
  },
};

export function waitTipsCardsForEdition(edition) {
  var t = String(edition || "").trim().toLowerCase();
  if (t !== "portfolio" && t !== "folio") return WAIT_TIPS_CARDS;
  return WAIT_TIPS_CARDS.map(function (card) {
    var over = PORTFOLIO_WAIT_TIP_OVERRIDES[card.id];
    if (!over) return card;
    return {
      id: card.id,
      category: card.category,
      tone: card.tone,
      label: card.label,
      title: over.title,
      body: over.body,
    };
  });
}
