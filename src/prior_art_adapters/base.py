"""Prior art adapter 公共基类与数据结构。

Phase A:USPTO Open Data + EPO OPS + Google Patents via Playwright 三源统一接口。
loader 端用 BaseAdapter.search() 拿 record 列表,统一入库。
"""
from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar, Iterator, Optional


@dataclass(frozen=True)
class PriorArtQuery:
    """单次检索查询参数。"""

    keywords: tuple[str, ...]               # ("reverse thrust", "FADEC", "EEC")
    cpc_prefixes: tuple[str, ...]           # ("B64D31", "F02C9")  adapter 内部转 OR
    filing_date_from: str = "2000-01-01"    # ISO date
    per_query_limit: int = 500              # 单关键词+CPC 硬上限


@dataclass(frozen=True)
class PriorArtRecord:
    """统一中间格式:一个专利先有技术条目。

    loader 端拿这个 dict 直接 INSERT。source_id 由 adapter 注入(便于桥表 is_primary 决策)。
    """

    publication_number: str          # 已 normalize:去空格/横线,大写
    country_code: str                # ISO 3166-1 alpha-2
    title_zh: str                    # 无中文统一占位 "[EN-only]"
    title_en: str
    abstract_zh: str
    abstract_en: str
    cpc_codes: tuple[str, ...]       # 已 normalize_cpc
    inventors: tuple[str, ...]
    assignees: tuple[str, ...]
    filing_date: str                 # YYYY-MM-DD
    publication_date: str
    grant_date: Optional[str] = None
    family_id: Optional[str] = None
    raw_url: str = ""                # 原始详情页 URL(给桥表用)
    raw_payload_sha256: str = ""     # 原始响应 hash
    source_id: str = ""              # 哪个 adapter 出的


class AdapterError(RuntimeError):
    """adapter 不可恢复错误(health check 失败 / OAuth 长期失败 / captcha 持续触发)。"""


class BaseAdapter(ABC):
    """三源统一签名。"""

    source_id: ClassVar[str]                # 例 "uspto-od"
    source_kind: ClassVar[str] = "prior_art_corpus"
    requires_auth: ClassVar[bool] = False
    rate_limit_sec: ClassVar[float] = 1.0

    def __init__(self) -> None:
        self._last_call_ts: float = 0.0

    def _rate_limit(self) -> None:
        """强制 rate_limit_sec 间隔,避免被 captcha / 429。"""
        elapsed = time.monotonic() - self._last_call_ts
        if elapsed < self.rate_limit_sec:
            time.sleep(self.rate_limit_sec - elapsed)
        self._last_call_ts = time.monotonic()

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @abstractmethod
    def health_check(self) -> bool:
        """import 流程开跑前 ping 一下,失败则 loader 直接报错不拉数据。"""

    @abstractmethod
    def search(self, query: PriorArtQuery) -> Iterator[PriorArtRecord]:
        """yield PriorArtRecord,适配器内部处理分页/限速/错误重试。"""
        # 子类 yield 前应 self._rate_limit() + 捕获 AdapterError