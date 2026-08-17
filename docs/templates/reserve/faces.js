// 备用库微缩几何 · 与 gallery.html / preview.html 共用。引擎不读。
window.RESERVE_FACES = [
      {
        id: "page-1-hero-land-right",
        displayName: "单图 · 横版英雄 · 右齐",
        badge: "1L",
        blurb: "高光池单横；4:3 右齐；左为剩余文案栏。没字槽仍靠右。",
        related: "兄弟 page-1-hero-land（4:3 居中）· -wide（16:9）· -ultra（21:9）",
        replaces: "意图顶岗 screen-landscape-1（满幅，不是同一张）",
        href: "page-1-hero-land-right/",
        copy: { left: 5, top: 5, width: 22.5, height: 90 },
        slot: { left: 27.5, top: 5, width: 67.5, height: 90 }
      },
      {
        id: "page-1-hero-land-wide",
        displayName: "单图 · 横版英雄 · 16:9",
        badge: "1L",
        blurb: "高光池单横；16:9 槽居中，四周 6.25% 留白，无文案栏。",
        related: "兄弟 page-1-hero-land（4:3 居中）· -right（4:3 右齐）· -ultra（21:9）",
        replaces: "意图顶岗 screen-landscape-1（满幅，不是同一张）",
        href: "page-1-hero-land-wide/",
        slot: { left: 6.25, top: 6.25, width: 87.5, height: 87.5 }
      },
      {
        id: "page-1-hero-square-right",
        displayName: "单图 · 方图英雄 · 右齐",
        badge: "1S",
        blurb: "只进 1:1 方图；方槽按高求解后右齐。左为剩余文案栏，可空。没字槽仍靠右。",
        related: "不同族。同构摆放参见 page-1-hero-land-right",
        replaces: "无合格现网顶岗；不要拿 screen-landscape-1 顶",
        href: "page-1-hero-square-right/",
        copy: { left: 6.25, top: 6.25, width: 38.28125, height: 87.5 },
        slot: { left: 44.53125, top: 6.25, width: 49.21875, height: 87.5 }
      },
      {
        id: "page-1-hero-land-ultra",
        displayName: "单图 · 横版英雄 · 21:9",
        badge: "1L",
        blurb: "超宽风景或合影；21:9 槽按宽求解后顶齐。下为剩余文案栏，可空。",
        related: "兄弟 page-1-hero-land / -right / -wide（槽比不同）",
        replaces: "意图顶岗 screen-panorama-1（文档有、仓库未见 YAML）",
        href: "page-1-hero-land-ultra/",
        copy: { left: 6.25, top: 72.916667, width: 87.5, height: 20.833333 },
        slot: { left: 6.25, top: 6.25, width: 87.5, height: 66.666667 }
      },
      {
        id: "page-1-hero-port",
        displayName: "单图 · 竖版英雄",
        badge: "1P",
        blurb: "高光池单竖；3:4 居中，上下 5% 留白。左右剩余为文案栏，可空。",
        related: "本族第一张。朝向对偶 page-1-hero-land（4:3 居中）",
        replaces: "意图顶岗 screen-portrait-1（满幅 9:16，不是同一张）",
        href: "page-1-hero-port/",
        copies: [
          { left: 5, top: 5, width: 26.015625, height: 90 },
          { left: 68.984375, top: 5, width: 26.015625, height: 90 }
        ],
        slot: { left: 31.015625, top: 5, width: 37.96875, height: 90 }
      },
      {
        id: "page-2-pair-port",
        displayName: "双竖版并排",
        badge: "2P",
        blurb: "高光池双竖；两槽 3:4，上下 5%，左右与间距三等分。无文案栏。",
        related: "同族 page-3-port。附录 A 已有同 id，边距不同",
        replaces: "意图顶岗 screen-portrait-2-gallery（不是同一张）",
        href: "page-2-pair-port/",
        slots: [
          { left: 8.020833, top: 5, width: 37.96875, height: 90 },
          { left: 54.010417, top: 5, width: 37.96875, height: 90 }
        ]
      },
      {
        id: "page-2-1p1l",
        displayName: "左竖右横",
        badge: "1P1L",
        blurb: "左竖 3:4 满高带，右横 4:3 顶齐。右下剩余文案，可空。按槽禁入。",
        related: "兄弟 page-2-1l1p（左横右竖）",
        replaces: "意图顶岗 screen-portrait-1-landscape-1（两槽满高 cover）",
        href: "page-2-1p1l/",
        hasSketch: true,
        copy: { left: 47.96875, top: 67.708333, width: 47.03125, height: 27.291667 },
        slots: [
          { left: 5, top: 5, width: 37.96875, height: 90 },
          { left: 47.96875, top: 5, width: 47.03125, height: 62.708333 }
        ]
      },
      {
        id: "page-2-1l1p",
        displayName: "左横右竖",
        badge: "1L1P",
        blurb: "上一张的镜像：左横 4:3 顶齐，右竖 3:4 满高带。左下剩余文案，可空。",
        related: "兄弟 page-2-1p1l（左竖右横）。无独立示意图",
        replaces: "意图顶岗 screen-landscape-1-portrait-1（两槽满高 cover）",
        href: "page-2-1l1p/",
        hasSketch: false,
        copy: { left: 5, top: 67.708333, width: 47.03125, height: 27.291667 },
        slots: [
          { left: 5, top: 5, width: 47.03125, height: 62.708333 },
          { left: 57.03125, top: 5, width: 37.96875, height: 90 }
        ]
      },
      {
        id: "page-2-pair-land",
        displayName: "双横版并排",
        badge: "2L",
        blurb: "两横槽 4:3 顶齐并排；下为通栏剩余文案，可空。竖版禁入。",
        related: "朝向对偶 page-2-pair-port。现网 screen-landscape-2 是上下叠，不是同一张",
        replaces: "意图顶岗 screen-landscape-2（上下 stack）",
        href: "page-2-pair-land/",
        copy: { left: 5, top: 61.666667, width: 90, height: 33.333333 },
        slots: [
          { left: 5, top: 5, width: 42.5, height: 56.666667 },
          { left: 52.5, top: 5, width: 42.5, height: 56.666667 }
        ]
      },
      {
        id: "page-2-pair-land-ultra",
        displayName: "双超宽叠放",
        badge: "2L",
        blurb: "两超宽条上下均分（64:17，不是 21:9）。左右 5%。竖版禁入。",
        related: "参见 page-2-pair-land（4:3 并排）· page-1-hero-land-ultra（单张 21:9）",
        replaces: "意图顶岗 screen-landscape-2（不是同一张）",
        href: "page-2-pair-land-ultra/",
        slots: [
          { left: 5, top: 5, width: 90, height: 42.5 },
          { left: 5, top: 52.5, width: 90, height: 42.5 }
        ]
      },
      {
        id: "page-3-port",
        displayName: "三竖并排",
        badge: "3P",
        blurb: "三竖槽 3:4 各 30%；余宽 10% 四等分（左右与两缝各 2.5%），整组垂直居中。横版禁入。",
        related: "同族 page-2-pair-port。附录 A 已有同 id，边距不同",
        replaces: "意图顶岗 screen-portrait-3（9:16 满幅，不是同一张）",
        href: "page-3-port/",
        slots: [
          { left: 2.5, top: 14.444444, width: 30, height: 71.111111 },
          { left: 35, top: 14.444444, width: 30, height: 71.111111 },
          { left: 67.5, top: 14.444444, width: 30, height: 71.111111 }
        ]
      },
      {
        id: "page-3-2l1p-left",
        displayName: "左竖右双横",
        badge: "1P2L",
        blurb: "左竖 3:4 满高为主；右两横 4:3 叠满高。按槽禁入。",
        related: "兄弟 page-3-2l1p-right（镜像）",
        replaces: "意图顶岗 screen-portrait-1-landscape-2（不是同一张）",
        href: "page-3-2l1p-left/",
        hasSketch: true,
        slots: [
          { left: 9.625, top: 0, width: 42.1875, height: 100 },
          { left: 53.8125, top: 0, width: 36.5625, height: 48.75 },
          { left: 53.8125, top: 51.25, width: 36.5625, height: 48.75 }
        ]
      },
      {
        id: "page-3-2l1p-right",
        displayName: "左双横右竖",
        badge: "2L1P",
        blurb: "上一张的镜像：左两横 4:3 叠满高，右竖 3:4 满高。",
        related: "兄弟 page-3-2l1p-left。无独立示意图",
        replaces: "意图顶岗 screen-landscape-2-portrait-1（不是同一张）",
        href: "page-3-2l1p-right/",
        hasSketch: false,
        slots: [
          { left: 9.625, top: 0, width: 36.5625, height: 48.75 },
          { left: 9.625, top: 51.25, width: 36.5625, height: 48.75 },
          { left: 48.1875, top: 0, width: 42.1875, height: 100 }
        ]
      },
      {
        id: "page-2-pair-square",
        displayName: "双方图并排",
        badge: "2S",
        blurb: "两方槽 1:1 各 40%；余宽 20% 三等分（左右与中缝各 1/15），垂直居中。优先方图，4:3/3:4 可进。",
        related: "参见 page-1-hero-square-right（单方图，只进 1:1）",
        replaces: "无合格现网顶岗",
        href: "page-2-pair-square/",
        slots: [
          { left: 6.666667, top: 14.444444, width: 40, height: 71.111111 },
          { left: 53.333333, top: 14.444444, width: 40, height: 71.111111 }
        ]
      },
      {
        id: "page-3-1s2l-left",
        displayName: "左方右双横",
        badge: "1S2L",
        blurb: "左主 1:1 半宽；右两横 4:3（各 25% 宽）上下均分。表头写 2 槽，按图是 3 槽。",
        related: "兄弟 page-3-1s2l-right（镜像）",
        replaces: "无合格现网顶岗",
        href: "page-3-1s2l-left/",
        hasSketch: true,
        slots: [
          { left: 0, top: 5.555556, width: 50, height: 88.888889 },
          { left: 62.5, top: 11.111111, width: 25, height: 33.333333 },
          { left: 62.5, top: 55.555556, width: 25, height: 33.333333 }
        ]
      },
      {
        id: "page-3-1s2l-right",
        displayName: "左双横右方",
        badge: "2L1S",
        blurb: "上一张的镜像：左两横 4:3，右主 1:1 半宽。",
        related: "兄弟 page-3-1s2l-left。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-3-1s2l-right/",
        hasSketch: false,
        slots: [
          { left: 12.5, top: 11.111111, width: 25, height: 33.333333 },
          { left: 12.5, top: 55.555556, width: 25, height: 33.333333 },
          { left: 50, top: 5.555556, width: 50, height: 88.888889 }
        ]
      },
      {
        id: "page-2-1s1p",
        displayName: "左方右竖",
        badge: "1S1P",
        blurb: "左主 1:1 半宽居中高；右竖 3:4 占页宽 25%，在右侧 50% 里居中。竖槽禁横。",
        related: "兄弟 page-2-1p1s（镜像）",
        replaces: "无合格现网顶岗",
        href: "page-2-1s1p/",
        hasSketch: true,
        slots: [
          { left: 0, top: 5.555556, width: 50, height: 88.888889 },
          { left: 62.5, top: 20.370370, width: 25, height: 59.259259 }
        ]
      },
      {
        id: "page-2-1p1s",
        displayName: "左竖右方",
        badge: "1P1S",
        blurb: "上一张的镜像：左竖 3:4 占页宽 25%，右主 1:1 半宽。",
        related: "兄弟 page-2-1s1p。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-2-1p1s/",
        hasSketch: false,
        slots: [
          { left: 12.5, top: 20.370370, width: 25, height: 59.259259 },
          { left: 50, top: 5.555556, width: 50, height: 88.888889 }
        ]
      },
      {
        id: "page-2-1l1p-wide",
        displayName: "左宽右竖",
        badge: "1L1P",
        blurb: "左主 16:9 占页宽 60%；右竖 3:4 占页宽 25%；左右与间距各 5%。按槽禁入。与 4:3 的 page-2-1l1p 不是同一张。",
        related: "兄弟 page-2-1p1l-wide（镜像）",
        replaces: "无合格现网顶岗",
        href: "page-2-1l1p-wide/",
        hasSketch: true,
        slots: [
          { left: 5, top: 20, width: 60, height: 60 },
          { left: 70, top: 20.370370, width: 25, height: 59.259259 }
        ]
      },
      {
        id: "page-2-1p1l-wide",
        displayName: "左竖右宽",
        badge: "1P1L",
        blurb: "上一张的镜像：左竖 3:4 占页宽 25%，右主 16:9 占页宽 60%。",
        related: "兄弟 page-2-1l1p-wide。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-2-1p1l-wide/",
        hasSketch: false,
        slots: [
          { left: 5, top: 20.370370, width: 25, height: 59.259259 },
          { left: 35, top: 20, width: 60, height: 60 }
        ]
      },
      {
        id: "page-3-land",
        displayName: "三横并排",
        badge: "3L",
        blurb: "三横槽 4:3 各 30%；余宽 10% 四等分（左右与两缝各 2.5%）。顶底通栏文案，可空。竖版禁入。现网三横是上下叠，不是同一张。",
        related: "同族 page-2-pair-land。朝向对偶 page-3-port",
        replaces: "意图顶岗 screen-landscape-3（上下 stack）",
        href: "page-3-land/",
        hasSketch: true,
        copies: [
          { left: 2.5, top: 0, width: 95, height: 30 },
          { left: 2.5, top: 70, width: 95, height: 30 }
        ],
        slots: [
          { left: 2.5, top: 30, width: 30, height: 40 },
          { left: 35, top: 30, width: 30, height: 40 },
          { left: 67.5, top: 30, width: 30, height: 40 }
        ]
      },
      {
        id: "page-3-port-hero-left",
        displayName: "左大右双小",
        badge: "3P",
        blurb: "左主 3:4 上下 5%；右两辅 3:4 扣 5% 中缝后均分剩余宽，垂直居中。横版禁入。与等权三竖 page-3-port 不是同一张。",
        related: "兄弟 page-3-port-hero-right（镜像）",
        replaces: "无合格现网顶岗",
        href: "page-3-port-hero-left/",
        hasSketch: true,
        slots: [
          { left: 5, top: 5, width: 37.96875, height: 90 },
          { left: 47.96875, top: 25.092593, width: 21.015625, height: 49.814815 },
          { left: 73.984375, top: 25.092593, width: 21.015625, height: 49.814815 }
        ]
      },
      {
        id: "page-3-port-hero-right",
        displayName: "左双小右大",
        badge: "3P",
        blurb: "上一张的镜像：左两辅 3:4 扣 5% 中缝后均分，右主 3:4 上下 5%。",
        related: "兄弟 page-3-port-hero-left。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-3-port-hero-right/",
        hasSketch: false,
        slots: [
          { left: 5, top: 25.092593, width: 21.015625, height: 49.814815 },
          { left: 31.015625, top: 25.092593, width: 21.015625, height: 49.814815 },
          { left: 57.03125, top: 5, width: 37.96875, height: 90 }
        ]
      },
      {
        id: "page-3-2l1p-hero-left",
        displayName: "左主横右上横下竖",
        badge: "2L1P",
        blurb: "左主 4:3 占页宽 71%；右上横 4:3、右下竖 3:4 各占 25%；列缝 4%。按槽禁入。与竖主的 page-3-2l1p-left 不是同一张。",
        related: "兄弟 page-3-2l1p-hero-right（镜像）",
        replaces: "无合格现网顶岗",
        href: "page-3-2l1p-hero-left/",
        hasSketch: true,
        slots: [
          { left: 0, top: 2.666667, width: 71, height: 94.666667 },
          { left: 75, top: 2.666667, width: 25, height: 33.333333 },
          { left: 75, top: 38.074074, width: 25, height: 59.259259 }
        ]
      },
      {
        id: "page-3-2l1p-hero-right",
        displayName: "左上横下竖右主横",
        badge: "1P2L",
        blurb: "上一张的镜像：左上横 4:3、左下竖 3:4，右主 4:3 占页宽 71%。栏内仍是上横下竖。",
        related: "兄弟 page-3-2l1p-hero-left。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-3-2l1p-hero-right/",
        hasSketch: false,
        slots: [
          { left: 0, top: 2.666667, width: 25, height: 33.333333 },
          { left: 0, top: 38.074074, width: 25, height: 59.259259 },
          { left: 29, top: 2.666667, width: 71, height: 94.666667 }
        ]
      },
      {
        id: "page-3-2l1p-hero-wide-left",
        displayName: "左主宽横右上宽横下竖",
        badge: "2L1P",
        blurb: "由 page-3-2l1p-hero-left 改槽比：两横 16:9。主宽仍 71% 上下居中，右栏宽仍 25%。右栏余高三等分。按槽禁入。与竖主的 page-3-2l1p-wide-left 不是同一张。",
        related: "兄弟 page-3-2l1p-hero-wide-right（镜像）· page-3-2l1p-hero-left（两横 4:3）。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-3-2l1p-hero-wide-left/",
        hasSketch: false,
        slots: [
          { left: 0, top: 14.5, width: 71, height: 71 },
          { left: 75, top: 5.246914, width: 25, height: 25 },
          { left: 75, top: 35.493827, width: 25, height: 59.259259 }
        ]
      },
      {
        id: "page-3-2l1p-hero-wide-right",
        displayName: "左上宽横下竖右主宽横",
        badge: "1P2L",
        blurb: "上一张的镜像：左上横 16:9、左下竖 3:4，右主 16:9 占页宽 71%。栏内仍是上横下竖。",
        related: "兄弟 page-3-2l1p-hero-wide-left。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-3-2l1p-hero-wide-right/",
        hasSketch: false,
        slots: [
          { left: 0, top: 5.246914, width: 25, height: 25 },
          { left: 0, top: 35.493827, width: 25, height: 59.259259 },
          { left: 29, top: 14.5, width: 71, height: 71 }
        ]
      },
      {
        id: "page-4-grid-land",
        displayName: "横版四宫",
        badge: "4L",
        blurb: "2×2 横槽 4:3；单槽高 4/9，剩余宽高各自三等分。竖版禁入。用途栏写三张，按图是四槽。与附录 A 同 id、边距不同。",
        related: "同族 page-2-pair-land · page-3-land",
        replaces: "意图顶岗 screen-landscape-4（偏满幅）",
        href: "page-4-grid-land/",
        hasSketch: true,
        slots: [
          { left: 11.111111, top: 3.703704, width: 33.333333, height: 44.444444 },
          { left: 55.555556, top: 3.703704, width: 33.333333, height: 44.444444 },
          { left: 11.111111, top: 51.851852, width: 33.333333, height: 44.444444 },
          { left: 55.555556, top: 51.851852, width: 33.333333, height: 44.444444 }
        ]
      },
      {
        id: "page-4-1p3l-left",
        displayName: "左竖右三横",
        badge: "1P3L",
        blurb: "左竖 3:4 高 8/9；右上两横各 3/16、右下横 7/16。两列等高。按槽禁入。",
        related: "兄弟 page-4-1p3l-right（镜像）",
        replaces: "无合格现网顶岗",
        href: "page-4-1p3l-left/",
        hasSketch: true,
        slots: [
          { left: 6.25, top: 5.555556, width: 37.5, height: 88.888889 },
          { left: 50, top: 5.555556, width: 18.75, height: 25 },
          { left: 75, top: 5.555556, width: 18.75, height: 25 },
          { left: 50, top: 36.111111, width: 43.75, height: 58.333333 }
        ]
      },
      {
        id: "page-4-1p3l-right",
        displayName: "左三横右竖",
        badge: "3L1P",
        blurb: "上一张的镜像：左上两横各 3/16、左下横 7/16，右竖 3:4 高 8/9。栏内仍是上二下一。",
        related: "兄弟 page-4-1p3l-left。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-4-1p3l-right/",
        hasSketch: false,
        slots: [
          { left: 6.25, top: 5.555556, width: 18.75, height: 25 },
          { left: 31.25, top: 5.555556, width: 18.75, height: 25 },
          { left: 6.25, top: 36.111111, width: 43.75, height: 58.333333 },
          { left: 56.25, top: 5.555556, width: 37.5, height: 88.888889 }
        ]
      },
      {
        id: "page-3-2p1s",
        displayName: "两竖夹一方",
        badge: "2P1S",
        blurb: "左右竖 3:4、中方 1:1，三槽同高 6/9，垂直居中。竖槽禁横。表头写竖 1，按图是 2 竖 + 1 方。",
        related: "参见 page-3-port（等权三竖）· page-2-1s1p（一方一竖）",
        replaces: "无合格现网顶岗",
        href: "page-3-2p1s/",
        hasSketch: true,
        slots: [
          { left: 1.5625, top: 16.666667, width: 28.125, height: 66.666667 },
          { left: 31.25, top: 16.666667, width: 37.5, height: 66.666667 },
          { left: 70.3125, top: 16.666667, width: 28.125, height: 66.666667 }
        ]
      },
      {
        id: "page-4-2p2l-cross",
        displayName: "十字两横两竖",
        badge: "2P2L",
        blurb: "左右竖 3:4 高 5/9，中上下横 4:3 宽 5/16。中列比竖槽高，不顶齐。竖禁横、横禁竖。表头写 2 方版，按图是 2 横。",
        related: "参见 page-4-grid-land（四横宫）· page-3-2p1s（两竖夹一方）。不是附录 A 的 page-4-2p2l 棋盘",
        replaces: "意图顶岗 screen-mosaic-4-2p2l-portrait-bookends（满高书挡，不是同一张）",
        href: "page-4-2p2l-cross/",
        hasSketch: true,
        slots: [
          { left: 5.46875, top: 22.222222, width: 23.4375, height: 55.555556 },
          { left: 34.375, top: 5.555556, width: 31.25, height: 41.666667 },
          { left: 34.375, top: 52.777778, width: 31.25, height: 41.666667 },
          { left: 71.09375, top: 22.222222, width: 23.4375, height: 55.555556 }
        ]
      },
      {
        id: "page-4-grid-land-wide",
        displayName: "宽版横版四宫",
        badge: "4L",
        blurb: "2×2 横槽 16:9；单槽宽 7/16，剩余宽高各自三等分。竖版禁入。不是 4:3 的 page-4-grid-land。",
        related: "同族 page-4-grid-land（4:3 四宫）· page-1-hero-land-wide（单张 16:9）",
        replaces: "意图顶岗 screen-landscape-4（偏满幅，不是同一张）",
        href: "page-4-grid-land-wide/",
        hasSketch: true,
        slots: [
          { left: 4.166667, top: 4.166667, width: 43.75, height: 43.75 },
          { left: 52.083333, top: 4.166667, width: 43.75, height: 43.75 },
          { left: 4.166667, top: 52.083333, width: 43.75, height: 43.75 },
          { left: 52.083333, top: 52.083333, width: 43.75, height: 43.75 }
        ]
      },
      {
        id: "page-3-2l1p-wide-left",
        displayName: "左竖右双宽横",
        badge: "1P2L",
        blurb: "左竖 3:4 满高；右两横 16:9 叠满高。剩余宽三等分。按槽禁入。不是 4:3 的 page-3-2l1p-left。",
        related: "兄弟 page-3-2l1p-wide-right（镜像）· page-3-2l1p-left（4:3 右栏）。无独立示意图",
        replaces: "意图顶岗 screen-portrait-1-landscape-2（不是同一张）",
        href: "page-3-2l1p-wide-left/",
        hasSketch: false,
        slots: [
          { left: 3.020833, top: 0, width: 42.1875, height: 100 },
          { left: 48.229167, top: 0, width: 48.75, height: 48.75 },
          { left: 48.229167, top: 51.25, width: 48.75, height: 48.75 }
        ]
      },
      {
        id: "page-3-2l1p-wide-right",
        displayName: "左双宽横右竖",
        badge: "2L1P",
        blurb: "上一张的镜像：左两横 16:9 叠满高，右竖 3:4 满高。",
        related: "兄弟 page-3-2l1p-wide-left。无独立示意图",
        replaces: "意图顶岗 screen-landscape-2-portrait-1（不是同一张）",
        href: "page-3-2l1p-wide-right/",
        hasSketch: false,
        slots: [
          { left: 3.020833, top: 0, width: 48.75, height: 48.75 },
          { left: 3.020833, top: 51.25, width: 48.75, height: 48.75 },
          { left: 54.791667, top: 0, width: 42.1875, height: 100 }
        ]
      },
      {
        id: "page-3-1s2l-wide-left",
        displayName: "左方右双宽横",
        badge: "1S2L",
        blurb: "左主 1:1 半宽贴左；右两横 16:9 各 1/3 宽，在右半宽内居中。不是 4:3 的 page-3-1s2l-left。",
        related: "兄弟 page-3-1s2l-wide-right（镜像）· page-3-1s2l-left（4:3 右栏）。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-3-1s2l-wide-left/",
        hasSketch: false,
        slots: [
          { left: 0, top: 5.555556, width: 50, height: 88.888889 },
          { left: 58.333333, top: 11.111111, width: 33.333333, height: 33.333333 },
          { left: 58.333333, top: 55.555556, width: 33.333333, height: 33.333333 }
        ]
      },
      {
        id: "page-3-1s2l-wide-right",
        displayName: "左双宽横右方",
        badge: "2L1S",
        blurb: "上一张的镜像：左两横 16:9 各 1/3 宽，右主 1:1 半宽。",
        related: "兄弟 page-3-1s2l-wide-left。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-3-1s2l-wide-right/",
        hasSketch: false,
        slots: [
          { left: 8.333333, top: 11.111111, width: 33.333333, height: 33.333333 },
          { left: 8.333333, top: 55.555556, width: 33.333333, height: 33.333333 },
          { left: 50, top: 5.555556, width: 50, height: 88.888889 }
        ]
      },
      {
        id: "page-4-1l3l-left",
        displayName: "左主横右三小",
        badge: "1L3L",
        blurb: "左主 4:3 半宽；右三横 4:3 各 22%。剩余宽三等分。右栏比主图高，不顶齐。竖版禁入。用途栏只写主图一张，按图是四槽。",
        related: "兄弟 page-4-1l3l-right（镜像）。不是附录 A 的 page-4-hero-rail（约 70% 侧栏）",
        replaces: "意图顶岗 screen-mosaic-4-hero-70-sidebar（不是同一张）",
        href: "page-4-1l3l-left/",
        hasSketch: true,
        slots: [
          { left: 9.333333, top: 16.666667, width: 50, height: 66.666667 },
          { left: 68.666667, top: 3, width: 22, height: 29.333333 },
          { left: 68.666667, top: 35.333333, width: 22, height: 29.333333 },
          { left: 68.666667, top: 67.666667, width: 22, height: 29.333333 }
        ]
      },
      {
        id: "page-4-1l3l-right",
        displayName: "左三小右主横",
        badge: "3L1L",
        blurb: "上一张的镜像：左三横 4:3 各 22%，右主 4:3 半宽。",
        related: "兄弟 page-4-1l3l-left。无独立示意图",
        replaces: "意图顶岗 screen-mosaic-4-hero-70-sidebar（不是同一张）",
        href: "page-4-1l3l-right/",
        hasSketch: false,
        slots: [
          { left: 9.333333, top: 3, width: 22, height: 29.333333 },
          { left: 9.333333, top: 35.333333, width: 22, height: 29.333333 },
          { left: 9.333333, top: 67.666667, width: 22, height: 29.333333 },
          { left: 40.666667, top: 16.666667, width: 50, height: 66.666667 }
        ]
      },
      {
        id: "page-4-1l3l-wide-left",
        displayName: "左主宽横右三小",
        badge: "1L3L",
        blurb: "左主 16:9 半宽；右三横 16:9 各 25%。剩余宽三等分。右栏比主图高，不顶齐。竖版禁入。不是 4:3 的 page-4-1l3l-left。",
        related: "兄弟 page-4-1l3l-wide-right（镜像）· page-4-1l3l-left（4:3）",
        replaces: "意图顶岗 screen-mosaic-4-hero-70-sidebar（不是同一张）",
        href: "page-4-1l3l-wide-left/",
        hasSketch: true,
        slots: [
          { left: 8.333333, top: 25, width: 50, height: 50 },
          { left: 66.666667, top: 6.25, width: 25, height: 25 },
          { left: 66.666667, top: 37.5, width: 25, height: 25 },
          { left: 66.666667, top: 68.75, width: 25, height: 25 }
        ]
      },
      {
        id: "page-4-1l3l-wide-right",
        displayName: "左三小右主宽横",
        badge: "3L1L",
        blurb: "上一张的镜像：左三横 16:9 各 25%，右主 16:9 半宽。",
        related: "兄弟 page-4-1l3l-wide-left。无独立示意图",
        replaces: "意图顶岗 screen-mosaic-4-hero-70-sidebar（不是同一张）",
        href: "page-4-1l3l-wide-right/",
        hasSketch: false,
        slots: [
          { left: 8.333333, top: 6.25, width: 25, height: 25 },
          { left: 8.333333, top: 37.5, width: 25, height: 25 },
          { left: 8.333333, top: 68.75, width: 25, height: 25 },
          { left: 41.666667, top: 25, width: 50, height: 50 }
        ]
      },
      {
        id: "page-4-port",
        displayName: "四竖并排",
        badge: "4P",
        blurb: "四竖槽 3:4 各 21.875%，顶 5%；余宽 12.5% 五等分（左右与三缝各 2.5%）。下为通栏剩余文案，可空。横版禁入。左右对称，无镜像。",
        related: "同族 page-3-port · page-2-pair-port。不是 2×2 的 grid-4-port",
        replaces: "意图顶岗 screen-portrait-4（9:16 四竖 2×2，不是同一张）",
        href: "page-4-port/",
        hasSketch: true,
        copy: { left: 2.5, top: 56.851852, width: 95, height: 43.148148 },
        slots: [
          { left: 2.5, top: 5, width: 21.875, height: 51.851852 },
          { left: 26.875, top: 5, width: 21.875, height: 51.851852 },
          { left: 51.25, top: 5, width: 21.875, height: 51.851852 },
          { left: 75.625, top: 5, width: 21.875, height: 51.851852 }
        ]
      },
      {
        id: "page-5-1p4l-left",
        displayName: "左竖右四横",
        badge: "1P4L",
        blurb: "左竖 3:4 高 8/9；右 2×2 横 4:3 各 25%，上下与竖槽齐，行缝吃剩余。按槽禁入。",
        related: "兄弟 page-5-1p4l-right（镜像）· page-4-1p3l-left（右三横）",
        replaces: "意图顶岗 screen-mosaic-5-1p4l-portrait-hero（满高+四扁轨，不是同一张）",
        href: "page-5-1p4l-left/",
        hasSketch: true,
        slots: [
          { left: 3.125, top: 5.555556, width: 37.5, height: 88.888889 },
          { left: 43.75, top: 5.555556, width: 25, height: 33.333333 },
          { left: 71.875, top: 5.555556, width: 25, height: 33.333333 },
          { left: 43.75, top: 61.111111, width: 25, height: 33.333333 },
          { left: 71.875, top: 61.111111, width: 25, height: 33.333333 }
        ]
      },
      {
        id: "page-5-1p4l-right",
        displayName: "左四横右竖",
        badge: "4L1P",
        blurb: "上一张的镜像：左 2×2 横 4:3 各 25%，右竖 3:4 高 8/9。",
        related: "兄弟 page-5-1p4l-left。无独立示意图",
        replaces: "意图顶岗 screen-mosaic-5-1p4l-portrait-hero（满高+四扁轨，不是同一张）",
        href: "page-5-1p4l-right/",
        hasSketch: false,
        slots: [
          { left: 3.125, top: 5.555556, width: 25, height: 33.333333 },
          { left: 31.25, top: 5.555556, width: 25, height: 33.333333 },
          { left: 3.125, top: 61.111111, width: 25, height: 33.333333 },
          { left: 31.25, top: 61.111111, width: 25, height: 33.333333 },
          { left: 59.375, top: 5.555556, width: 37.5, height: 88.888889 }
        ]
      },
      {
        id: "page-5-1p4p-left",
        displayName: "左大竖右四小竖",
        badge: "1P4P",
        blurb: "左主 3:4 高 25/27；右 2×2 小竖 3:4 各宽 18.75%。顶/行缝/底各 1/27；三组余宽四等分。横版禁入。与右四横的 page-5-1p4l-left 不是同一张。",
        related: "兄弟 page-5-1p4p-right（镜像）· page-5-1p4l-left（右四横）",
        replaces: "无合格现网顶岗",
        href: "page-5-1p4p-left/",
        hasSketch: true,
        slots: [
          { left: 5.859375, top: 3.703704, width: 39.0625, height: 92.592593 },
          { left: 50.78125, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 75.390625, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 50.78125, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 75.390625, top: 51.851852, width: 18.75, height: 44.444444 }
        ]
      },
      {
        id: "page-5-1p4p-right",
        displayName: "左四小竖右大竖",
        badge: "4P1P",
        blurb: "上一张的镜像：左 2×2 小竖 3:4 各宽 18.75%，右主 3:4 高 25/27。",
        related: "兄弟 page-5-1p4p-left。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-5-1p4p-right/",
        hasSketch: false,
        slots: [
          { left: 5.859375, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 30.46875, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 5.859375, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 30.46875, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 55.078125, top: 3.703704, width: 39.0625, height: 92.592593 }
        ]
      },
      {
        id: "page-4-2p2p",
        displayName: "两大夹两小竖",
        badge: "2P2P",
        blurb: "左右主 3:4 高 25/27；中两小 3:4 各宽 18.75%。大/小尺寸同 page-5-1p4p-left。三组余宽四等分（缝约 0.78%）。横版禁入。左右对称，无镜像。",
        related: "同族 page-5-1p4p-left（同尺寸，左大右四小）· page-4-port（等权四竖）",
        replaces: "无合格现网顶岗；不是 page-4-2p2l-cross",
        href: "page-4-2p2p/",
        hasSketch: true,
        slots: [
          { left: 0.78125, top: 3.703704, width: 39.0625, height: 92.592593 },
          { left: 40.625, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 40.625, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 60.15625, top: 3.703704, width: 39.0625, height: 92.592593 }
        ]
      },
      {
        id: "page-7-1p6l-left",
        displayName: "左竖右六横",
        badge: "1P6L",
        blurb: "左竖 3:4 高 8/9；右 2×3 横 16:9 各 25%，上下与竖槽齐，两行缝均分剩余。按槽禁入。",
        related: "兄弟 page-7-1p6l-right（镜像）· page-5-1p4l-left（右四横 4:3）",
        replaces: "无合格现网顶岗",
        href: "page-7-1p6l-left/",
        hasSketch: true,
        slots: [
          { left: 3.125, top: 5.555556, width: 37.5, height: 88.888889 },
          { left: 43.75, top: 5.555556, width: 25, height: 25 },
          { left: 71.875, top: 5.555556, width: 25, height: 25 },
          { left: 43.75, top: 37.5, width: 25, height: 25 },
          { left: 71.875, top: 37.5, width: 25, height: 25 },
          { left: 43.75, top: 69.444444, width: 25, height: 25 },
          { left: 71.875, top: 69.444444, width: 25, height: 25 }
        ]
      },
      {
        id: "page-7-1p6l-right",
        displayName: "左六横右竖",
        badge: "6L1P",
        blurb: "上一张的镜像：左 2×3 横 16:9 各 25%，右竖 3:4 高 8/9。",
        related: "兄弟 page-7-1p6l-left。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-7-1p6l-right/",
        hasSketch: false,
        slots: [
          { left: 3.125, top: 5.555556, width: 25, height: 25 },
          { left: 31.25, top: 5.555556, width: 25, height: 25 },
          { left: 3.125, top: 37.5, width: 25, height: 25 },
          { left: 31.25, top: 37.5, width: 25, height: 25 },
          { left: 3.125, top: 69.444444, width: 25, height: 25 },
          { left: 31.25, top: 69.444444, width: 25, height: 25 },
          { left: 59.375, top: 5.555556, width: 37.5, height: 88.888889 }
        ]
      },
      {
        id: "page-5-3p2l-left",
        displayName: "左大竖右交错",
        badge: "3P2L",
        blurb: "左大竖 3:4 高 8/9；中上 16:9 下 3:4；右上 3:4 下 16:9。侧列各 25%，上下与大竖齐。用途写 1 竖 6 横，按图是 3 竖 2 横。",
        related: "兄弟 page-5-3p2l-right（镜像）· page-5-1p4l-left（右四横）",
        replaces: "意图顶岗 screen-mosaic-5-2p3l-portrait-hero-rail（不是同一张）",
        href: "page-5-3p2l-left/",
        hasSketch: true,
        slots: [
          { left: 3.125, top: 5.555556, width: 37.5, height: 88.888889 },
          { left: 43.75, top: 5.555556, width: 25, height: 25 },
          { left: 43.75, top: 35.185185, width: 25, height: 59.259259 },
          { left: 71.875, top: 5.555556, width: 25, height: 59.259259 },
          { left: 71.875, top: 69.444444, width: 25, height: 25 }
        ]
      },
      {
        id: "page-5-3p2l-right",
        displayName: "左交错右大竖",
        badge: "2L3P",
        blurb: "上一张的镜像：左上 3:4 下 16:9；中上 16:9 下 3:4；右大竖 3:4 高 8/9。",
        related: "兄弟 page-5-3p2l-left。无独立示意图",
        replaces: "意图顶岗 screen-mosaic-5-2p3l-portrait-hero-rail（不是同一张）",
        href: "page-5-3p2l-right/",
        hasSketch: false,
        slots: [
          { left: 3.125, top: 5.555556, width: 25, height: 59.259259 },
          { left: 3.125, top: 69.444444, width: 25, height: 25 },
          { left: 31.25, top: 5.555556, width: 25, height: 25 },
          { left: 31.25, top: 35.185185, width: 25, height: 59.259259 },
          { left: 59.375, top: 5.555556, width: 37.5, height: 88.888889 }
        ]
      },
      {
        id: "page-5-3p2l-stack-left",
        displayName: "左大竖右上二竖下二横",
        badge: "3P2L",
        blurb: "左大竖 3:4 高 8/9；右两列皆上 3:4 下 16:9，各 25%。用途栏数量有笔误，按图是 3 竖 2 横。不是交错的 page-5-3p2l-left。",
        related: "兄弟 page-5-3p2l-stack-right（镜像）· page-5-3p2l-left（交错）",
        replaces: "意图顶岗 screen-mosaic-5-2p3l-portrait-hero-rail（不是同一张）",
        href: "page-5-3p2l-stack-left/",
        hasSketch: true,
        slots: [
          { left: 3.125, top: 5.555556, width: 37.5, height: 88.888889 },
          { left: 43.75, top: 5.555556, width: 25, height: 59.259259 },
          { left: 43.75, top: 69.444444, width: 25, height: 25 },
          { left: 71.875, top: 5.555556, width: 25, height: 59.259259 },
          { left: 71.875, top: 69.444444, width: 25, height: 25 }
        ]
      },
      {
        id: "page-5-3p2l-stack-right",
        displayName: "左上二竖下二横右大竖",
        badge: "2L3P",
        blurb: "上一张的镜像：左两列皆上 3:4 下 16:9；右大竖 3:4 高 8/9。",
        related: "兄弟 page-5-3p2l-stack-left。无独立示意图",
        replaces: "意图顶岗 screen-mosaic-5-2p3l-portrait-hero-rail（不是同一张）",
        href: "page-5-3p2l-stack-right/",
        hasSketch: false,
        slots: [
          { left: 3.125, top: 5.555556, width: 25, height: 59.259259 },
          { left: 3.125, top: 69.444444, width: 25, height: 25 },
          { left: 31.25, top: 5.555556, width: 25, height: 59.259259 },
          { left: 31.25, top: 69.444444, width: 25, height: 25 },
          { left: 59.375, top: 5.555556, width: 37.5, height: 88.888889 }
        ]
      },
      {
        id: "page-5-3p2l-center",
        displayName: "中大竖左上竖右上横",
        badge: "3P2L",
        blurb: "中大竖 3:4 高 8/9；左上 3:4 下 16:9；右上 16:9 下 3:4。侧列各 25%，上下与大竖齐。不是靠左大竖的 page-5-3p2l-left。",
        related: "兄弟 page-5-3p2l-center-flip（镜像）· page-5-3p2l-left（大竖靠左）",
        replaces: "意图顶岗 screen-mosaic-5-2p3l-portrait-hero-rail（不是同一张）",
        href: "page-5-3p2l-center/",
        hasSketch: true,
        slots: [
          { left: 3.125, top: 5.555556, width: 25, height: 59.259259 },
          { left: 3.125, top: 69.444444, width: 25, height: 25 },
          { left: 31.25, top: 5.555556, width: 37.5, height: 88.888889 },
          { left: 71.875, top: 5.555556, width: 25, height: 25 },
          { left: 71.875, top: 35.185185, width: 25, height: 59.259259 }
        ]
      },
      {
        id: "page-5-3p2l-center-flip",
        displayName: "中大竖左上横右上竖",
        badge: "2L3P",
        blurb: "上一张的镜像：中大竖不动；左上 16:9 下 3:4；右上 3:4 下 16:9。无独立示意图。",
        related: "兄弟 page-5-3p2l-center。无独立示意图",
        replaces: "意图顶岗 screen-mosaic-5-2p3l-portrait-hero-rail（不是同一张）",
        href: "page-5-3p2l-center-flip/",
        hasSketch: false,
        slots: [
          { left: 3.125, top: 5.555556, width: 25, height: 25 },
          { left: 3.125, top: 35.185185, width: 25, height: 59.259259 },
          { left: 31.25, top: 5.555556, width: 37.5, height: 88.888889 },
          { left: 71.875, top: 5.555556, width: 25, height: 59.259259 },
          { left: 71.875, top: 69.444444, width: 25, height: 25 }
        ]
      },
      {
        id: "page-9-grid-land-wide",
        displayName: "宽幅九宫格",
        badge: "9L",
        blurb: "3×3 横槽 16:9；单槽高 30%，宽同 30%。剩余宽高各 10%，各自四等分。竖版禁入。左右对称，无镜像。",
        related: "同族 page-4-grid-land-wide（2×2 宽横）· page-3-land（三横一行）",
        replaces: "意图顶岗 screen-landscape-9（文档已 deprecated，边距未必同本稿）",
        href: "page-9-grid-land-wide/",
        hasSketch: true,
        slots: [
          { left: 2.5, top: 2.5, width: 30, height: 30 },
          { left: 35, top: 2.5, width: 30, height: 30 },
          { left: 67.5, top: 2.5, width: 30, height: 30 },
          { left: 2.5, top: 35, width: 30, height: 30 },
          { left: 35, top: 35, width: 30, height: 30 },
          { left: 67.5, top: 35, width: 30, height: 30 },
          { left: 2.5, top: 67.5, width: 30, height: 30 },
          { left: 35, top: 67.5, width: 30, height: 30 },
          { left: 67.5, top: 67.5, width: 30, height: 30 }
        ]
      },
      {
        id: "page-6-grid-land",
        displayName: "横版六宫格",
        badge: "6L",
        blurb: "3×2 横槽 4:3；单槽宽 31%。剩余宽四等分、剩余高三等分。竖版禁入。不是现网等分的 screen-landscape-6。左右对称，无镜像。",
        related: "同族 page-4-grid-land（2×2）· page-3-land · page-9-grid-land-wide（3×3 宽横）",
        replaces: "意图顶岗 screen-landscape-6（3×2 等分，槽比约 1.185，不是同一张）",
        href: "page-6-grid-land/",
        hasSketch: true,
        slots: [
          { left: 1.75, top: 5.777778, width: 31, height: 41.333333 },
          { left: 34.5, top: 5.777778, width: 31, height: 41.333333 },
          { left: 67.25, top: 5.777778, width: 31, height: 41.333333 },
          { left: 1.75, top: 52.888889, width: 31, height: 41.333333 },
          { left: 34.5, top: 52.888889, width: 31, height: 41.333333 },
          { left: 67.25, top: 52.888889, width: 31, height: 41.333333 }
        ]
      },
      {
        id: "page-8-grid-land",
        displayName: "横版八宫格",
        badge: "8L",
        blurb: "4×2 横槽 4:3；单槽宽 24.25%；列间 1% 最小缝，左右贴边。剩余高三等分。竖版禁入。左右对称，无镜像。",
        related: "同族 page-4-grid-land（2×2）· page-6-grid-land（3×2）",
        replaces: "无合格现网顶岗（screen-portrait-grid-8 是 9:16 八竖，不是同一张）",
        href: "page-8-grid-land/",
        hasSketch: true,
        slots: [
          { left: 0, top: 11.777778, width: 24.25, height: 32.333333 },
          { left: 25.25, top: 11.777778, width: 24.25, height: 32.333333 },
          { left: 50.5, top: 11.777778, width: 24.25, height: 32.333333 },
          { left: 75.75, top: 11.777778, width: 24.25, height: 32.333333 },
          { left: 0, top: 55.888889, width: 24.25, height: 32.333333 },
          { left: 25.25, top: 55.888889, width: 24.25, height: 32.333333 },
          { left: 50.5, top: 55.888889, width: 24.25, height: 32.333333 },
          { left: 75.75, top: 55.888889, width: 24.25, height: 32.333333 }
        ]
      },
      {
        id: "page-10-grid-port",
        displayName: "竖版十宫格",
        badge: "10P",
        blurb: "5×2 竖槽 3:4 各宽 18.75%（与 page-5-1p4p-left 小竖同尺寸）。余宽六等分；顶/行缝/底各 1/27。横版禁入。左右对称，无镜像。",
        related: "同族 page-4-port · page-5-1p4p-left（同宽小竖）",
        replaces: "无合格现网顶岗",
        href: "page-10-grid-port/",
        hasSketch: true,
        slots: [
          { left: 1.041667, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 20.833333, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 40.625, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 60.416667, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 80.208333, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 1.041667, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 20.833333, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 40.625, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 60.416667, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 80.208333, top: 51.851852, width: 18.75, height: 44.444444 }
        ]
      },
      {
        id: "page-8-2l6p",
        displayName: "上横三竖下三竖横",
        badge: "2L6P",
        blurb: "上：横 1/3 + 三竖 18.75%；下：三竖 + 横 1/3。两行等高 4/9；顶/缝/底各 1/27。按槽禁入。垂直镜像是 page-8-2l6p-flip。",
        related: "兄弟 page-8-2l6p-flip（垂直镜像）· page-10-grid-port（同宽小竖）",
        replaces: "无合格现网顶岗",
        href: "page-8-2l6p/",
        hasSketch: true,
        slots: [
          { left: 2.083333, top: 3.703704, width: 33.333333, height: 44.444444 },
          { left: 37.5, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 58.333333, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 79.166667, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 2.083333, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 22.916667, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 43.75, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 64.583333, top: 51.851852, width: 33.333333, height: 44.444444 }
        ]
      },
      {
        id: "page-8-2l6p-flip",
        displayName: "上三竖横下横三竖",
        badge: "2L6P",
        blurb: "上一张的垂直镜像：上三竖 + 横 1/3；下横 1/3 + 三竖。左右不换。无独立示意图。",
        related: "兄弟 page-8-2l6p。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-8-2l6p-flip/",
        hasSketch: false,
        slots: [
          { left: 2.083333, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 22.916667, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 43.75, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 64.583333, top: 3.703704, width: 33.333333, height: 44.444444 },
          { left: 2.083333, top: 51.851852, width: 33.333333, height: 44.444444 },
          { left: 37.5, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 58.333333, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 79.166667, top: 51.851852, width: 18.75, height: 44.444444 }
        ]
      },
      {
        id: "page-6-2l4p-left",
        displayName: "左两横右四竖",
        badge: "2L4P",
        blurb: "左两横 4:3 宽 1/3 叠；右 2×2 竖 3:4 各宽 18.75%。两行等高 4/9；顶/缝/底各 1/27。按槽禁入。",
        related: "兄弟 page-6-2l4p-right（镜像）· page-8-2l6p（两横对角）",
        replaces: "无合格现网顶岗",
        href: "page-6-2l4p-left/",
        hasSketch: true,
        slots: [
          { left: 7.291667, top: 3.703704, width: 33.333333, height: 44.444444 },
          { left: 47.916667, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 73.958333, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 7.291667, top: 51.851852, width: 33.333333, height: 44.444444 },
          { left: 47.916667, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 73.958333, top: 51.851852, width: 18.75, height: 44.444444 }
        ]
      },
      {
        id: "page-6-2l4p-right",
        displayName: "左四竖右两横",
        badge: "4P2L",
        blurb: "上一张的镜像：左 2×2 竖 3:4 各宽 18.75%，右两横 4:3 宽 1/3 叠。",
        related: "兄弟 page-6-2l4p-left。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-6-2l4p-right/",
        hasSketch: false,
        slots: [
          { left: 7.291667, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 33.333333, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 59.375, top: 3.703704, width: 33.333333, height: 44.444444 },
          { left: 7.291667, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 33.333333, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 59.375, top: 51.851852, width: 33.333333, height: 44.444444 }
        ]
      },
      {
        id: "page-6-4l2p",
        displayName: "四横夹两竖",
        badge: "4L2P",
        blurb: "左右各两横 4:3 宽 1/3 叠；中两竖 3:4 宽 18.75%。两行等高 4/9；顶/缝/底各 1/27。三组余宽四等分。按槽禁入。左右对称无镜像。",
        related: "同尺寸 page-6-2l4p-left（左两横右四竖）· page-4-2p2p（两大竖夹两小竖）",
        replaces: "无合格现网顶岗",
        href: "page-6-4l2p/",
        hasSketch: true,
        slots: [
          { left: 3.645833, top: 3.703704, width: 33.333333, height: 44.444444 },
          { left: 40.625, top: 3.703704, width: 18.75, height: 44.444444 },
          { left: 63.020833, top: 3.703704, width: 33.333333, height: 44.444444 },
          { left: 3.645833, top: 51.851852, width: 33.333333, height: 44.444444 },
          { left: 40.625, top: 51.851852, width: 18.75, height: 44.444444 },
          { left: 63.020833, top: 51.851852, width: 33.333333, height: 44.444444 }
        ]
      },
      {
        id: "page-6-1l5l-wide-left",
        displayName: "左主宽横右下五小",
        badge: "1L5L",
        blurb: "大横 16:9 高 65% 顶齐左齐、底贴底行；右侧三小垂直居中均分；底行三小占满宽。右侧 5% 不对齐。竖版禁入。",
        related: "兄弟 page-6-1l5l-wide-right（镜像）· page-4-1l3l-wide-left（1 大 3 小）",
        replaces: "无合格现网顶岗",
        href: "page-6-1l5l-wide-left/",
        hasSketch: true,
        slots: [
          { left: 0, top: 2.5, width: 65, height: 65 },
          { left: 70, top: 2.5, width: 30, height: 30 },
          { left: 70, top: 35, width: 30, height: 30 },
          { left: 0, top: 67.5, width: 30, height: 30 },
          { left: 35, top: 67.5, width: 30, height: 30 },
          { left: 70, top: 67.5, width: 30, height: 30 }
        ]
      },
      {
        id: "page-6-1l5l-wide-right",
        displayName: "左下五小右主宽横",
        badge: "5L1L",
        blurb: "上一张的镜像：大横 65% 顶齐右齐、底贴底行；左侧三小垂直居中均分；底行三小占满宽。无独立示意图。",
        related: "兄弟 page-6-1l5l-wide-left。无独立示意图",
        replaces: "无合格现网顶岗",
        href: "page-6-1l5l-wide-right/",
        hasSketch: false,
        slots: [
          { left: 0, top: 2.5, width: 30, height: 30 },
          { left: 0, top: 35, width: 30, height: 30 },
          { left: 35, top: 2.5, width: 65, height: 65 },
          { left: 0, top: 67.5, width: 30, height: 30 },
          { left: 35, top: 67.5, width: 30, height: 30 },
          { left: 70, top: 67.5, width: 30, height: 30 }
        ]
      }
    ];
