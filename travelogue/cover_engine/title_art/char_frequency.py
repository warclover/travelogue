"""路线 C 标题预筛选（D-CAL-21 · Route C W0.5 Spike 数据驱动，2026-08-08）。

W0.5 完整 Spike（26 条真实/边界标题，见
``docs/acceptance-records/cover-calligraphy-title-v1-w05-route-c-spike-2026-08-08.md``）
发现：常见地名 / 纯数字标题 OCR 回读通过率稳定 100%，含生僻字（GB2312 一级
常用字表以外的汉字）的标题通过率显著更低（55.6%～0%）。本模块提供一个轻
量、可解释、零外部依赖的预筛选——标题里出现"表外汉字"就判定为「不建议
尝试路线 C」，在真正发起一次 15～28 秒 + 有成本的 API 调用前直接短路到路
线 B，省下一次大概率失败的调用。

**不改变最终正确性**：D-CAL-19 OCR 回读校验始终是唯一真正的安全闸门，
本模块只影响"要不要多花一次调用成本去赌"这个决策，被预筛选拦下的标题
跟"调用了但 OCR 没过"最终展示效果完全一样——都是路线 B。

字表来源：GB2312 一级汉字（3755 个，按拼音排序的"常用字"，与二级"次常
用字"分列是国标本身的设计）。在导入时直接用标准库 ``codecs`` 从 GB2312
编码本身派生对应码位，不依赖外部数据文件、不发网络请求，也不会因供应商
调价/模型更新而过时——这是一份自 1980 年发布后未变过的国标，用来做"是
否常用字"的代理指标是标准且可复现的选择，不是本项目自造的频率表。

局限（对 26 条 Spike 样本回测后如实记录，见验收记录 §5）：
- 召回不完美：像"黟/硇/邺"这几个二级字（表外）在本次 Spike 里实际生成
  正确，会被本过滤器误判为"不建议尝试"（错杀，纯效率损失——路线 C 根本
  没被调用，直接走路线 B，跟"调用后 OCR 没过再降级"安全性完全等价）。
- 精确度也不是 100%：一级表内的字仍有生成失败案例（例如叠字"一茶一饭
  间"→"一茶大饭间"、省略号被吃掉），这类失败模式跟"字有多常用"无关，
  本过滤器管不了，D-CAL-19 OCR 校验仍需兜底。
- 回测结果：过滤器允许 26 条中的 17 条尝试路线 C，这 17 条里实际 OCR 通
  过率从 57.7%（全量）提升到 64.7%——**仍未达 AC-CAL-11 的 90% 门槛**，
  预筛选是降本增效手段，不单独构成"解锁默认开启"的依据。
"""

from __future__ import annotations

import unicodedata
from functools import lru_cache

#: GB2312 一级汉字所在的字节区间：高位字节 0xB0～0xD7（区 16～55），
#: 低位字节 0xA1～0xFE（区内 1～94 位）。区 56～87（0xD8～0xF7）是二级
#: 汉字，故意不纳入——那正是"次常用字"，本模块要过滤掉的就是这部分。
_LEVEL1_HIGH_BYTE_RANGE = range(0xB0, 0xD8)
_LOW_BYTE_RANGE = range(0xA1, 0xFF)


def _build_common_hanzi() -> frozenset[str]:
    chars: set[str] = set()
    try:
        for hi in _LEVEL1_HIGH_BYTE_RANGE:
            for lo in _LOW_BYTE_RANGE:
                try:
                    chars.add(bytes([hi, lo]).decode("gb2312"))
                except UnicodeDecodeError:
                    continue
    except LookupError:
        # gb2312 codec 在极少数精简 Python 构建下可能缺失（无
        # _codecs_cn 扩展）；宁可预筛选整体失效（回到"全量尝试"的行为），
        # 也不要把"取不到字表"误当成"全部都是生僻字"去拦截一切标题。
        return frozenset()
    return frozenset(chars)


@lru_cache(maxsize=1)
def _common_hanzi() -> frozenset[str]:
    return _build_common_hanzi()


def _is_han(ch: str) -> bool:
    """单个字符是否为 CJK 统一汉字（供本模块与 risk_rules 共用）。"""
    return "CJK UNIFIED" in unicodedata.name(ch, "")


def title_has_only_common_chars(text: str) -> bool:
    """标题是否只含 GB2312 一级常用汉字（数字/英文/标点永远视为不阻断）。

    字表构建失败（见 :func:`_build_common_hanzi` 的 ``LookupError`` 分支）
    时返回 ``True``——预筛选静默失效，不阻断任何标题。
    """
    common = _common_hanzi()
    if not common:
        return True
    return all(not _is_han(ch) or ch in common for ch in text)
