from __future__ import annotations

OFFICIAL_QUALITIES = {"government_primary", "official_dataset", "official", "high"}


def source_credibility_tier(quality: str) -> str:
    value = (quality or "").strip().casefold()
    if value in OFFICIAL_QUALITIES:
        return "official"
    if value in {"primary", "curated"}:
        return "curated_primary"
    return "unclassified"


def evidence_strength(group_count: int, component_count: int, cpc_scope: str) -> str:
    if group_count >= 2 and component_count >= 1 and cpc_scope == "core":
        return "STRONG"
    if group_count >= 2 and component_count >= 1 and cpc_scope in {"adjacent", "unknown"}:
        return "MEDIUM"
    if group_count >= 1 and component_count >= 1 and cpc_scope == "core":
        return "MEDIUM"
    return "WEAK"


def is_fact_eligible(credibility: str, strength: str, verification_status: str) -> bool:
    return (
        credibility == "official"
        and strength == "STRONG"
        and verification_status == "official_crosschecked"
    )
