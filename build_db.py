from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.cross_match_builder import create_schema as create_cross_match_schema
from src.ontology_loader import install_ontology


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "throttle_knowledge.db"


# ===== AirworthinessKB API 接入 =====
# 单一可信源：所有法规条款走 AirworthinessKB :8000，工具不再各自手录
# 关闭时降级到本地 FALLBACK_REGULATORY_CONSTRAINTS，保证离线可用
AWKB_BASE = os.environ.get("AWKB_BASE", "http://127.0.0.1:8000")
AWKB_TIMEOUT = float(os.environ.get("AWKB_TIMEOUT", "8"))
AWKB_ENABLED = os.environ.get("AWKB_ENABLED", "1") not in ("0", "false", "no", "")


def _awkb_get(path: str) -> dict | None:
    """GET AirworthinessKB API，失败返回 None（降级）。"""
    if not AWKB_ENABLED:
        return None
    url = f"{AWKB_BASE}{path}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=AWKB_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        print(f"[AWKB] 降级：{url} 失败 ({exc})，回退本地数据")
        return None


def _awkb_post(path: str, payload: dict) -> dict | None:
    """POST AirworthinessKB API，失败返回 None。"""
    if not AWKB_ENABLED:
        return None
    url = f"{AWKB_BASE}{path}"
    try:
        body = json.dumps(payload).encode("utf-8")
        req = Request(url, data=body, headers={"Accept": "application/json", "Content-Type": "application/json"})
        with urlopen(req, timeout=AWKB_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        print(f"[AWKB] 降级：{url} 失败 ({exc})，回退本地数据")
        return None


def _awkb_fetch_clause_body(regulation: str, clause_number: str) -> str | None:
    """从 AirworthinessKB 拉条款正文。

    用 /v1/ask 自然语言查询 + 过滤到目标规章，取最高分命中。
    返回条款正文（用于覆盖 requirement_zh/en），失败返回 None。
    """
    question = f"{regulation} §{clause_number}"
    result = _awkb_post(
        "/api/v1/ask",
        {"question": question, "top_k": 5, "regulations": [regulation]},
    )
    if not result or not result.get("hits"):
        return None
    # 取分数最高且 regulation 匹配的命中
    for hit in result["hits"]:
        if hit.get("regulation") == regulation and hit.get("clause_number") == clause_number:
            return hit.get("snippet", "").strip()
    # 退而求其次：取第一条 snippet
    return result["hits"][0].get("snippet", "").strip() or None


MODELS = [
    {
        "id": "a320",
        "category": "commercial",
        "family": "airbus",
        "nation_zh": "欧洲",
        "nation_en": "Europe",
        "maker_zh": "空中客车",
        "maker_en": "Airbus",
        "name_zh": "A320 系列油门台",
        "name_en": "A320 Family Thrust Levers",
        "short_zh": "双发固定式推力手柄，以机械卡位向自动推力系统表达推力上限。",
        "short_en": "Twin fixed-position thrust levers whose detents command thrust limits to autothrust.",
        "source_id": "airbus-safety-flare",
        "confidence": "high",
        "geometry": {"base": "wide", "levers": 2, "split": 0.72, "grip": "airbus", "buttons": 2, "side": "center"},
        "features": {
            "engine_channels": ["双发 / 2", "Twin / 2"],
            "control_philosophy": ["推力卡位 + 自动推力", "Detents + autothrust"],
            "automation": ["A/THR；手柄通常停在卡位", "A/THR; levers normally remain in detent"],
            "automation_motion": ["不随自动推力移动", "No commanded lever motion"],
            "detents": ["IDLE / CL / MCT-FLX / TOGA", "IDLE / CL / MCT-FLX / TOGA"],
            "reverse": ["独立反推手柄", "Dedicated reverse levers"],
            "afterburner": ["不适用", "Not applicable"],
            "hotas": ["否", "No"],
            "special": ["双发主手柄、反推锁、卡位触感", "Twin main levers, reverse locks, tactile detents"],
            "evidence": ["厂商安全资料直接支持", "Direct manufacturer safety material"],
        },
    },
    {
        "id": "b737ng",
        "category": "commercial",
        "family": "boeing",
        "nation_zh": "美国",
        "nation_en": "United States",
        "maker_zh": "波音",
        "maker_en": "Boeing",
        "name_zh": "737NG 油门台",
        "name_en": "737NG Throttle Quadrant",
        "short_zh": "经典中央油门台布局，双主油门配反推手柄，自动油门动作可在手柄上观察。",
        "short_en": "Classic center quadrant with twin thrust and reverse levers; autothrottle motion is observable at the levers.",
        "source_id": "boeing-737ng",
        "confidence": "medium",
        "geometry": {"base": "pedestal", "levers": 2, "split": 0.88, "grip": "boeing", "buttons": 2, "side": "center"},
        "features": {
            "engine_channels": ["双发 / 2", "Twin / 2"],
            "control_philosophy": ["移动式主油门 + 自动油门", "Moving thrust levers + autothrottle"],
            "automation": ["A/T 驱动主油门", "A/T drives thrust levers"],
            "automation_motion": ["自动模式下可移动", "Moves under automation"],
            "detents": ["IDLE；前向连续行程", "IDLE; continuous forward travel"],
            "reverse": ["主手柄上方反推手柄", "Piggyback reverse levers"],
            "afterburner": ["不适用", "Not applicable"],
            "hotas": ["否", "No"],
            "special": ["TO/GA 按钮、可见自动油门运动", "TO/GA switches, visible A/T motion"],
            "evidence": ["厂商飞行甲板资料 + 公开驾驶舱资料", "Manufacturer flight-deck page + public cockpit material"],
        },
    },
    {
        "id": "c919",
        "category": "commercial",
        "family": "comac",
        "nation_zh": "中国",
        "nation_en": "China",
        "maker_zh": "中国商飞",
        "maker_en": "COMAC",
        "name_zh": "C919 油门台",
        "name_en": "C919 Throttle Quadrant",
        "short_zh": "双发中央油门台，与现代玻璃驾驶舱及自动飞行系统协同；公开细节有限。",
        "short_en": "Twin-engine center quadrant integrated with a modern glass cockpit and autoflight system; public detail is limited.",
        "source_id": "comac-training",
        "confidence": "limited",
        "geometry": {"base": "modern", "levers": 2, "split": 0.76, "grip": "comac", "buttons": 2, "side": "center"},
        "features": {
            "engine_channels": ["双发 / 2", "Twin / 2"],
            "control_philosophy": ["现代民航中央油门台", "Modern civil center quadrant"],
            "automation": ["具备自动油门；公开控制逻辑有限", "Autothrottle present; public logic is limited"],
            "automation_motion": ["公开资料未充分披露", "Not sufficiently disclosed publicly"],
            "detents": ["公开资料未充分披露", "Not sufficiently disclosed publicly"],
            "reverse": ["双发反推控制", "Twin-engine reverse control"],
            "afterburner": ["不适用", "Not applicable"],
            "hotas": ["否", "No"],
            "special": ["强调机组训练与系统程序", "Emphasis on crew training and system procedures"],
            "evidence": ["商飞公开培训目录；细节采用保守表述", "COMAC public training catalog; conservative detail"],
        },
    },
    {
        "id": "f16c",
        "category": "military",
        "family": "us-f",
        "nation_zh": "美国",
        "nation_en": "United States",
        "maker_zh": "洛克希德·马丁",
        "maker_en": "Lockheed Martin",
        "name_zh": "F-16C 油门 / HOTAS",
        "name_en": "F-16C Throttle / HOTAS",
        "short_zh": "单发左手油门，与右侧压感操纵杆构成典型 HOTAS 工作流。",
        "short_en": "Single-engine left-hand throttle paired with a right-side force-sensing stick for a classic HOTAS workflow.",
        "source_id": "usaf-f16",
        "confidence": "high",
        "geometry": {"base": "side", "levers": 1, "split": 1.0, "grip": "fighter", "buttons": 8, "side": "left"},
        "features": {
            "engine_channels": ["单发 / 1", "Single / 1"],
            "control_philosophy": ["左手油门 + 右侧杆 HOTAS", "Left throttle + right side-stick HOTAS"],
            "automation": ["作战型人工推力控制为主", "Primarily manual tactical thrust control"],
            "automation_motion": ["不适用", "Not applicable"],
            "detents": ["OFF / IDLE；军用推力 / 加力区", "OFF / IDLE; military / afterburner region"],
            "reverse": ["无", "None"],
            "afterburner": ["有", "Yes"],
            "hotas": ["高度集成", "Highly integrated"],
            "special": ["雷达、武器与通信快捷控制", "Rapid radar, weapon and communications controls"],
            "evidence": ["美国空军官方型号资料", "Official U.S. Air Force fact sheet"],
        },
    },
    {
        "id": "fa18e",
        "category": "military",
        "family": "us-f",
        "nation_zh": "美国",
        "nation_en": "United States",
        "maker_zh": "波音",
        "maker_en": "Boeing",
        "name_zh": "F/A-18E 双发油门 / HOTAS",
        "name_en": "F/A-18E Twin Throttle / HOTAS",
        "short_zh": "舰载双发分体油门，兼顾独立发动机控制、加力与高负荷任务操作。",
        "short_en": "Carrier-capable split twin throttles supporting independent engine control, afterburner and high-workload missions.",
        "source_id": "usn-fa18",
        "confidence": "medium",
        "geometry": {"base": "side", "levers": 2, "split": 1.08, "grip": "fighter", "buttons": 10, "side": "left"},
        "features": {
            "engine_channels": ["双发 / 2，可分体", "Twin / 2, split-capable"],
            "control_philosophy": ["舰载双发 HOTAS", "Carrier twin-engine HOTAS"],
            "automation": ["战术任务人工控制为主", "Primarily manual tactical control"],
            "automation_motion": ["不适用", "Not applicable"],
            "detents": ["OFF / IDLE；MIL / AB", "OFF / IDLE; MIL / AB"],
            "reverse": ["无", "None"],
            "afterburner": ["有", "Yes"],
            "hotas": ["高度集成", "Highly integrated"],
            "special": ["双发分体、舰载任务、多用途", "Split engines, carrier ops, multirole"],
            "evidence": ["美国海军官方型号资料；控制细节为公开资料综合", "Official U.S. Navy fact file; control details synthesized"],
        },
    },
    {
        "id": "typhoon",
        "category": "military",
        "family": "europe",
        "nation_zh": "欧洲",
        "nation_en": "Europe",
        "maker_zh": "Eurofighter 联合体",
        "maker_en": "Eurofighter Consortium",
        "name_zh": "台风 VTAS / HOTAS",
        "name_en": "Typhoon VTAS / HOTAS",
        "short_zh": "双发 HOTAS 与直接语音输入结合，形成 Voice, Throttle and Stick 控制概念。",
        "short_en": "Twin-engine HOTAS combined with Direct Voice Input as the Voice, Throttle and Stick concept.",
        "source_id": "eurofighter-features",
        "confidence": "high",
        "geometry": {"base": "side", "levers": 2, "split": 0.84, "grip": "euro", "buttons": 12, "side": "left"},
        "features": {
            "engine_channels": ["双发 / 2", "Twin / 2"],
            "control_philosophy": ["VTAS：语音 + 油门 + 杆", "VTAS: Voice + Throttle + Stick"],
            "automation": ["飞控与任务系统高度集成", "Highly integrated flight and mission systems"],
            "automation_motion": ["不适用", "Not applicable"],
            "detents": ["IDLE / MIL / 加力区", "IDLE / MIL / afterburner region"],
            "reverse": ["无", "None"],
            "afterburner": ["有", "Yes"],
            "hotas": ["HOTAS + DVI", "HOTAS + DVI"],
            "special": ["语音输入、传感器与防御系统控制", "Voice input, sensor and defensive-system control"],
            "evidence": ["Eurofighter 官方功能页直接支持", "Directly supported by Eurofighter official feature page"],
        },
    },
    {
        "id": "rafale",
        "category": "military",
        "family": "europe",
        "nation_zh": "法国",
        "nation_en": "France",
        "maker_zh": "达索航空",
        "maker_en": "Dassault Aviation",
        "name_zh": "阵风 HOTAS",
        "name_en": "Rafale HOTAS",
        "short_zh": "双发油门与任务控制深度整合，强调抬头工作流与快速战术操作。",
        "short_en": "Twin-engine throttle deeply integrated with mission controls for heads-up workflow and rapid tactical action.",
        "source_id": "dassault-rafale",
        "confidence": "high",
        "geometry": {"base": "side", "levers": 2, "split": 0.78, "grip": "euro", "buttons": 11, "side": "left"},
        "features": {
            "engine_channels": ["双发 / 2", "Twin / 2"],
            "control_philosophy": ["高集成 HOTAS 人机界面", "Highly integrated HOTAS HMI"],
            "automation": ["飞控、任务与传感器融合", "Flight, mission and sensor integration"],
            "automation_motion": ["不适用", "Not applicable"],
            "detents": ["IDLE / 军用推力 / 加力区", "IDLE / military / afterburner region"],
            "reverse": ["无", "None"],
            "afterburner": ["有", "Yes"],
            "hotas": ["高度集成", "Highly integrated"],
            "special": ["显示、传感器、武器快速交互", "Rapid display, sensor and weapon interaction"],
            "evidence": ["达索航空官方座舱人机界面资料", "Dassault official cockpit HMI material"],
        },
    },
    {
        "id": "gripen",
        "category": "military",
        "family": "europe",
        "nation_zh": "瑞典",
        "nation_en": "Sweden",
        "maker_zh": "萨博",
        "maker_en": "Saab",
        "name_zh": "鹰狮 C HOTAS",
        "name_en": "Gripen C HOTAS",
        "short_zh": "单发 HOTAS 与优化的人机界面、数据链和传感器融合协同。",
        "short_en": "Single-engine HOTAS working with an optimized HMI, datalinks and sensor-fused information.",
        "source_id": "saab-gripen",
        "confidence": "high",
        "geometry": {"base": "side", "levers": 1, "split": 1.0, "grip": "euro", "buttons": 10, "side": "left"},
        "features": {
            "engine_channels": ["单发 / 1", "Single / 1"],
            "control_philosophy": ["HOTAS + 信息融合 HMI", "HOTAS + information-fusion HMI"],
            "automation": ["任务系统与决策支持集成", "Mission systems and decision support integration"],
            "automation_motion": ["不适用", "Not applicable"],
            "detents": ["IDLE / 军用推力 / 加力区", "IDLE / military / afterburner region"],
            "reverse": ["无", "None"],
            "afterburner": ["有", "Yes"],
            "hotas": ["完整 HOTAS", "Complete HOTAS"],
            "special": ["数据链、传感器融合、角色切换", "Datalink, sensor fusion, role switching"],
            "evidence": ["萨博官方型号资料", "Official Saab product material"],
        },
    },
    {
        "id": "su35s",
        "category": "military",
        "family": "russia",
        "nation_zh": "俄罗斯",
        "nation_en": "Russia",
        "maker_zh": "苏霍伊 / 联合航空制造集团",
        "maker_en": "Sukhoi / UAC",
        "name_zh": "苏-35S 双发油门",
        "name_en": "Su-35S Twin Throttle",
        "short_zh": "双发左侧油门，与玻璃座舱、数字发动机控制和任务系统协同；公开细节受限。",
        "short_en": "Twin left-console throttles integrated with a glass cockpit, digital engine control and mission systems; public detail is limited.",
        "source_id": "uac-su35",
        "confidence": "limited",
        "geometry": {"base": "side", "levers": 2, "split": 0.92, "grip": "flanker", "buttons": 9, "side": "left"},
        "features": {
            "engine_channels": ["双发 / 2", "Twin / 2"],
            "control_philosophy": ["双发 HOTAS 类战术控制", "Twin-engine HOTAS-type tactical control"],
            "automation": ["数字发动机控制", "Digital engine control"],
            "automation_motion": ["公开资料未充分披露", "Not sufficiently disclosed publicly"],
            "detents": ["IDLE / 军用推力 / 加力区", "IDLE / military / afterburner region"],
            "reverse": ["无", "None"],
            "afterburner": ["有", "Yes"],
            "hotas": ["公开资料支持 HOTAS 概念，细节有限", "Public material supports HOTAS; detail is limited"],
            "special": ["双发分控、任务与传感器交互", "Twin-engine split control, mission and sensor interaction"],
            "evidence": ["UAC 官方型号资料；油门细节标为有限证据", "Official UAC aircraft page; throttle detail marked limited"],
        },
    },
]


SOURCES = [
    {
        "id": "faa-phak",
        "kind": "official_manual",
        "quality": "high",
        "org": "FAA",
        "title_zh": "《飞行员航空知识手册》：发动机与油门基础",
        "title_en": "Pilot's Handbook of Aeronautical Knowledge: engine and throttle fundamentals",
        "url": "https://www.faa.gov/aviation/phak/pilots-handbook-aeronautical-knowledge-faa-h-8083-25b",
        "note_zh": "监管机构公开手册，用于解释油门、功率、螺旋桨控制与驾驶舱控制的一般概念。",
        "note_en": "Regulator handbook used for general concepts of throttles, power, propeller control and cockpit controls.",
    },
    {
        "id": "airbus-cockpits",
        "kind": "manufacturer",
        "quality": "high",
        "org": "Airbus",
        "title_zh": "空客驾驶舱与共通性",
        "title_en": "Airbus cockpits and commonality",
        "url": "https://www.airbus.com/en/products-services/commercial-aircraft/cockpits",
        "note_zh": "空客官方说明飞控、驾驶舱布局和机型共通性。",
        "note_en": "Airbus overview of fly-by-wire cockpits, layout and fleet commonality.",
    },
    {
        "id": "faa-a320-autothrust",
        "kind": "official_safety",
        "quality": "high",
        "org": "FAA",
        "title_zh": "A320 自动推力系统与固定手柄逻辑",
        "title_en": "A320 autothrust and static-lever logic",
        "url": "https://www.faa.gov/lessons_learned/transport_airplane/accidents/VT-EPN",
        "note_zh": "FAA 事故教训页面明确说明 A320 推力手柄停留在卡位，发动机推力变化不会反向驱动手柄。",
        "note_en": "FAA Lessons Learned explicitly explains that A320 thrust levers remain in detent and are not back-driven by engine thrust changes.",
    },
    {
        "id": "airbus-safety-flare",
        "kind": "manufacturer_safety",
        "quality": "high",
        "org": "Airbus Safety First",
        "title_zh": "着陆拉平中的推力手柄管理",
        "title_en": "Thrust lever management during landing flare",
        "url": "https://safetyfirst.airbus.com/a-focus-on-the-landing-flare/",
        "note_zh": "明确说明 A320 等机型的 CLB/IDLE 卡位、自动推力与 RETARD 提示的关系。",
        "note_en": "Explains CLB/IDLE detents, autothrust and the RETARD reminder on A320-family aircraft.",
    },
    {
        "id": "airbus-takeoff",
        "kind": "manufacturer_safety",
        "quality": "high",
        "org": "Airbus Safety First",
        "title_zh": "起飞推力设置与双手柄同步",
        "title_en": "Takeoff thrust setting and synchronized lever movement",
        "url": "https://safetyfirst.airbus.com/engine-thrust-management-thrust-setting-at-takeoff/",
        "note_zh": "空客官方安全文章，解释 A320 起飞推力的两步设置和双手柄同步要求。",
        "note_en": "Airbus safety article on two-step takeoff thrust application and synchronized lever movement.",
    },
    {
        "id": "boeing-737ng",
        "kind": "manufacturer",
        "quality": "high",
        "org": "Boeing",
        "title_zh": "737NG 设计亮点：先进飞行甲板",
        "title_en": "737NG Design Highlights: advanced flight deck",
        "url": "https://www.boeing.com/Commercial/737ng/737-next-generation-design-highlights",
        "note_zh": "波音官方介绍 737NG 飞行甲板设计、自动化与飞行员最终控制权。",
        "note_en": "Boeing overview of the 737NG flight deck, automation and pilot authority.",
    },
    {
        "id": "ntsb-737-autothrottle",
        "kind": "official_investigation",
        "quality": "high",
        "org": "NTSB / FAA",
        "title_zh": "737 自动油门驱动推力手柄",
        "title_en": "737 autothrottle drives the thrust levers",
        "url": "https://www.faa.gov/sites/faa.gov/files/2022-11/usair427_ntsb_report.pdf",
        "note_zh": "FAA 托管的 NTSB 事故报告说明，737 自动油门移动推力手柄，以保持选定空速或推力设置。",
        "note_en": "FAA-hosted NTSB report states that the 737 autothrottle moves thrust levers to maintain selected airspeed or thrust settings.",
    },
    {
        "id": "comac-training",
        "kind": "manufacturer",
        "quality": "high",
        "org": "COMAC",
        "title_zh": "C919 客户培训资料目录",
        "title_en": "C919 customer training material catalog",
        "url": "https://www.comac.cc/cpyzr/jszl/px/pxzl/202501/15/t20250115_7400587.shtml",
        "note_zh": "商飞官方列出驾驶舱图、面板图、快速检查单与飞行机组操作手册等培训资料。",
        "note_en": "COMAC lists cockpit diagrams, panel diagrams, quick checklists and flight-crew manuals used for training.",
    },
    {
        "id": "usaf-f16",
        "kind": "military_official",
        "quality": "high",
        "org": "U.S. Air Force",
        "title_zh": "F-16 战隼官方资料页",
        "title_en": "F-16 Fighting Falcon official fact sheet",
        "url": "https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104505/f-16-fighting-falcon/",
        "note_zh": "美国空军说明 F-16 的电传飞控、右侧杆、人机工程与多用途任务。",
        "note_en": "U.S. Air Force source on F-16 fly-by-wire, side-stick ergonomics and multirole mission.",
    },
    {
        "id": "usn-fa18",
        "kind": "military_official",
        "quality": "high",
        "org": "U.S. Navy",
        "title_zh": "F/A-18E/F 超级大黄蜂官方资料页",
        "title_en": "F/A-18E/F Super Hornet official fact file",
        "url": "https://www.navy.mil/Resources/Fact-Files/Display-FactFiles/Article/2383479/fa-18a-d-hornet-and-fa-18ef-super-hornet-strike-fighter/",
        "note_zh": "美国海军说明其双发、舰载、多任务和 Block III 先进驾驶舱特征。",
        "note_en": "U.S. Navy overview of the twin-engine carrier aircraft, multirole mission and Block III cockpit.",
    },
    {
        "id": "eurofighter-features",
        "kind": "manufacturer",
        "quality": "high",
        "org": "Eurofighter",
        "title_zh": "台风战斗机座舱、HOTAS 与 VTAS",
        "title_en": "Typhoon cockpit, HOTAS and VTAS",
        "url": "https://www.eurofighter.com/the-aircraft/features",
        "note_zh": "官方明确描述 HOTAS 与直接语音输入结合为 VTAS，并说明无需低头或离开飞行控制器。",
        "note_en": "Official description of HOTAS combined with Direct Voice Input as VTAS for heads-up control.",
    },
    {
        "id": "dassault-rafale",
        "kind": "manufacturer",
        "quality": "high",
        "org": "Dassault Aviation",
        "title_zh": "阵风人机界面：综合与简化",
        "title_en": "Rafale HMI: synthesise and facilitate",
        "url": "https://www.dassault-aviation.com/en/defense/rafale/synthesise-and-facilitate/",
        "note_zh": "达索官方说明阵风采用高度集成的 HOTAS 人机界面。",
        "note_en": "Dassault official description of Rafale's highly integrated HOTAS interface.",
    },
    {
        "id": "saab-gripen",
        "kind": "manufacturer",
        "quality": "high",
        "org": "Saab",
        "title_zh": "鹰狮 C 系列：信息优势与人机界面",
        "title_en": "Gripen C-series: information superiority and HMI",
        "url": "https://www.saab.com/products/gripen-c-series",
        "note_zh": "萨博官方介绍数据链、传感器融合、决策支持和优化的人机界面。",
        "note_en": "Saab overview of datalink, sensor fusion, decision support and optimized HMI.",
    },
    {
        "id": "uac-su35",
        "kind": "manufacturer",
        "quality": "high",
        "org": "United Aircraft Corporation",
        "title_zh": "苏-35 官方型号资料",
        "title_en": "Su-35 official aircraft page",
        "url": "https://uacrussia.ru/en/aircraft/lineup/military/su-35/",
        "note_zh": "UAC 官方说明苏-35 的双发、数字发动机控制、通信和任务系统；油门细节公开有限。",
        "note_en": "UAC source on the Su-35 twin-engine platform, digital engine control, communications and mission systems; throttle detail is limited.",
    },
    {
        "id": "img-a320",
        "kind": "licensed_media",
        "quality": "verified",
        "org": "Wikimedia Commons",
        "title_zh": "图片：A320 推力手柄",
        "title_en": "Image: A320 thrust levers",
        "url": "https://commons.wikimedia.org/wiki/File:Thrust_levers_of_an_Airbus_A320.jpg",
        "note_zh": "Olivier Cleynen，CC BY-SA 3.0，2013。",
        "note_en": "Olivier Cleynen, CC BY-SA 3.0, 2013.",
    },
    {
        "id": "img-boeing",
        "kind": "licensed_media",
        "quality": "verified",
        "org": "Wikimedia Commons",
        "title_zh": "图片：波音 737 驾驶舱",
        "title_en": "Image: Boeing 737 cockpit",
        "url": "https://commons.wikimedia.org/wiki/File:Boeing_737_cockpit.jpg",
        "note_zh": "Milkmandan，CC BY-SA 3.0 / GFDL，2005。",
        "note_en": "Milkmandan, CC BY-SA 3.0 / GFDL, 2005.",
    },
    {
        "id": "img-f16",
        "kind": "licensed_media",
        "quality": "verified",
        "org": "Wikimedia Commons",
        "title_zh": "图片：F-16 驾驶舱局部",
        "title_en": "Image: F-16 cockpit detail",
        "url": "https://commons.wikimedia.org/wiki/File:F-16_Cockpit_part.JPG",
        "note_zh": "Alf van Beem，CC0 1.0，2012。",
        "note_en": "Alf van Beem, CC0 1.0, 2012.",
    },
    {
        "id": "img-typhoon",
        "kind": "licensed_media",
        "quality": "verified",
        "org": "Wikimedia Commons",
        "title_zh": "图片：台风驾驶舱",
        "title_en": "Image: Eurofighter Typhoon cockpit",
        "url": "https://commons.wikimedia.org/wiki/File:Eurofighter_Cockpit.jpg",
        "note_zh": "tribp，CC BY 2.0，2012。",
        "note_en": "tribp, CC BY 2.0, 2012.",
    },
    {
        "id": "img-su35",
        "kind": "licensed_media",
        "quality": "verified",
        "org": "Wikimedia Commons",
        "title_zh": "图片：苏-35S 驾驶舱",
        "title_en": "Image: Su-35S cockpit",
        "url": "https://commons.wikimedia.org/wiki/File:Sukhoi_Su-35S_07_RED_PAS_2013_08_Cockpit.jpg",
        "note_zh": "Julian Herzog，CC BY 4.0 / GFDL，2013。",
        "note_en": "Julian Herzog, CC BY 4.0 / GFDL, 2013.",
    },
]

SOURCES.extend([
    {
        "id": "faa-25-flightdeck-controls",
        "kind": "official_regulation",
        "quality": "primary",
        "org": "FAA / eCFR",
        "title_zh": "14 CFR §25.777 驾驶舱操纵器件",
        "title_en": "14 CFR §25.777 Cockpit controls",
        "url": "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-25/subpart-D/section-25.777",
        "note_zh": "美国运输类飞机驾驶舱操纵器件的位置、可达性、防混淆和防误动要求；与 §25.779 配套使用。",
        "note_en": "U.S. transport-category requirements for control location, reach, confusion and inadvertent operation; read with §25.779.",
    },
    {
        "id": "faa-25-powerplant-controls",
        "kind": "official_regulation",
        "quality": "primary",
        "org": "FAA / eCFR",
        "title_zh": "14 CFR §§25.1141–25.1143 动力装置操纵器件",
        "title_en": "14 CFR §§25.1141–25.1143 Powerplant controls",
        "url": "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-25/subpart-E/section-25.1143",
        "note_zh": "美国运输类飞机动力/推力操纵器件的总则、独立发动机控制、同步控制与燃油切断防护。",
        "note_en": "U.S. rules for power/thrust-control design, independent and simultaneous engine control, and fuel-cutoff protection.",
    },
    {
        "id": "faa-25-reverse",
        "kind": "official_regulation",
        "quality": "primary",
        "org": "FAA / eCFR",
        "title_zh": "14 CFR §25.1155 反推与低于飞行状态的桨距",
        "title_en": "14 CFR §25.1155 Reverse thrust and propeller pitch settings below the flight regime",
        "url": "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-25/subpart-E/section-25.1155",
        "note_zh": "要求防止误动，并在飞行慢车设置确实的锁或止动器；离开正推力状态需另一个明显动作。",
        "note_en": "Requires inadvertent-operation protection, a positive lock or stop at flight idle, and a separate and distinct crew operation.",
    },
    {
        "id": "easa-cs25-current",
        "kind": "official_certification_specification",
        "quality": "primary",
        "org": "EASA",
        "title_zh": "CS-25 大型飞机认证规范（现行文件库）",
        "title_en": "CS-25 Large Aeroplanes — current document library",
        "url": "https://www.easa.europa.eu/en/document-library/certification-specifications/group/cs-25-large-aeroplanes",
        "note_zh": "EASA 官方 CS-25 文件库；截至核验日列示 Amendment 28。适用修订版仍须由具体项目审定基础确定。",
        "note_en": "Official EASA CS-25 library; Amendment 28 is listed at the verification date. The applicable amendment remains project-specific.",
    },
    {
        "id": "easa-cs25-flightdeck-controls",
        "kind": "official_certification_specification",
        "quality": "primary",
        "org": "EASA",
        "title_zh": "CS 25.777 / 25.779 驾驶舱操纵器件",
        "title_en": "CS 25.777 / 25.779 Cockpit controls",
        "url": "https://www.easa.europa.eu/en/document-library/easy-access-rules/online-publications/easy-access-rules-large-aeroplanes-cs-25?page=26",
        "note_zh": "EASA Easy Access Rules 在线条文页，包含操纵器件位置、全行程和推力杆运动方向要求。",
        "note_en": "EASA Easy Access Rules page covering control location, full travel and thrust-lever direction.",
    },
    {
        "id": "easa-cs25-powerplant-controls",
        "kind": "official_certification_specification",
        "quality": "primary",
        "org": "EASA",
        "title_zh": "CS 25.1141 / 25.1143 / 25.1155 动力装置与反推控制",
        "title_en": "CS 25.1141 / 25.1143 / 25.1155 Powerplant and reverse-thrust controls",
        "url": "https://www.easa.europa.eu/en/document-library/easy-access-rules/online-publications/easy-access-rules-large-aeroplanes-cs-25?page=39",
        "note_zh": "EASA 在线条文及 AMC，含反推离开正推力状态的独立动作、飞行包线外防护和告警要求。",
        "note_en": "EASA provisions and AMC for separate reverse selection, out-of-envelope prevention and associated cautions.",
    },
    {
        "id": "caac-ccar25-r4-controls",
        "kind": "official_regulation",
        "quality": "primary",
        "org": "CAAC",
        "title_zh": "CCAR-25-R4《运输类飞机适航标准》",
        "title_en": "CCAR-25-R4 Airworthiness Standards: Transport Category Airplanes",
        "url": "https://www.caac.gov.cn/XXGK/XXGK/MHGZ/201606/P020160622405532063536.pdf",
        "note_zh": "中国民航局官方规章 PDF；本模块引用第25.777、25.779、25.1141、25.1143和25.1155条。",
        "note_en": "Official CAAC regulation PDF; this module cites §§25.777, 25.779, 25.1141, 25.1143 and 25.1155.",
    },
])

SOURCES.extend([
    {
        "id": "patent-us12258138",
        "kind": "patent_document",
        "quality": "primary_document",
        "org": "USPTO publication",
        "title_zh": "US12258138B2：集成视觉指示的飞机油门台",
        "title_en": "US12258138B2: Aircraft throttle quadrant with integrated visual indicator",
        "url": "https://patents.google.com/patent/US12258138B2/en",
        "note_zh": "权利要求涉及手柄内可激活视觉指示、状态响应和用户纠正动作；法律状态须在官方登记簿复核。",
        "note_en": "Claims cover an activatable handle-integrated visual indicator, status response and user corrective action; verify legal status in the official register.",
    },
    {
        "id": "patent-us12162616",
        "kind": "patent_document",
        "quality": "primary_document",
        "org": "USPTO publication",
        "title_zh": "US12162616B2：飞机自动油门飞行员界面",
        "title_en": "US12162616B2: Pilot interface for aircraft autothrottle control",
        "url": "https://patents.google.com/patent/US12162616B2/en",
        "note_zh": "权利要求核心包括随目标动态变化的虚拟卡位及其触觉阻力反馈。",
        "note_en": "Claim focus includes a dynamically positioned virtual detent and associated haptic resisting force.",
    },
    {
        "id": "patent-us10633105",
        "kind": "patent_document",
        "quality": "primary_document",
        "org": "USPTO publication",
        "title_zh": "US10633105B2：带发动机性能调节的自动油门精密作动器",
        "title_en": "US10633105B2: Precision operator for autothrottle with engine-performance adjust",
        "url": "https://patents.google.com/patent/US10633105B2/en",
        "note_zh": "涉及油门杆振动/摇动触觉告警、性能监控及多发推力不平衡提示。",
        "note_en": "Covers throttle-lever vibration/shake alerts, performance monitoring and multi-engine imbalance feedback.",
    },
    {
        "id": "patent-us9043050",
        "kind": "patent_document",
        "quality": "primary_document",
        "org": "USPTO publication",
        "title_zh": "US9043050B2：可编程反推卡位系统",
        "title_en": "US9043050B2: Programmable reverse thrust detent system",
        "url": "https://patents.google.com/patent/US9043050B2/en",
        "note_zh": "涉及可调中间反推卡位、着陆参数、制动系统和目标滑跑距离的联动；公开聚合页显示费用相关失效，仍可能构成现有技术。",
        "note_en": "Covers an adjustable intermediate reverse detent coordinated with landing parameters, braking and rollout distance; an expired right may still be prior art.",
    },
    {
        "id": "patent-us7143984",
        "kind": "patent_document",
        "quality": "primary_document",
        "org": "USPTO publication",
        "title_zh": "US7143984B2：多导轨飞机油门杆",
        "title_en": "US7143984B2: Aircraft throttle lever with multiple guide tracks",
        "url": "https://patents.google.com/patent/US7143984B2/en",
        "note_zh": "涉及正推、反推与辅助连续正推导轨、多个卡位和连接导轨的组合。",
        "note_en": "Covers forward, reverse and auxiliary continuous-forward guide tracks, multiple detents and connector tracks.",
    },
    {
        "id": "patent-cn109606705",
        "kind": "patent_document",
        "quality": "primary_document",
        "org": "CNIPA publication",
        "title_zh": "CN109606705B：可调高度飞机油门台",
        "title_en": "CN109606705B: Height-adjustable aircraft throttle quadrant",
        "url": "https://patents.google.com/patent/CN109606705B/zh",
        "note_zh": "针对身高较矮飞行员复飞时前极限可达性，权利要求涉及可在不同高度固定的安装装置。",
        "note_en": "Addresses forward-limit reach during go-around for shorter pilots through a mounting device fixable at different heights.",
    },
    {
        "id": "patent-cn102452481",
        "kind": "patent_document",
        "quality": "primary_document",
        "org": "CNIPA publication",
        "title_zh": "CN102452481A：自动油门台操纵装置",
        "title_en": "CN102452481A: Automatic throttle-quadrant operating device",
        "url": "https://patents.google.com/patent/CN102452481A/zh",
        "note_zh": "涉及蜗轮蜗杆、摩擦片和电机实现自动/手动控制切换；申请后来视为撤回，但公开内容仍可作为现有技术线索。",
        "note_en": "Uses worm gearing, friction plates and a motor for automatic/manual control; the application was deemed withdrawn but remains a prior-art lead.",
    },
    {
        "id": "patent-cn117542251",
        "kind": "patent_document",
        "quality": "primary_document",
        "org": "CNIPA publication",
        "title_zh": "CN117542251B：一体化仿真油门台",
        "title_en": "CN117542251B: Integrated simulated throttle quadrant",
        "url": "https://patents.google.com/patent/CN117542251B/zh",
        "note_zh": "涉及操纵、信号采集、模式切换、动力输入和电子系统的一体化仿真油门台。",
        "note_en": "Covers an integrated simulator quadrant combining mechanics, sensing, mode switching, power input and electronics.",
    },
    {
        "id": "pilot-asrs-423",
        "kind": "pilot_report_digest",
        "quality": "government_primary",
        "org": "NASA ASRS",
        "title_zh": "ASRS CALLBACK 423：自动油门速度控制问题",
        "title_en": "ASRS CALLBACK 423: Autothrottle speed-control issues",
        "url": "https://asrs.arc.nasa.gov/publications/callback/cb_423.html",
        "note_zh": "飞行员报告显示自动油门断开状态未被及时识别、机组对系统反应预期不一致并导致低速/复飞。",
        "note_en": "Pilot reports describe unrecognized autothrottle disengagement, mismatched expectations and low-speed/go-around consequences.",
    },
    {
        "id": "pilot-asrs-463",
        "kind": "pilot_report_digest",
        "quality": "government_primary",
        "org": "NASA ASRS",
        "title_zh": "ASRS CALLBACK 463：复飞中的自动推力意外",
        "title_en": "ASRS CALLBACK 463: Go-around autothrottle surprise",
        "url": "https://asrs.arc.nasa.gov/publications/callback/cb_463.html",
        "note_zh": "报告描述按下复飞按钮后自动油门指令全推力，飞行员未预期该推力跃变并出现姿态/速度问题。",
        "note_en": "A report describes full thrust after go-around selection, surprising the pilot and contributing to pitch/airspeed difficulty.",
    },
    {
        "id": "pilot-asrs-370",
        "kind": "pilot_report_digest",
        "quality": "government_primary",
        "org": "NASA ASRS",
        "title_zh": "ASRS CALLBACK 370：误触推力杆上的 TO/GA",
        "title_en": "ASRS CALLBACK 370: Inadvertent thrust-lever TO/GA selection",
        "url": "https://asrs.arc.nasa.gov/publications/callback/cb_370.html",
        "note_zh": "报告记录在操作过程中误按推力杆 TO/GA 按钮并引发模式混淆。",
        "note_en": "A report records inadvertent activation of a thrust-lever TO/GA button and resulting mode confusion.",
    },
    {
        "id": "pilot-aaib-gjzhl",
        "kind": "accident_investigation",
        "quality": "government_primary",
        "org": "UK AAIB",
        "title_zh": "AAIB：B737-800 起飞推力不足（G-JZHL）",
        "title_en": "AAIB: B737-800 insufficient takeoff thrust (G-JZHL)",
        "url": "https://www.gov.uk/government/news/aaib-report-boeing-737-800-g-jzhl-insufficient-thrust-during-takeoff",
        "note_zh": "TO/GA 未按下、机组受惊与分心导致推力保留在较低设置；AAIB 指出现有防护不充分。",
        "note_en": "TO/GA was not pressed amid startle and distraction, leaving thrust low; AAIB found current barriers insufficient.",
    },
    {
        "id": "pilot-aaib-gviit",
        "kind": "accident_investigation",
        "quality": "government_primary",
        "org": "UK AAIB",
        "title_zh": "AAIB：B777 在 V1 附近误收推力（G-VIIT）",
        "title_en": "AAIB: B777 inadvertent thrust reduction near V1 (G-VIIT)",
        "url": "https://www.gov.uk/aaib-reports/aaib-investigation-to-boeing-777-236-g-viit",
        "note_zh": "副驾驶在 V1 附近开始收推力而非把手移开，体现高工作负荷阶段动作滑误风险。",
        "note_en": "The copilot began retarding the levers near V1 instead of removing the hand, illustrating action-slip risk in a high-workload phase.",
    },
    {
        "id": "google-patents-bigquery",
        "kind": "prior_art_corpus",
        "quality": "official_dataset",
        "org": "Google LLC / IFI CLAIMS",
        "title_zh": "Google Patents 公开数据集（BigQuery patents-public-data）",
        "title_en": "Google Patents Public Data (BigQuery patents-public-data)",
        "url": "https://console.cloud.google.com/marketplace/details/google_patents_public_datasets/patents-public-data",
        "note_zh": "Google Patents 公开数据集，CC BY 4.0 许可，含中美欧等多国专利全文与书目；本库历史切片取 B64D13/00+B60K26/00+B60K41/00 且 filing_date >= 20000101。B64D13/00 已在本体层标为非油门台核心范围，保留原始记录但不自动进入跨源事实口径。中文字段为 BigQuery 多语种原文，非翻译。[archive_policy=download]",
        "note_en": "Google Patents public dataset under CC BY 4.0. The historical slice used B64D13/00, B60K26/00 and B60K41/00 with filing_date >= 20000101. B64D13/00 is now marked out of scope for throttle controls; records remain searchable but cannot enter cross-source fact output automatically. Chinese fields are source multilingual text, not translations. [archive_policy=download]",
        "license": "CC BY 4.0",
        "disclaimer_zh": "先有技术检索辅助，不构成新颖性、创造性、自由实施或侵权法律意见。",
        "disclaimer_en": "Prior-art search aid only; not a novelty, inventive-step, freedom-to-operate or infringement opinion.",
    },
])


# ===== 知识库扩展接入（2026-07-28）：14 个新来源 =====
# 守纪律 1：每个新来源必须挂精确 URL + 进 sources 表
# 守纪律 2：archive_policy 标记放 note_zh 末尾，metadata_only 的来源不下载只登记
# 来源：data/knowledge_base/SOURCE_REGISTRY.md
SOURCES.extend([
    {
        "id": "triz-40-principles",
        "kind": "academic_reference",
        "quality": "primary",
        "org": "MATRIZ",
        "title_zh": "TRIZ 40 条发明原理（Altshuller 经典体系）",
        "title_en": "TRIZ 40 Inventive Principles (Altshuller canon)",
        "url": "https://matriz.org/training-tools/triz-40-principles/",
        "note_zh": "Altshuller 40 原理由 MATRIZ（国际 TRIZ 协会）官方维护，是 TRIZ 方法的原始权威出处。[archive_policy=download]",
        "note_en": "The 40 principles maintained by MATRIZ as the canonical TRIZ reference.",
    },
    {
        "id": "wipo-cpc-scheme",
        "kind": "ontology_schema",
        "quality": "government_primary",
        "org": "WIPO / EPO",
        "title_zh": "CPC 合作专利分类表",
        "title_en": "Cooperative Patent Classification Scheme",
        "url": "https://www.cooperativepatentclassification.org/index",
        "note_zh": "CPC 由 WIPO 与 EPO 联合维护，提供完整分类表下载。本库只取与油门台相关的子组。[archive_policy=download]",
        "note_en": "Official CPC scheme maintained jointly by WIPO and EPO.",
    },
    {
        "id": "cnipa-patent-law-2020",
        "kind": "legal_statute",
        "quality": "government_primary",
        "org": "CNIPA",
        "title_zh": "中华人民共和国专利法（2020 年第四次修正）",
        "title_en": "Patent Law of the People's Republic of China (4th amendment, 2020)",
        "url": "https://www.cnipa.gov.cn/col/col86/index.html",
        "note_zh": "国家知识产权局官方发布的 2020 年第四次修正版专利法。[archive_policy=download]",
        "note_en": "CNIPA official 2020 fourth-amendment Patent Law.",
    },
    {
        "id": "cnipa-patent-examination-guidelines-2023",
        "kind": "legal_statute",
        "quality": "government_primary",
        "org": "CNIPA",
        "title_zh": "专利审查指南（2023 年修订）",
        "title_en": "Patent Examination Guidelines (2023 revision)",
        "url": "https://www.cnipa.gov.cn/col/col489/index.html",
        "note_zh": "国家知识产权局 2023 年 12 月 21 日发布、2024 年 1 月 20 日生效。[archive_policy=download]",
        "note_en": "CNIPA Patent Examination Guidelines 2023 revision.",
    },
    {
        "id": "uspto-35-usc-aia",
        "kind": "legal_statute",
        "quality": "government_primary",
        "org": "USPTO / Cornell LII",
        "title_zh": "美国法典第 35 卷（专利法）AIA 版本",
        "title_en": "35 U.S.C. (Patents), Leahy-Smith America Invents Act version",
        "url": "https://www.law.cornell.edu/uscode/text/35",
        "note_zh": "35 USC 由 Cornell LII 维护公开版本，AIA 2011 后版本为现行。[archive_policy=download]",
        "note_en": "35 USC maintained by Cornell LII; AIA version is current.",
    },
    {
        "id": "uspto-mpep-9th",
        "kind": "legal_statute",
        "quality": "government_primary",
        "org": "USPTO",
        "title_zh": "美国专利审查程序手册（MPEP 第 9 版，2024 年修订）",
        "title_en": "Manual of Patent Examining Procedure (MPEP, 9th ed., 2024 rev.)",
        "url": "https://www.uspto.gov/web/offices/pac/mpep/index.html",
        "note_zh": "USPTO 官方 MPEP。[archive_policy=download]",
        "note_en": "USPTO official MPEP 9th edition.",
    },
    {
        "id": "us-supreme-court-patent-cases",
        "kind": "legal_statute",
        "quality": "government_primary",
        "org": "U.S. Supreme Court / Cornell LII",
        "title_zh": "美国专利相关判例集（Alice, Mayo, KSR, Nautilus 等）",
        "title_en": "U.S. patent-related case law collection",
        "url": "https://www.law.cornell.edu/supct/html/13-298.html",
        "note_zh": "Alice Corp. v. CLS Bank（573 U.S. 208, 2014）作为客体资格两步法的代表性判例。[archive_policy=download]",
        "note_en": "Alice Corp. v. CLS Bank as the representative subject-matter eligibility case.",
    },
    {
        "id": "sae-arp4761",
        "kind": "industry_standard",
        "quality": "primary",
        "org": "SAE International",
        "title_zh": "SAE ARP4761 民用机载系统安全性评估过程指南",
        "title_en": "SAE ARP4761 Guidelines for Methods of Safety Assessment Process",
        "url": "https://www.sae.org/standards/content/arp4761/",
        "note_zh": "ARP4761 定义了 Catastrophic / Hazardous / Major / Minor / No-Safety-Effect 五级失效分类。[archive_policy=metadata_only]",
        "note_en": "ARP4761 defines five-level failure classification. SAE paid standard.",
    },
    {
        "id": "sae-arp5580",
        "kind": "industry_standard",
        "quality": "primary",
        "org": "SAE International",
        "title_zh": "SAE ARP5580 故障模式影响分析（FMEA）",
        "title_en": "SAE ARP5580 Recommended Failure Modes and Effects Analysis",
        "url": "https://www.sae.org/standards/content/arp5580/",
        "note_zh": "SAE 付费标准，仅登记 URL 不下载。[archive_policy=metadata_only]",
        "note_en": "SAE paid standard; metadata only.",
    },
    {
        "id": "nasa-tlx",
        "kind": "academic_reference",
        "quality": "primary",
        "org": "NASA ARC",
        "title_zh": "NASA 任务负荷指数（NASA-TLX）",
        "title_en": "NASA Task Load Index",
        "url": "https://humansystems.arc.nasa.gov/groups/TLX/",
        "note_zh": "Hart & Staveland 1988 原始论文由 NASA ARC 官方页面提供。[archive_policy=download]",
        "note_en": "Hart & Staveland 1988 original paper hosted by NASA ARC.",
    },
    {
        "id": "cooper-harper-1969",
        "kind": "academic_reference",
        "quality": "primary",
        "org": "NASA / Cornell e-Commons",
        "title_zh": "Cooper-Harper 飞行品质评级（1969 原始论文）",
        "title_en": "Cooper-Harper Handling Qualities Rating",
        "url": "https://commons.erau.edu/space-congress-proceedings/proceedings-1969-6th-v1/6th-V1-7/",
        "note_zh": "Cooper & Harper 1969 原始论文。[archive_policy=download]",
        "note_en": "Cooper & Harper 1969 original paper.",
    },
    {
        "id": "faa-ac-25-1302",
        "kind": "official_regulation",
        "quality": "government_primary",
        "org": "FAA",
        "title_zh": "FAA AC 25.1302 驾驶舱系统人为因素",
        "title_en": "FAA AC 25.1302 Human Factors for Cockpit Systems",
        "url": "https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.information/documentID/1041470",
        "note_zh": "FAA 咨询通报。[archive_policy=download]",
        "note_en": "FAA Advisory Circular.",
    },
    {
        "id": "ntsb-aviation-database",
        "kind": "accident_investigation",
        "quality": "government_primary",
        "org": "NTSB",
        "title_zh": "NTSB 航空事故数据库",
        "title_en": "NTSB Aviation Accident Database & Synopses",
        "url": "https://data.ntsb.gov/avdata/",
        "note_zh": "NTSB 公开 API。[archive_policy=download]",
        "note_en": "NTSB public aviation accident data API.",
    },
    {
        "id": "nasa-asrs-database",
        "kind": "pilot_report_digest",
        "quality": "government_primary",
        "org": "NASA ASRS",
        "title_zh": "NASA 航空安全报告系统数据库",
        "title_en": "NASA Aviation Safety Reporting System Database",
        "url": "https://asrs.arc.nasa.gov/search/database.html",
        "note_zh": "NASA ASRS 公开检索。[archive_policy=download]",
        "note_en": "NASA ASRS public search.",
    },
    {
        "id": "uk-aaib-bulletins",
        "kind": "accident_investigation",
        "quality": "government_primary",
        "org": "UK AAIB",
        "title_zh": "UK AAIB 调查通报库",
        "title_en": "UK Air Accidents Investigation Branch bulletins",
        "url": "https://www.gov.uk/aaib-reports",
        "note_zh": "GOV.UK 公开通报。[archive_policy=download]",
        "note_en": "GOV.UK public bulletins.",
    },
    {
        "id": "ata-ispec-2200",
        "kind": "industry_standard",
        "quality": "primary",
        "org": "ATA",
        "title_zh": "ATA iSpec 2200 / ATA-100 章节分类",
        "title_en": "ATA iSpec 2200 / ATA-100 Chapter Classification",
        "url": "https://www.ata.org/",
        "note_zh": "ATA-100 章节分类是航空业事实标准。ATA iSpec 2200 是付费标准，仅登记 URL。[archive_policy=metadata_only]",
        "note_en": "ATA-100 chapter classification as aviation industry de facto standard.",
    },
    {
        "id": "w3c-skos-reference",
        "kind": "ontology_schema",
        "quality": "primary",
        "org": "W3C",
        "title_zh": "W3C SKOS 简易知识组织系统参考",
        "title_en": "W3C SKOS Simple Knowledge Organization System Reference",
        "url": "https://www.w3.org/TR/skos-reference/",
        "note_zh": "W3C SKOS 标准。[archive_policy=download]",
        "note_en": "W3C SKOS standard.",
    },
    {
        "id": "w3c-rdf-schema",
        "kind": "ontology_schema",
        "quality": "primary",
        "org": "W3C",
        "title_zh": "W3C RDF Schema 1.1",
        "title_en": "W3C RDF Schema 1.1",
        "url": "https://www.w3.org/TR/rdf-schema/",
        "note_zh": "W3C RDF Schema 标准。[archive_policy=download]",
        "note_en": "W3C RDF Schema standard.",
    },
    {
        "id": "w3c-owl2-overview",
        "kind": "ontology_schema",
        "quality": "primary",
        "org": "W3C",
        "title_zh": "W3C OWL 2 概览",
        "title_en": "W3C OWL 2 Web Ontology Language Document Overview (Second Edition)",
        "url": "https://www.w3.org/TR/owl2-overview/",
        "note_zh": "W3C OWL 2 标准。[archive_policy=download]",
        "note_en": "W3C OWL 2 standard.",
    },
    {
        "id": "hqy-curated-ontology",
        "kind": "curated_ontology",
        "quality": "curated",
        "org": "HQY Throttle Atlas",
        "title_zh": "HQY 油门台专利助手工程本体 v1",
        "title_en": "HQY Throttle Atlas Engineering Ontology v1",
        "url": "local://ontology/hqy-throttle-atlas-v1",
        "note_zh": "项目内部整理的飞机族、油门台组件、法规条款与 CPC 范围本体。[archive_policy=metadata_only]",
        "note_en": "Project-curated aircraft, throttle-component, regulatory-clause and CPC scope ontology.",
        "license": "Project internal curated data",
        "disclaimer_zh": "仅用于工程检索和概念对齐，不替代适航、法律或原厂设计结论。",
        "disclaimer_en": "For engineering retrieval and concept alignment only; not an airworthiness, legal or OEM design determination.",
    },
])


CHUNKS = [
    ("油门台是什么", "What is a throttle quadrant", "油门台是飞行员管理发动机功率或推力的主要人机界面。它通常包含一个或多个推力手柄，并可能集成反推、配平、自动油门断开、TO/GA、通信、传感器或武器控制。民航设计强调标准程序、双人协作、触觉卡位和自动飞行耦合；军机设计更强调 HOTAS，使飞行员在高负荷环境中不离开油门与操纵杆。", "A throttle quadrant is the primary human-machine interface for managing engine power or thrust. It may integrate reverse thrust, trim, autothrottle disconnect, TO/GA, communications, sensors or weapon controls. Civil designs emphasize procedures, crew coordination, tactile detents and autoflight coupling, while combat aircraft emphasize HOTAS.", "faa-phak"),
    ("推力手柄与自动推力", "Thrust levers and autothrust", "自动推力并不意味着所有飞机的手柄都会自动移动。A320 系列用手柄卡位表达推力上限，自动推力在该范围内调节；737NG 的经典设计则让自动油门动作可在主油门手柄上观察。比较时应区分“系统控制的推力”和“手柄是否物理运动”。", "Autothrust does not mean that every aircraft's levers physically move. A320-family detents command thrust limits while autothrust works within that range; the classic 737NG design makes autothrottle action observable at the levers. Compare commanded thrust separately from physical lever motion.", "airbus-safety-flare"),
    ("A320 手柄为何不随自动推力移动", "Why A320 levers do not move with autothrust", "FAA 资料明确说明，A320 推力手柄在正常自动推力运行中放入所需卡位后保持不动，系统没有用于手柄的自动推力反向驱动。发动机推力改变时，手柄不会跟随移动；飞行员可通过发动机显示监控实际推力。", "FAA material explains that A320 thrust levers are placed in the required detent and left there during normal autothrust. There is no autothrust backdrive, so the levers do not move when engine thrust changes.", "faa-a320-autothrust"),
    ("737 自动油门与手柄运动", "737 autothrottle and lever motion", "FAA 托管的 NTSB 737 报告说明，自动油门会移动推力手柄，以保持飞行员或系统选定的空速与推力设置。这种可见、可触觉的手柄运动与 A320 固定卡位式自动推力构成直观对比。", "An FAA-hosted NTSB 737 report states that autothrottle moves the thrust levers to maintain pilot- or system-selected airspeeds and thrust settings. That visible, tactile movement contrasts with the A320 fixed-detent philosophy.", "ntsb-737-autothrottle"),
    ("A320 着陆推力管理", "A320 landing thrust management", "空客 Safety First 说明，A320/A330/A340/A350/A380 在拉平时的 RETARD 是提示而非命令；飞行员应在接地前将推力手柄收到 IDLE，以满足地面扰流板等系统逻辑。自动推力在手柄未收到 IDLE 前仍可保持目标速度。", "Airbus Safety First explains that RETARD is a reminder rather than an order. The pilot should move thrust levers to IDLE by touchdown; until then, autothrust can continue targeting approach speed.", "airbus-safety-flare"),
    ("A320 起飞推力卡位", "A320 takeoff thrust detents", "A320 的起飞推力设置通过双手柄同步移动到相应卡位完成。公开安全资料讨论了两步推力应用、发动机稳定和避免不对称加速的重要性。", "A320 takeoff thrust is set by moving both levers together into the relevant detent. Airbus safety material discusses two-step application, engine stabilization and avoiding asymmetric acceleration.", "airbus-takeoff"),
    ("空客驾驶舱共通性", "Airbus cockpit commonality", "空客强调 A320、A330、A350、A380 等电传机型在驾驶舱布局和操作理念上的共通性。对训练台架而言，共通性意味着卡位、标识、行程和程序反馈应保持一致，而不仅是外观相似。", "Airbus emphasizes cockpit and operational commonality across fly-by-wire families. For training hardware, commonality means consistent detents, labeling, travel and procedural feedback—not just a similar appearance.", "airbus-cockpits"),
    ("737NG 飞行甲板理念", "737NG flight deck philosophy", "波音官方资料强调飞行甲板自动化用于减轻例行工作，同时保持飞行员的态势感知和最终操纵权。737NG 的油门台常被用于对比移动式自动油门与空客固定卡位式自动推力理念。", "Boeing describes automation as reducing routine workload while keeping pilots aware and in authority. The 737NG quadrant is often contrasted with Airbus fixed-detent autothrust because its automatic action is observable at the levers.", "boeing-737ng"),
    ("C919 公开资料边界", "C919 public-information boundary", "中国商飞公开培训目录确认 C919 训练包含驾驶舱图、面板图、快速检查单和飞行机组操作手册。由于完整控制逻辑并未在该公开页面披露，本库对 C919 的油门卡位、自动运动等细节使用“未充分披露”标记，而不是推测。", "COMAC's public training catalog confirms cockpit diagrams, panel diagrams, quick checklists and flight-crew manuals. Because detailed control logic is not disclosed on that page, this library marks specific detents and automatic motion as insufficiently disclosed rather than guessing.", "comac-training"),
    ("F-16 人机工程", "F-16 cockpit ergonomics", "美国空军资料说明 F-16 使用电传飞控和右侧操纵杆，以便在高过载机动中进行准确控制。左手油门与右手侧杆共同形成经典 HOTAS 工作流，使常用任务功能在不离开主操纵器的情况下完成。", "The U.S. Air Force describes the F-16's fly-by-wire and right-side controller for accurate high-G control. Its left throttle and right side-stick create a classic HOTAS workflow for common mission actions.", "usaf-f16"),
    ("F/A-18E 舰载双发", "F/A-18E carrier twin-engine context", "美国海军将 F/A-18E/F 定义为双发、舰载、多任务战术飞机。双发分体油门有利于独立发动机管理；舰载环境还要求在高工作负荷下快速、可触觉确认的控制。具体开关映射会随批次和构型变化。", "The U.S. Navy defines the F/A-18E/F as a twin-engine, carrier-suitable multirole tactical aircraft. Split throttles support independent engine management, while carrier operations reward rapid, tactile control. Exact switch mapping varies with block and configuration.", "usn-fa18"),
    ("台风 VTAS", "Typhoon VTAS", "Eurofighter 官方将台风的控制概念描述为 HOTAS 加直接语音输入，即 Voice, Throttle and Stick。其目标是在高负荷空空、空地和多用途任务中，让飞行员无需离开主飞行控制器或低头寻找开关即可执行关键功能。", "Eurofighter describes Typhoon's concept as HOTAS plus Direct Voice Input: Voice, Throttle and Stick. It supports critical actions without removing hands from the primary flight controls or looking down during demanding missions.", "eurofighter-features"),
    ("阵风 HOTAS", "Rafale HOTAS", "达索航空说明阵风的人机界面以高度集成 HOTAS 为核心，并与抬头显示、头盔显示和战术显示的视觉转换相协调。设计目标是综合信息、降低飞行员负荷并加快战术决策。", "Dassault describes Rafale's HMI as a highly integrated HOTAS concept coordinated with head-up, helmet and tactical displays to synthesize information, reduce workload and speed decisions.", "dassault-rafale"),
    ("鹰狮信息融合", "Gripen information fusion", "萨博官方资料强调鹰狮 C 的 Link 16、战术数据链、共享传感器融合数据、嵌入式决策支持和优化座舱 HMI。油门台因此不是孤立机械部件，而是任务信息交互链的一部分。", "Saab highlights Link 16, tactical datalinks, shared sensor-fused data, embedded decision support and an optimized cockpit HMI. The throttle is therefore part of a mission-information interaction chain, not an isolated mechanism.", "saab-gripen"),
    ("苏-35S 公开信息", "Su-35S public information", "UAC 官方资料确认苏-35 是双发多用途战斗机，采用数字发动机控制、现代通信和高速数据交换。公开页面没有给出完整油门开关映射，因此本库只对双发、加力、数字控制等高层特征作比较，并将具体 HOTAS 细节标为有限证据。", "UAC confirms the Su-35 as a twin-engine multirole fighter with digital engine control, modern communications and high-speed data exchange. The public page does not provide a full throttle switch map, so this library compares only high-level features and marks detailed HOTAS claims as limited.", "uac-su35"),
    ("民航与军用油门差异", "Civil versus combat throttles", "民航油门台通常围绕发动机功率、自动推力、反推和标准操作程序设计，强调双人可见性、误操作防护和卡位一致性。战斗机油门通常是 HOTAS 的一半，除推力外还承载通信、雷达、传感器、武器、对抗等任务输入。", "Civil quadrants center on engine power, autothrust, reverse thrust and SOPs, with crew visibility, error prevention and consistent detents. Fighter throttles are one half of HOTAS and often carry communications, radar, sensor, weapon and defensive inputs.", "faa-phak"),
    ("三维模型说明", "3D model disclaimer", "应用中的三维外形为依据公开照片和高层功能特征制作的参数化示意模型，用于比较手柄数量、基座比例、分体方式和功能密度。它们不是原厂 CAD，不包含制造尺寸、内部机构或受限技术数据，也不应作为适航、维修或制造依据。", "The 3D shapes are parametric conceptual models based on public photographs and high-level features. They compare lever count, base proportion, split configuration and control density. They are not OEM CAD and must not be used for airworthiness, maintenance or manufacturing.", "img-a320"),
    ("RAG 数据结构", "RAG data structure", "本地知识库将来源、文档和检索片段分离保存。每个片段保留 source_id，可回溯到组织、标题、链接、来源类型和可靠性。当前检索使用离线关键词评分；后续可在不改 UI 的情况下为 chunks 表增加 embedding 字段并连接本地或云端向量模型。", "The local knowledge base stores sources, documents and retrievable chunks separately. Every chunk retains source_id for traceability. Search currently uses offline lexical scoring; an embedding field and local or hosted vector model can be added later without changing the UI.", "faa-phak"),
]

COMPONENTS = [
    {
        "id": "forward_lever", "icon": "↗", "order_index": 1,
        "name_zh": "正推力杆", "name_en": "Forward thrust lever",
        "description_zh": "正推力方向、可达性、防混淆与多发操纵",
        "description_en": "Direction, reach, confusion prevention and multi-engine control",
    },
    {
        "id": "reverse_lever", "icon": "↙", "order_index": 2,
        "name_zh": "反推力杆", "name_en": "Reverse-thrust lever",
        "description_zh": "反推选择、防误动、飞行包线与告警",
        "description_en": "Reverse selection, inadvertent operation, flight envelope and cautions",
    },
    {
        "id": "flight_idle_gate", "icon": "⊣", "order_index": 3,
        "name_zh": "飞行慢车门锁", "name_en": "Flight-idle gate",
        "description_zh": "确实锁止、止动与“另一个明显动作”",
        "description_en": "Positive lock/stop and a separate, distinct action",
    },
    {
        "id": "engine_grouping", "icon": "Ⅱ", "order_index": 4,
        "name_zh": "多发分控 / 联控", "name_en": "Multi-engine grouping",
        "description_zh": "每台发动机独立控制并可同时操纵",
        "description_en": "Independent control of each engine plus simultaneous control",
    },
    {
        "id": "fuel_cutoff", "icon": "×", "order_index": 5,
        "name_zh": "燃油切断联锁", "name_en": "Fuel-cutoff interlock",
        "description_zh": "从慢车进入断油位置的防误操作设计",
        "description_en": "Error-resistant transition from idle into fuel cutoff",
    },
    {
        "id": "retention_layout", "icon": "◎", "order_index": 6,
        "name_zh": "保持 / 布局机构", "name_en": "Retention and layout",
        "description_zh": "防滑移、强度刚度、人员活动与全行程空间",
        "description_en": "Creep resistance, strength, crew movement and full travel",
    },
]


def regulation(
    item_id, component_id, authority, rule_ref, source_id, status_zh, status_en,
    applicability_zh, applicability_en, requirement_zh, requirement_en,
    interpretation_zh, interpretation_en, difference_zh, difference_en, order_index,
):
    return {
        "id": item_id, "component_id": component_id, "authority": authority,
        "rule_ref": rule_ref, "source_id": source_id,
        "status_zh": status_zh, "status_en": status_en,
        "applicability_zh": applicability_zh, "applicability_en": applicability_en,
        "requirement_zh": requirement_zh, "requirement_en": requirement_en,
        "interpretation_zh": interpretation_zh, "interpretation_en": interpretation_en,
        "difference_zh": difference_zh, "difference_en": difference_en,
        "order_index": order_index,
    }


# 离线降级数据：AirworthinessKB API 不可用时使用
# 仅当 API 不可达时启用，正常工作流走 build_regulatory_constraints() 实时同步
FALLBACK_REGULATORY_CONSTRAINTS = [
    regulation(
        "forward-faa", "forward_lever", "FAA",
        "14 CFR §§25.777(a)–(d), 25.779(b)(1), 25.1143(a)–(c)",
        "faa-25-flightdeck-controls", "法规正文", "Binding regulation",
        "美国运输类飞机；具体修订版由审定基础确定",
        "U.S. transport-category airplanes; amendment level is certification-basis specific",
        "操纵器件须便于操作并防止混淆和误动；正推力杆前移应增大正推力。各发动机须有单独推力控制，并能同时操纵全部发动机；相同发动机控制的布局不得造成发动机混淆。",
        "Controls must be convenient and resist confusion and inadvertent operation; forward motion must increase forward thrust. Each engine needs a separate control, while simultaneous control of all engines must remain possible.",
        "台架应验证推力增加方向、左右发动机映射、手柄全行程可达性及双杆同步握持。标签、间距和形态应让机组快速识别所控发动机。",
        "Verify thrust-increase direction, left/right engine mapping, full-travel reach and one-hand simultaneous movement. Labels, spacing and form should make engine identity unmistakable.",
        "三方共同基线；FAA 明确给出 5 ft 2 in–6 ft 3 in 的机组身高范围。",
        "Common three-authority baseline; FAA explicitly states a 5 ft 2 in–6 ft 3 in crew-stature range.",
        1,
    ),
    regulation(
        "forward-easa", "forward_lever", "EASA",
        "CS 25.777(a)–(c), CS 25.779(b)(1), CS 25.1143(a)–(c)",
        "easa-cs25-flightdeck-controls", "认证规范", "Certification specification",
        "EASA CS-25 大型飞机；适用修订版由项目审定基础确定",
        "EASA CS-25 large aeroplanes; amendment level is project-specific",
        "操纵器件须便于操作并防止混淆、疏忽操作；正推力杆前移增大正推力。每台发动机须有单独控制，并能分别或同时操纵所有发动机，控制响应须确实且及时。",
        "Controls must be convenient and prevent confusion or inadvertence; forward motion increases forward thrust. Each engine needs a separate control, with both individual and simultaneous operation and positive, immediate response.",
        "除了几何行程，还应把卡位触感、发动机编号、双杆联动手感和从任一驾驶员位置的操作纳入人因验证。",
        "Beyond geometry, validate tactile detents, engine identification, paired-lever feel and operation from each pilot position.",
        "方向与分控/联控要求基本等同 FAA；EASA 的 AMC 提供符合性解释，AMC 本身不是唯一设计方案。",
        "Direction and grouping largely align with FAA; EASA AMC offers acceptable means, not the only possible design.",
        2,
    ),
    regulation(
        "forward-caac", "forward_lever", "CAAC",
        "CCAR-25-R4 §§25.777(a)–(d), 25.779(b)(1), 25.1143(a)–(c)",
        "caac-ccar25-r4-controls", "法规正文", "Binding regulation",
        "中国运输类飞机；适用规章修订版由型号审定基础确定",
        "Chinese transport-category airplanes; the applicable revision is certification-basis specific",
        "驾驶舱操纵器件须操作方便并防止混淆和误动；油门杆前移使正推力增大、后移使反推力增大。每台发动机须有单独控制，并能分别或同时操纵所有发动机。",
        "Cockpit controls must be convenient and resist confusion and inadvertent operation; forward motion increases forward thrust and rearward motion increases reverse thrust. Each engine requires separate and simultaneous control capability.",
        "台架尺寸应覆盖身高 158–190 cm 的最小机组成员在系紧约束系统时的全行程操作，并避免驾驶舱结构或衣着干涉。",
        "The rig should demonstrate unrestricted full travel for 158–190 cm minimum crew members while restrained, without cockpit-structure or clothing interference.",
        "与 FAA 基线高度一致；CCAR-25-R4直接给出 158–190 cm 的人体尺寸范围。",
        "Closely aligned with the FAA baseline; CCAR-25-R4 states the 158–190 cm stature range directly.",
        3,
    ),
    regulation(
        "reverse-faa", "reverse_lever", "FAA",
        "14 CFR §§25.779(b)(1), 25.1155",
        "faa-25-reverse", "法规正文", "Binding regulation",
        "美国运输类飞机的反推或低于飞行状态桨距控制",
        "Reverse-thrust or below-flight-regime pitch controls on U.S. transport-category airplanes",
        "每个反推控制必须防止误动；飞行慢车处必须有确实的锁或止动器，并要求机组采取另一个明显动作才能离开正推力状态。",
        "Each reverse control must prevent inadvertent operation, provide a positive lock or stop at flight idle, and require a separate and distinct crew operation to leave the forward-thrust regime.",
        "不能让一次连续后拉动作直接跨过慢车进入反推。可采用独立反推小手柄、需主动抬起的闩锁或明确改变操作方向的机构。",
        "A single continuous pull must not pass directly through idle into reverse. A separate reverse lever, deliberate latch lift or clear change in operating direction can create the distinct action.",
        "FAA 条文给出核心门槛，但不像当前 EASA CS 25.1155 那样逐项写出飞行包线外防护及告警。",
        "FAA states the core gate requirement but does not enumerate the same out-of-envelope prevention and caution set as current EASA CS 25.1155.",
        1,
    ),
    regulation(
        "reverse-easa", "reverse_lever", "EASA",
        "CS 25.1155(a)–(e); AMC 25.1155",
        "easa-cs25-powerplant-controls", "认证规范", "Certification specification",
        "EASA CS-25 大型飞机的反推或低于飞行状态桨距控制",
        "Reverse-thrust or below-flight-regime pitch controls on CS-25 large aeroplanes",
        "除飞行慢车锁止和独立动作外，还须防止在批准的飞行中反推包线之外有意或无意选择/激活反推；不得提供超控。防护丧失须极不可能，并须在丧失防护或控制器在包线外进入反推位置时给出注意告警（机械阻挡满足条件时可例外）。",
        "Beyond the flight-idle gate and separate action, reverse selection or activation—intentional or inadvertent—must be prevented outside the approved in-flight envelope, without override. Loss of prevention must be remote and cautions are required for loss or out-of-envelope control displacement, subject to the mechanical-baulk exception.",
        "设计审查须同时覆盖机械门锁、逻辑联锁、传感器失效概率、告警时机和机组误操作。AMC 明确：可预加载的闩锁或可在到达 Flight Idle 前解除的动作不合格。",
        "Review the mechanical gate, logic interlock, sensor-failure probability, caution timing and crew error together. AMC specifically rejects pre-loadable latches or actions that can be completed before Flight Idle.",
        "三方中最明确：增加飞行包线外防护、禁止超控、故障概率和告警条款。",
        "The most explicit of the three: it adds out-of-envelope prevention, no override, failure-probability and caution requirements.",
        2,
    ),
    regulation(
        "reverse-caac", "reverse_lever", "CAAC",
        "CCAR-25-R4 §25.1155; §25.779(b)(1)",
        "caac-ccar25-r4-controls", "法规正文", "Binding regulation",
        "中国运输类飞机的反推或低于飞行状态桨距控制",
        "Reverse-thrust or below-flight-regime pitch controls on Chinese transport-category airplanes",
        "反推控制必须防止误动；飞行慢车位置须有确实的锁或止动器，并要求机组采取另外明显动作，才能将控制器从正推力状态移开。",
        "Reverse controls must resist inadvertent operation, have a positive lock or stop at flight idle, and require an additional distinct crew action to leave the positive-thrust regime.",
        "台架验收应证明正常后拉不会误入反推，门锁在磨损、振动和典型握持方式下仍提供清晰阻挡，并能被机组有意识解除。",
        "Rig acceptance should show that normal aft movement cannot enter reverse and that the gate remains a clear barrier under wear, vibration and representative grips while allowing deliberate release.",
        "核心门锁要求与 FAA 对齐；具体型号仍可能通过专用条件或审定文件增加要求。",
        "The core gate aligns with FAA; project-specific conditions or certification material may add requirements.",
        3,
    ),
    regulation(
        "idle-faa", "flight_idle_gate", "FAA",
        "14 CFR §§25.1143(e), 25.1155",
        "faa-25-reverse", "法规正文", "Binding regulation",
        "美国运输类飞机的反推门锁；若推力控制含燃油切断，也适用于慢车—断油过渡",
        "U.S. transport-category reverse gate and, where integrated, idle-to-fuel-cutoff transition",
        "飞行慢车处必须有确实的锁或止动器；跨入反推或断油区域必须通过另一个明显动作。",
        "A positive lock or stop is required at flight idle; entry into reverse or cutoff requires a separate and distinct action.",
        "“有卡点”不等于“确实锁止”。应通过力—位移曲线、错误序列试验、磨损容差和手套/单手操作验证门锁不能被无意越过。",
        "A tactile bump is not necessarily a positive lock. Use force-travel data, erroneous-sequence tests, wear tolerances and representative hand/glove trials to show the gate cannot be crossed inadvertently.",
        "适用于反推门锁和集成式燃油切断门锁两个边界。",
        "Applies at both the reverse gate and an integrated fuel-cutoff gate.",
        1,
    ),
    regulation(
        "idle-easa", "flight_idle_gate", "EASA",
        "CS 25.1143(e), CS 25.1155(a); AMC 25.1155",
        "easa-cs25-powerplant-controls", "认证规范", "Certification specification",
        "EASA CS-25 大型飞机",
        "EASA CS-25 large aeroplanes",
        "只有到达 Flight Idle 后，才能执行离开正推力状态的另一个明显动作。可接受示例包括独立正/反推手柄、在 Flight Idle 才能动作的闩锁，或操作方向的明确改变。",
        "The separate and distinct action to leave forward thrust may occur only after Flight Idle. Acceptable examples include separate forward/reverse levers, a latch operable only at Flight Idle, or a clear change in operating direction.",
        "避免可提前捏住或预加载的闩锁；磨损不得把“两步动作”退化为一次连续动作。台架应将这一序列作为独立测试用例。",
        "Avoid latches that can be held or pre-loaded early; wear must not turn two actions into one continuous motion. Make this sequence a dedicated rig test.",
        "EASA AMC 对“另一个明显动作”的可接受与不可接受机构给出最具体的人因解释。",
        "EASA AMC gives the clearest acceptable/unacceptable human-factors examples for the distinct action.",
        2,
    ),
    regulation(
        "idle-caac", "flight_idle_gate", "CAAC",
        "CCAR-25-R4 §§25.1143(e), 25.1155",
        "caac-ccar25-r4-controls", "法规正文", "Binding regulation",
        "中国运输类飞机",
        "Chinese transport-category airplanes",
        "慢车位置须有确实的锁或止动器；进入断油或离开正推力状态均须另外的明显动作。",
        "A positive lock or stop is required at idle; entry into cutoff or departure from positive thrust requires an additional distinct action.",
        "设计记录应明确哪个零件承担“确实锁止”、哪个动作构成“另外明显动作”，并验证制造公差和磨损后的功能。",
        "Design records should identify the part providing the positive lock and the action providing the distinct operation, with manufacturing-tolerance and worn-condition verification.",
        "用语和核心意图与 FAA 接近。",
        "Wording and core intent closely track FAA.",
        3,
    ),
    regulation(
        "group-faa", "engine_grouping", "FAA",
        "14 CFR §§25.777(d), 25.1143(a)–(c)",
        "faa-25-powerplant-controls", "法规正文", "Binding regulation",
        "美国多发运输类飞机",
        "U.S. multi-engine transport-category airplanes",
        "每台发动机须有单独的推力控制，排列要支持分别操纵各发动机和同时操纵全部发动机；相同控制的布局必须防止发动机混淆，响应须确实且及时。",
        "Each engine requires a separate thrust control. The arrangement must permit individual and simultaneous operation, prevent engine confusion, and provide positive and immediate response.",
        "手柄间距既要允许分体差动，又要允许一手成组推动；发动机编号、左右顺序和控制—响应映射应在正常及故障场景中一致。",
        "Spacing must support both split differential movement and one-hand grouped movement. Engine numbering, left/right order and control-response mapping should remain consistent in normal and failure cases.",
        "三方要求高度一致。",
        "Highly aligned across all three authorities.",
        1,
    ),
    regulation(
        "group-easa", "engine_grouping", "EASA",
        "CS 25.1143(a)–(c)",
        "easa-cs25-powerplant-controls", "认证规范", "Certification specification",
        "EASA 多发大型飞机",
        "EASA multi-engine large aeroplanes",
        "每台发动机须有单独控制；排列须允许单独操纵每台发动机和同时操纵全部发动机，并提供确实且及时的响应。",
        "Each engine must have a separate control; the arrangement must permit individual and simultaneous operation with positive, immediate response.",
        "台架应测试单杆、双杆/多杆齐推、非对称位置识别和误抓相邻手柄的风险。",
        "Test single-lever use, paired/multiple-lever movement, asymmetric-position recognition and the risk of grasping the adjacent lever.",
        "与 FAA、CAAC 形成共同设计基线。",
        "Forms a common design baseline with FAA and CAAC.",
        2,
    ),
    regulation(
        "group-caac", "engine_grouping", "CAAC",
        "CCAR-25-R4 §§25.777(d), 25.1143(a)–(c)",
        "caac-ccar25-r4-controls", "法规正文", "Binding regulation",
        "中国多发运输类飞机",
        "Chinese multi-engine transport-category airplanes",
        "每台发动机必须有单独功率（推力）操纵器件；排列须能单独操纵每台发动机并同时操纵所有发动机，且不得混淆所控发动机。",
        "Each engine must have a separate power/thrust control; the arrangement must allow individual and simultaneous engine control without engine confusion.",
        "对四发等构型，还应验证内外侧发动机识别、成组操作与分体操作之间不会产生歧义。",
        "For four-engine layouts, also verify unambiguous inboard/outboard identification, grouped operation and split operation.",
        "与 FAA、EASA 基线一致。",
        "Aligned with the FAA and EASA baseline.",
        3,
    ),
    regulation(
        "cutoff-faa", "fuel_cutoff", "FAA",
        "14 CFR §25.1143(e)",
        "faa-25-powerplant-controls", "法规正文", "Binding regulation",
        "推力控制器本身包含燃油切断功能时",
        "Where the power/thrust control itself incorporates fuel shutoff",
        "必须防止误入断油位置；慢车处设置确实锁或止动器，并要求另一个明显动作才能进入断油。",
        "Inadvertent movement into fuel cutoff must be prevented by a positive lock or stop at idle and a separate, distinct action into cutoff.",
        "如果停车功能整合在主杆行程中，应把慢车—断油设计成明确的两阶段动作，并与反推选择保持可区分的操作语义。",
        "If shutdown is integrated into main-lever travel, make idle-to-cutoff a clear two-stage action and keep its operating meaning distinct from reverse selection.",
        "仅在推力控制器整合燃油切断功能时直接适用。",
        "Directly applicable only when fuel shutoff is incorporated in the thrust control.",
        1,
    ),
    regulation(
        "cutoff-easa", "fuel_cutoff", "EASA",
        "CS 25.1143(e)",
        "easa-cs25-powerplant-controls", "认证规范", "Certification specification",
        "推力控制器包含燃油切断功能的 CS-25 大型飞机",
        "CS-25 large aeroplanes where the thrust control incorporates fuel shutoff",
        "慢车处须有确实的锁或止动器，并通过另一个明显动作进入燃油切断，以防止误操作。",
        "A positive lock or stop at idle and a separate, distinct operation into fuel cutoff are required to prevent inadvertent selection.",
        "应验证正常减推力、快速收杆或振动不会越过慢车进入断油；紧急停车时又能被机组明确、及时解除。",
        "Show that normal retard, rapid pullback or vibration cannot cross idle into cutoff, while deliberate emergency shutdown remains clear and timely.",
        "与 FAA、CAAC 实质一致。",
        "Substantively aligned with FAA and CAAC.",
        2,
    ),
    regulation(
        "cutoff-caac", "fuel_cutoff", "CAAC",
        "CCAR-25-R4 §25.1143(e)",
        "caac-ccar25-r4-controls", "法规正文", "Binding regulation",
        "功率（推力）操纵器件具有切断燃油特性时",
        "Where a power/thrust control has a fuel-cutoff feature",
        "必须防止误动到断油位置；慢车位置须有确实锁或止动器，并以另外明显动作进入断油。",
        "Inadvertent movement to cutoff must be prevented by a positive lock or stop at idle and an additional distinct action.",
        "将断油闩锁、释放方向、状态标识和错误序列纳入台架符合性检查，不能只验证正常停车流程。",
        "Include the cutoff latch, release direction, state marking and erroneous sequences in rig compliance checks—not only the normal shutdown flow.",
        "与 FAA、EASA 共同形成两阶段断油防护基线。",
        "Shares the two-stage cutoff-protection baseline with FAA and EASA.",
        3,
    ),
    regulation(
        "layout-faa", "retention_layout", "FAA",
        "14 CFR §§25.777(a),(c), 25.1141(a),(c),(d)",
        "faa-25-powerplant-controls", "法规正文", "Binding regulation",
        "美国运输类飞机动力装置操纵器件",
        "Powerplant controls on U.S. transport-category airplanes",
        "控制器不得因人员进出或正常活动而误动；须有足够强度和刚度，并能保持任意设定位置，无需机组持续注意，也不得因载荷或振动产生滑移。",
        "Controls must not be moved inadvertently by crew entry, exit or normal movement; they need adequate strength and rigidity and must hold any set position without constant attention or creep from loads or vibration.",
        "台架应覆盖侧碰/衣物勾挂、振动、最大操作载荷、摩擦衰减和全行程结构干涉；保持力不能大到损害及时操纵。",
        "Test side bumps/clothing snags, vibration, maximum operating load, friction decay and full-travel interference; retention force must not impair timely operation.",
        "FAA 与 CAAC 条文均明确强度、刚度和抗滑移。",
        "FAA and CAAC explicitly state strength, rigidity and creep resistance.",
        1,
    ),
    regulation(
        "layout-easa", "retention_layout", "EASA",
        "CS 25.777(a),(c), CS 25.1141(a),(c),(d)",
        "easa-cs25-powerplant-controls", "认证规范", "Certification specification",
        "EASA CS-25 大型飞机动力装置操纵器件",
        "Powerplant controls on EASA CS-25 large aeroplanes",
        "布局须避免人员进出或正常活动造成误动；控制器须有足够强度/刚度并保持设定位置，不需持续注意，且不因操纵载荷或振动滑移。",
        "The layout must prevent inadvertent movement during crew entry, exit or normal activity; controls need sufficient strength/rigidity and must hold position without attention or creep from control loads or vibration.",
        "把座椅位置、约束系统、衣着、邻近控制器、手臂路径和振动环境合并成人因/机械联合验证，而非各自独立检查。",
        "Combine seat position, restraints, clothing, adjacent controls, arm paths and vibration into a joint human-factors/mechanical assessment.",
        "与 FAA、CAAC 的通用布局和保持要求一致。",
        "Aligned with the general FAA and CAAC layout/retention requirements.",
        2,
    ),
    regulation(
        "layout-caac", "retention_layout", "CAAC",
        "CCAR-25-R4 §§25.777(a),(c), 25.1141(a),(c),(d)",
        "caac-ccar25-r4-controls", "法规正文", "Binding regulation",
        "中国运输类飞机动力装置操纵器件",
        "Powerplant controls on Chinese transport-category airplanes",
        "操纵器件须防止人员进出和正常活动导致误动，具有足够强度和刚度；能保持任意给定位置，无需经常注意，且不得因载荷或振动滑移。",
        "Controls must resist inadvertent movement from crew entry/exit and normal activity, have adequate strength and rigidity, and hold any selected position without frequent attention or creep from loads or vibration.",
        "建议形成可量化的保持力、越门力、自由间隙和耐久后漂移指标，并保留与人体尺寸验证的对应关系。",
        "Define measurable retention force, gate-crossing force, clearance and post-endurance drift, tied to the human-dimension assessment.",
        "与 FAA、EASA 共同基线；CCAR-25-R4 同时给出 158–190 cm 的可达性范围。",
        "Common baseline with FAA and EASA; CCAR-25-R4 also states the 158–190 cm reach range.",
        3,
    ),
]


# 每条 FALLBACK 项需要从 API 同步正文的 CCAR-25/FAR-Part-25 条款号
# value 是该约束要拉取的 (regulation, [clause_numbers]) 列表
_AWKB_CLAUSE_MAP = {
    # forward_lever
    "forward-faa":  [("FAR-Part-25", ["25.777", "25.779", "25.1143"])],
    "forward-easa": [],  # EASA CS-25 暂未在 AirworthinessKB 全量索引
    "forward-caac": [("CCAR-25", ["25.777", "25.779", "25.1143"])],
    # reverse_lever
    "reverse-faa":  [("FAR-Part-25", ["25.779", "25.1155"])],
    "reverse-easa": [],
    "reverse-caac": [("CCAR-25", ["25.1155", "25.779"])],
    # flight_idle_gate
    "idle-faa":     [("FAR-Part-25", ["25.1143", "25.1155"])],
    "idle-easa":    [],
    "idle-caac":    [("CCAR-25", ["25.1143", "25.1155"])],
    # engine_grouping
    "group-faa":    [("FAR-Part-25", ["25.777", "25.1143"])],
    "group-easa":   [],
    "group-caac":   [("CCAR-25", ["25.777", "25.1143"])],
    # fuel_cutoff
    "cutoff-faa":   [("FAR-Part-25", ["25.1143"])],
    "cutoff-easa":  [],
    "cutoff-caac":  [("CCAR-25", ["25.1143"])],
    # retention_layout
    "layout-faa":   [("FAR-Part-25", ["25.777", "25.1141"])],
    "layout-easa":  [],
    "layout-caac":  [("CCAR-25", ["25.777", "25.1141"])],
}


def build_regulatory_constraints() -> tuple[list[dict], dict]:
    """构造 regulatory_constraints 列表。

    工作流：
    1. 启动时尝试连 AirworthinessKB API，拉最新条款正文覆盖 FALLBACK 的 requirement_zh/en
    2. 保留 FALLBACK 的工程解读（interpretation/difference），这是本工具独有的工程价值
    3. API 不可达时全量降级到 FALLBACK

    返回 (constraints, sync_meta)
      sync_meta 含 awkb_reachable / awkb_synced_at / awkb_base 用于审计
    """
    sync_meta = {
        "awkb_base": AWKB_BASE,
        "awkb_enabled": AWKB_ENABLED,
        "awkb_reachable": False,
        "awkb_synced_at": "",
        "awkb_overrides": 0,
    }

    # 先做健康检查
    health = _awkb_get("/api/v1/health")
    if not health or health.get("status") != "ok":
        print(f"[AWKB] 健康检查失败或服务未启，全量降级到 FALLBACK（{len(FALLBACK_REGULATORY_CONSTRAINTS)} 条）")
        return list(FALLBACK_REGULATORY_CONSTRAINTS), sync_meta

    sync_meta["awkb_reachable"] = True
    sync_meta["awkb_synced_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"[AWKB] 健康检查通过（uptime={health.get('uptime_s', 0):.0f}s），开始同步条款正文")

    merged: list[dict] = []
    override_count = 0
    for item in FALLBACK_REGULATORY_CONSTRAINTS:
        item_id = item["id"]
        clause_targets = _AWKB_CLAUSE_MAP.get(item_id, [])
        # 拉每条目标条款的正文，合并成单一文本
        if clause_targets:
            snippets_zh: list[str] = []
            for regulation, clause_numbers in clause_targets:
                for num in clause_numbers:
                    body = _awkb_fetch_clause_body(regulation, num)
                    if body and len(body) > 50:
                        snippets_zh.append(f"〔{regulation} §{num}〕{body[:600]}")
            if snippets_zh:
                # 用 API 拉到的最新条款原文覆盖本地 requirement_zh/en
                merged_body = "\n\n".join(snippets_zh)
                new_item = dict(item)
                new_item["requirement_zh"] = merged_body
                new_item["requirement_en"] = f"[Synced from AirworthinessKB at {sync_meta['awkb_synced_at']}]"
                merged.append(new_item)
                override_count += 1
                continue
        # API 没拉到就保留原 FALLBACK（含 EASA CS-25 那几条，因为 API 没全量索引）
        merged.append(dict(item))

    sync_meta["awkb_overrides"] = override_count
    print(f"[AWKB] 同步完成：{override_count}/{len(FALLBACK_REGULATORY_CONSTRAINTS)} 条用 API 正文覆盖，其余保留 FALLBACK")
    return merged, sync_meta


def design_option(
    item_id, slot_id, slot_zh, slot_en, name_zh, name_en, origin_zh, origin_en,
    description_zh, description_en, regulation_component_id, change_space_zh,
    change_space_en, protected_zone_zh, protected_zone_en, tags, source_id, order_index,
):
    return {
        "id": item_id, "slot_id": slot_id, "slot_zh": slot_zh, "slot_en": slot_en,
        "name_zh": name_zh, "name_en": name_en, "origin_zh": origin_zh, "origin_en": origin_en,
        "description_zh": description_zh, "description_en": description_en,
        "regulation_component_id": regulation_component_id,
        "change_space_zh": change_space_zh, "change_space_en": change_space_en,
        "protected_zone_zh": protected_zone_zh, "protected_zone_en": protected_zone_en,
        "tags": tags, "source_id": source_id, "order_index": order_index,
    }


DESIGN_COMPONENT_OPTIONS = [
    design_option(
        "main-fixed-detent", "main_lever", "主推力杆", "Main thrust lever",
        "固定卡位式双杆", "Fixed-detent twin levers", "参考：Airbus A320", "Reference: Airbus A320",
        "手柄表达推力限制卡位，自动推力在限制范围内调节，杆体通常不随系统移动。",
        "Levers express thrust-limit detents while autothrust works within the selected limit; the levers normally stay still.",
        "forward_lever", "握把人机尺寸、卡位编码、状态反馈媒介与模块化结构。",
        "Grip ergonomics, detent coding, state-feedback medium and modular structure.",
        "前推增大正推力；各发动机分控/联控；全行程可达且不得造成发动机混淆。",
        "Forward increases thrust; engines remain individually and jointly controllable; full travel must be reachable without engine confusion.",
        ["fixed_detent", "static_lever", "twin_lever", "mode_awareness"], "airbus-safety-flare", 1,
    ),
    design_option(
        "main-moving", "main_lever", "主推力杆", "Main thrust lever",
        "自动随动式双杆", "Motor-backdriven twin levers", "参考：Boeing 737NG", "Reference: Boeing 737NG",
        "自动油门驱动手柄，系统动作能够通过位置和运动被机组直接观察。",
        "Autothrottle backdrives the levers so system action is directly visible through position and motion.",
        "forward_lever", "驱动方式、离合器、接管力感、运动提示和故障降级。",
        "Drive mechanism, clutch, takeover feel, motion cues and degraded-mode behavior.",
        "手动超控必须及时且不会造成不安全响应；保持力、强度和防误动仍受约束。",
        "Manual override must remain timely without unsafe response; retention, strength and inadvertent-operation limits remain.",
        ["moving_lever", "motor_drive", "manual_override", "status_visibility"], "ntsb-737-autothrottle", 2,
    ),
    design_option(
        "main-adjustable", "main_lever", "主推力杆", "Main thrust lever",
        "可调安装高度模块", "Height-adjustable mounting module", "现有专利：CN109606705B", "Patent reference: CN109606705B",
        "通过可释放固定的安装结构改变油门台高度，以改善不同身高飞行员的极限位置可达性。",
        "A releasably fixed mounting arrangement changes quadrant height to improve full-travel reach across pilot statures.",
        "forward_lever", "调节锁定方式、连续/离散调节、记忆位置和调节后校准。",
        "Locking method, continuous/discrete adjustment, position memory and post-adjustment calibration.",
        "所有调节位置均须满足全行程、防干涉、强度和发动机映射要求；不可因调节引入松动。",
        "Every setting must preserve full travel, clearance, strength and engine mapping without adjustment-induced looseness.",
        ["adjustable_reach", "height_adjust", "ergonomics", "mounting_lock"], "patent-cn109606705", 3,
    ),
    design_option(
        "reverse-piggyback", "reverse", "反推组件", "Reverse-thrust component",
        "叠置反推小手柄", "Piggyback reverse levers", "参考：Boeing 民航布局", "Reference: Boeing civil layout",
        "反推小手柄叠置在主推力杆上，须在慢车位置后通过独立动作拉起。",
        "Reverse levers sit on the main levers and require a distinct lift action after flight idle.",
        "reverse_lever", "握持形态、左右联动、状态照明和越门手感。",
        "Grip form, left/right linking, state illumination and gate feel.",
        "飞行慢车必须有确实锁止；不能一次连续动作误入反推；飞行包线外选择须被防止。",
        "Flight idle needs a positive lock; a single continuous action must not enter reverse; out-of-envelope selection must be prevented.",
        ["piggyback_reverse", "distinct_action", "flight_idle_gate"], "img-boeing", 1,
    ),
    design_option(
        "reverse-separate", "reverse", "反推组件", "Reverse-thrust component",
        "独立反推触发杆", "Separate reverse trigger", "参考：Airbus A320", "Reference: Airbus A320",
        "独立反推触发件与正推力握把在形态和动作上区分，降低语义混淆。",
        "A separate trigger is differentiated from the forward-thrust grip in both form and action.",
        "reverse_lever", "触发杆形态、动作方向、触觉编码和双发同步策略。",
        "Trigger geometry, action direction, tactile coding and twin-engine synchronization.",
        "触发动作只能在 Flight Idle 后有效，且磨损后仍不能退化为单一连续动作。",
        "The trigger may become effective only after Flight Idle and must not degrade into one continuous action with wear.",
        ["separate_reverse", "distinct_action", "tactile_differentiation"], "img-a320", 2,
    ),
    design_option(
        "reverse-programmable", "reverse", "反推组件", "Reverse-thrust component",
        "任务自适应中间反推卡位", "Adaptive intermediate reverse detent", "现有专利：US9043050B2", "Patent reference: US9043050B2",
        "根据着陆性能和目标滑跑距离设定中间反推卡位，并与制动逻辑协同。",
        "Sets an intermediate reverse detent from landing performance and target rollout distance in coordination with braking.",
        "reverse_lever", "目标计算输入、提示方式、故障回退和非着陆用途的交互。",
        "Target-computation inputs, cueing method, failure fallback and non-landing interaction.",
        "自适应卡位不能削弱反推包线联锁、慢车门锁、禁止超控和故障告警。",
        "Adaptive detents must not weaken reverse-envelope interlocks, the idle gate, no-override logic or failure cautions.",
        ["programmable_reverse", "adjustable_detent", "rollout_target", "brake_coordination"], "patent-us9043050", 3,
    ),
    design_option(
        "detent-mechanical", "detent", "卡位 / 力感", "Detent and feel",
        "机械固定卡位", "Mechanical fixed detents", "成熟基线", "Mature baseline",
        "依靠几何槽、弹簧和摩擦机构提供可重复触觉卡位。",
        "Geometric tracks, springs and friction provide repeatable tactile detents.",
        "flight_idle_gate", "卡位力曲线、材料、磨损补偿、噪声和维护可达性。",
        "Force curve, material, wear compensation, noise and maintenance access.",
        "慢车/反推边界需确实锁止；振动和磨损不得使控制滑移或越门。",
        "The idle/reverse boundary requires a positive lock; vibration and wear must not cause creep or gate crossing.",
        ["mechanical_detent", "tactile_feedback", "wear_compensation"], "faa-25-reverse", 1,
    ),
    design_option(
        "detent-virtual", "detent", "卡位 / 力感", "Detent and feel",
        "动态虚拟卡位", "Dynamic virtual detent", "现有专利：US12162616B2", "Patent reference: US12162616B2",
        "控制器根据目标设置沿手柄行程动态建立触觉阻力卡位。",
        "A controller dynamically places a haptic resisting-force detent along lever travel at the target setting.",
        "flight_idle_gate", "非阻力式触觉编码、目标形成机制、冗余通道和机械安全后备。",
        "Non-resistive tactile coding, target-generation mechanism, redundancy and mechanical safety backup.",
        "虚拟卡位不可替代法规要求的反推确实锁/止动器；断电和故障状态必须可预测。",
        "A virtual detent cannot replace the required positive reverse lock/stop; power-loss and failure behavior must be predictable.",
        ["virtual_detent", "haptic_feedback", "target_setting", "dynamic_position"], "patent-us12162616", 2,
    ),
    design_option(
        "detent-multitrack", "detent", "卡位 / 力感", "Detent and feel",
        "多导轨连续 / 离散切换", "Multi-track continuous/discrete selector", "现有专利：US7143984B2", "Patent reference: US7143984B2",
        "通过连接导轨在带卡位的离散路径和无障碍连续路径之间切换。",
        "Connector tracks switch between a detented discrete path and an unobstructed continuous path.",
        "flight_idle_gate", "非同心路径、电子力感、切换判据和误路径检测。",
        "Non-concentric path geometry, electronic feel, switching criteria and wrong-path detection.",
        "路径切换不能使正/反推语义含糊，也不能绕过慢车处的独立动作。",
        "Path switching must not blur forward/reverse meaning or bypass the distinct action at idle.",
        ["multi_track", "continuous_control", "discrete_detent", "path_switch"], "patent-us7143984", 3,
    ),
    design_option(
        "feedback-display", "automation_feedback", "自动化反馈", "Automation feedback",
        "固定杆 + 独立状态显示", "Static lever + separate status display", "参考：Airbus 自动推力", "Reference: Airbus autothrust",
        "手柄位置表达限制范围，实际推力和自动推力模式由显示系统呈现。",
        "Lever position expresses the limit range while actual thrust and autothrust mode appear on displays.",
        "retention_layout", "跨模态提示、杆上状态触觉、注意力管理和显示冗余。",
        "Cross-modal cues, on-lever state feel, attention management and display redundancy.",
        "新增反馈不能让杆位与推力含义更加混淆；错误/丧失状态必须清晰。",
        "Additional feedback must not further confuse lever position and actual thrust; error/loss states must remain clear.",
        ["static_lever", "mode_display", "autothrust_status", "mode_awareness"], "faa-a320-autothrust", 1,
    ),
    design_option(
        "feedback-moving", "automation_feedback", "自动化反馈", "Automation feedback",
        "随动杆 + 手动超控", "Moving lever + manual override", "参考：Boeing 自动油门", "Reference: Boeing autothrottle",
        "手柄运动直接传达系统推力指令，并允许飞行员人工接管。",
        "Lever motion directly conveys commanded thrust and allows manual takeover.",
        "retention_layout", "无电机的运动提示、离合器架构、超控检测和接管确认。",
        "Motorless motion cues, clutch architecture, override detection and takeover confirmation.",
        "系统响应必须及时且不会形成危险跃变；摩擦/离合不得阻碍人工接管。",
        "System response must be timely without hazardous transients; friction/clutch behavior must not impede takeover.",
        ["moving_lever", "manual_override", "automation_motion", "status_visibility"], "ntsb-737-autothrottle", 2,
    ),
    design_option(
        "feedback-handle-light", "automation_feedback", "自动化反馈", "Automation feedback",
        "手柄集成视觉/触觉状态", "Handle-integrated visual/haptic status", "现有专利：US12258138B2", "Patent reference: US12258138B2",
        "在油门手柄内集成可激活视觉指示和交互控制，可附加触觉反馈。",
        "Integrates activatable visual indication and user control into the throttle handle, optionally with haptic feedback.",
        "retention_layout", "非灯光视觉编码、被动机械状态窗、空间/方向编码和跨手柄协同。",
        "Non-light visual coding, passive mechanical state windows, spatial/directional coding and cross-handle coordination.",
        "指示件不能诱发误操作、眩光或发动机混淆；故障时仍须保持主推力控制。",
        "Indicators must not induce inadvertent action, glare or engine confusion; primary thrust control must remain after failure.",
        ["integrated_indicator", "handle_visual", "corrective_action", "haptic_feedback"], "patent-us12258138", 3,
    ),
    design_option(
        "group-split", "engine_group", "发动机分组", "Engine grouping",
        "可分体双发手柄", "Split-capable twin levers", "民航 / 军机通用", "Civil/combat baseline",
        "左右发动机手柄可独立差动，也可单手同步推动。",
        "Left and right engine levers support differential movement and one-hand simultaneous control.",
        "engine_grouping", "可拆联接、非对称状态提醒、握把桥接和防误抓设计。",
        "Removable linking, asymmetric-state cueing, grip bridging and wrong-grasp prevention.",
        "必须保持每台发动机单独控制和全部发动机同时控制能力，且映射不可混淆。",
        "Individual control of each engine and simultaneous control of all engines must remain, without mapping confusion.",
        ["split_levers", "independent_control", "simultaneous_control"], "faa-25-powerplant-controls", 1,
    ),
    design_option(
        "group-linked", "engine_group", "发动机分组", "Engine grouping",
        "可选择机械联动", "Selectable mechanical ganging", "模块化概念", "Modular concept",
        "通过可见联接件在成组控制与独立控制之间切换。",
        "A visible coupling switches between grouped and independent engine control.",
        "engine_grouping", "联接位置、状态确认、无工具切换和故障自释放。",
        "Coupler location, state confirmation, tool-free change and fail-release behavior.",
        "联动不得取消单发控制能力；切换后必须明确、确实且及时响应。",
        "Ganging must not remove single-engine control; response after switching must be clear, positive and immediate.",
        ["selectable_link", "group_control", "modular_channel"], "faa-25-powerplant-controls", 2,
    ),
    design_option(
        "group-haptic", "engine_group", "发动机分组", "Engine grouping",
        "推力不平衡触觉提示", "Thrust-imbalance haptic cue", "现有专利：US10633105B2", "Patent reference: US10633105B2",
        "检测发动机推力/扭矩不平衡并通过一个或多个油门杆振动提醒。",
        "Detects thrust/torque imbalance and vibrates one or more levers as a cue.",
        "engine_grouping", "非振动提示、方向性力感、差异化表面温度/形变和视觉关联。",
        "Non-vibration cues, directional force, differentiated surface deformation/temperature and visual linkage.",
        "提示不得造成无意杆位改变、掩盖卡位或引起错误发动机识别。",
        "The cue must not move the lever inadvertently, mask detents or misidentify the affected engine.",
        ["haptic_imbalance", "lever_vibration", "thrust_split", "engine_alert"], "patent-us10633105", 3,
    ),
    design_option(
        "action-toga-guard", "action_control", "动作控制", "Action controls",
        "受保护 TO/GA 触发", "Guarded TO/GA trigger", "来自飞行员痛点", "From pilot-report evidence",
        "通过形态、方向或阶段性解锁降低 TO/GA 误触，同时保留紧急复飞可达性。",
        "Uses form, direction or phase-aware enabling to reduce inadvertent TO/GA while preserving go-around access.",
        "retention_layout", "护圈、双动作、力阈值、阶段性触觉和按后确认。",
        "Guard ring, dual action, force threshold, phase-aware tactile cue and post-press confirmation.",
        "防护不能延误复飞；控制位置仍须方便操作且不得与其他按钮混淆。",
        "Protection must not delay go-around; the control must remain convenient and distinguishable.",
        ["toga_guard", "button_protection", "action_slip", "phase_awareness"], "pilot-asrs-370", 1,
    ),
    design_option(
        "action-at-disconnect", "action_control", "动作控制", "Action controls",
        "自动油门断开 + 明确确认", "Autothrottle disconnect with positive confirmation", "来自飞行员痛点", "From pilot-report evidence",
        "在手柄上断开自动油门，并用持续视觉/触觉/听觉状态确认避免“以为仍接通”。",
        "Disconnects autothrottle at the handle and provides persistent visual/tactile/aural confirmation to prevent false assumptions.",
        "retention_layout", "确认通道、复位逻辑、双击语义和模式恢复提示。",
        "Confirmation channel, reset logic, double-click semantics and re-engagement cueing.",
        "断开/重接逻辑不得造成危险推力跃变，且状态必须在所有相关机组位置可识别。",
        "Disconnect/re-engage logic must not create hazardous thrust transients and state must be identifiable from relevant crew positions.",
        ["autothrottle_disconnect", "persistent_status", "mode_awareness", "confirmation"], "pilot-asrs-423", 2,
    ),
    design_option(
        "action-cutoff-gate", "action_control", "动作控制", "Action controls",
        "慢车—断油两阶段门锁", "Two-stage idle-to-cutoff gate", "适航基线", "Airworthiness baseline",
        "慢车处确实止动，再通过抬起、横移或独立闩锁进入断油。",
        "Provides a positive stop at idle followed by lift, lateral shift or a separate latch into cutoff.",
        "fuel_cutoff", "闩锁几何、方向、状态编码、紧急操作和耐磨机构。",
        "Latch geometry, direction, state coding, emergency operation and wear-resistant mechanism.",
        "慢车处必须确实锁止，进入断油必须另一个明显动作；正常收杆不得误关车。",
        "Idle requires a positive lock and cutoff a separate distinct action; normal retard must not shut down the engine.",
        ["fuel_cutoff_gate", "distinct_action", "positive_stop", "shutdown_safety"], "faa-25-powerplant-controls", 3,
    ),
]


PATENT_LANDSCAPE = [
    {
        "id": "us12258138", "publication_no": "US12258138B2", "jurisdiction": "US",
        "assignee": "Gulfstream Aerospace Corp", "priority_date": "2022-06-08",
        "title_zh": "手柄集成视觉指示与纠正动作", "title_en": "Handle-integrated visual indication and corrective action",
        "status_zh": "公开聚合页标示有效；须在 USPTO 官方登记簿复核", "status_en": "Aggregator lists active; verify in the official USPTO register",
        "claim_zh": "独立权利要求组合了油门手柄内可激活视觉指示、响应发动机状态的控制器，以及用于启动纠正动作的手柄内用户界面控制元件。",
        "claim_en": "Independent claims combine an activatable visual indicator in the throttle handle, a controller responding to engine status, and a handle-integrated UI element initiating corrective action.",
        "change_zh": ["不要仅改变灯色或外形；改变状态编码的物理原理或信息路径。", "避免沿用“手柄内指示 + 手柄内纠正控制 + 状态响应控制器”的完整组合。", "证明新机制解决不同的人因问题并产生可测量效果。"],
        "change_en": ["Do more than alter color or shape; change the physical state-coding principle or information path.", "Avoid reproducing the complete handle-indicator + handle-corrective-control + status-controller combination.", "Show a different human-factors problem and measurable technical effect."],
        "tags": ["integrated_indicator", "handle_visual", "corrective_action", "haptic_feedback"], "applicable_aircraft": ["aircraft:a320-family", "aircraft:b737ng-family", "aircraft:c919-family"], "source_id": "patent-us12258138",
    },
    {
        "id": "us12162616", "publication_no": "US12162616B2", "jurisdiction": "US",
        "assignee": "Innovative Solutions & Support", "priority_date": "2021-12-05",
        "title_zh": "动态虚拟卡位自动油门界面", "title_en": "Dynamic virtual-detent autothrottle interface",
        "status_zh": "公开聚合页标示有效；须复核权利要求与家族", "status_en": "Aggregator lists active; verify claims and family",
        "claim_zh": "核心组合是自动油门目标设置、随目标动态改变位置的虚拟卡位，以及在手动移动到该位置时施加阻力的触觉效果。",
        "claim_en": "Core combination: autothrottle target setting, a dynamically repositioned virtual detent, and a resisting haptic effect when the pilot reaches that location.",
        "change_zh": ["避免用同一目标值直接决定动态卡位位置。", "探索非阻力式或非行程位置式提示。", "形成不同的模式切换触发条件与安全后备。"],
        "change_en": ["Avoid directly using the same target value to place a dynamic detent.", "Explore non-resistive or non-travel-position cues.", "Use different mode-transition criteria and safety backup."],
        "tags": ["virtual_detent", "haptic_feedback", "target_setting", "dynamic_position"], "applicable_aircraft": ["aircraft:a320-family", "aircraft:b737ng-family", "aircraft:c919-family"], "source_id": "patent-us12162616",
    },
    {
        "id": "us10633105", "publication_no": "US10633105B2", "jurisdiction": "US",
        "assignee": "Innovative Solutions & Support", "priority_date": "2017-11-09",
        "title_zh": "油门杆振动告警与性能调节", "title_en": "Throttle-lever vibration alert and performance adjust",
        "status_zh": "公开聚合页标示有效；须复核官方状态", "status_en": "Aggregator lists active; verify official status",
        "claim_zh": "相关权利要求覆盖在定义条件下使油门杆摇动/振动，并结合自动油门作动和发动机/飞行参数监控。",
        "claim_en": "Relevant claims cover shaking/vibrating a throttle lever under defined conditions with autothrottle actuation and engine/flight-parameter monitoring.",
        "change_zh": ["改用不会周期振动杆体的方向性或表面触觉。", "改变不平衡判断参数和提示到发动机的映射。", "将告警与独立安全功能解耦并验证不会造成杆位变化。"],
        "change_en": ["Use directional or surface haptics that do not cyclically vibrate the lever.", "Change imbalance criteria and engine-to-cue mapping.", "Decouple alerting from control action and prove the cue cannot alter lever position."],
        "tags": ["haptic_imbalance", "lever_vibration", "thrust_split", "engine_alert", "haptic_feedback"], "applicable_aircraft": ["aircraft:a320-family", "aircraft:b737ng-family", "aircraft:c919-family"], "source_id": "patent-us10633105",
    },
    {
        "id": "us9043050", "publication_no": "US9043050B2", "jurisdiction": "US",
        "assignee": "The Boeing Company", "priority_date": "2008-08-13",
        "title_zh": "可编程中间反推卡位", "title_en": "Programmable intermediate reverse detent",
        "status_zh": "聚合页显示费用相关失效；仍可能是现有技术", "status_en": "Aggregator shows fee-related lapse; still potentially prior art",
        "claim_zh": "权利要求组合了可调中间反推卡位、反推调度、制动系统、可编程反推设置及目标滑跑距离。",
        "claim_en": "Claims combine an adjustable intermediate reverse detent, reverse scheduling, braking, programmable reverse setting and target rollout distance.",
        "change_zh": ["不要只改变卡位数量；改变目标形成与人机交互闭环。", "避免同样以目标滑跑距离联动制动与反推卡位。", "考虑非卡位式能量管理或只提供建议、不直接设卡位。"],
        "change_en": ["Do more than change detent count; alter target formation and the HMI loop.", "Avoid the same rollout-distance coordination of braking and reverse detent.", "Consider non-detent energy management or advisory-only cueing."],
        "tags": ["programmable_reverse", "adjustable_detent", "rollout_target", "brake_coordination"], "applicable_aircraft": ["aircraft:a320-family", "aircraft:b737ng-family", "aircraft:c919-family"], "source_id": "patent-us9043050",
    },
    {
        "id": "us7143984", "publication_no": "US7143984B2", "jurisdiction": "US",
        "assignee": "Airbus France", "priority_date": "2003-04-18",
        "title_zh": "正推/反推/辅助连续控制多导轨", "title_en": "Forward/reverse/auxiliary continuous multi-track lever",
        "status_zh": "历史授权文献；须复核期限和家族", "status_en": "Historic granted document; verify term and family",
        "claim_zh": "核心是控制杆配合第一、第二及辅助导轨，分别提供反推连续控制、正推离散卡位和正推连续控制。",
        "claim_en": "Core: a lever cooperating with first, second and auxiliary tracks for continuous reverse, detented forward and continuous forward control.",
        "change_zh": ["避免复用三条同心导轨及相同连接轨切换。", "改变离散/连续模式的切换原理。", "采用电子力感时仍需证明机械安全边界。"],
        "change_en": ["Avoid the same three concentric tracks and connector-track switching.", "Change the discrete/continuous mode-selection principle.", "If using active feel, preserve a demonstrable mechanical safety boundary."],
        "tags": ["multi_track", "continuous_control", "discrete_detent", "path_switch"], "applicable_aircraft": ["aircraft:a320-family", "aircraft:b737ng-family", "aircraft:c919-family"], "source_id": "patent-us7143984",
    },
    {
        "id": "cn109606705", "publication_no": "CN109606705B", "jurisdiction": "CN",
        "assignee": "空客相关申请人（以官方登记为准）", "priority_date": "2018-12-11",
        "title_zh": "不同高度位置可释放固定的油门台", "title_en": "Quadrant releasably fixed at different height positions",
        "status_zh": "授权文献；须在 CNIPA 复核状态与权利人", "status_en": "Granted publication; verify status and proprietor at CNIPA",
        "claim_zh": "权利要求围绕控制台本体、操纵杆和围绕本体设置、可在不同高度位置固定的安装装置及其支架/钢索结构。",
        "claim_en": "Claims center on the quadrant body, lever and a surrounding mounting device fixable at different heights, including bracket/cable structure.",
        "change_zh": ["不要只替换钢索材料；改变调节自由度和承载路径。", "避免围绕本体的相对支架与收紧钢索组合。", "提出调节后自动校准或动态可达性的新技术效果。"],
        "change_en": ["Do more than substitute cable material; change adjustment degrees of freedom and load path.", "Avoid the surrounding opposed-bracket and tightening-cable combination.", "Add a distinct effect such as automatic calibration after adjustment or dynamic reach adaptation."],
        "tags": ["adjustable_reach", "height_adjust", "mounting_lock", "ergonomics"], "applicable_aircraft": ["aircraft:a320-family", "aircraft:b737ng-family", "aircraft:c919-family"], "source_id": "patent-cn109606705",
    },
    {
        "id": "cn102452481", "publication_no": "CN102452481A", "jurisdiction": "CN",
        "assignee": "公开申请人（以 CNIPA 为准）", "priority_date": "2010-10-29",
        "title_zh": "蜗轮蜗杆与摩擦片自动/手动油门", "title_en": "Worm-gear/friction automatic-manual throttle",
        "status_zh": "申请视为撤回；公开内容仍可构成现有技术线索", "status_en": "Application deemed withdrawn; disclosure remains a prior-art lead",
        "claim_zh": "披露组合包括油门杆、蜗轮蜗杆、电机、摩擦片、主轴和弹簧，通过摩擦传动实现自动随动与人工接管。",
        "claim_en": "Discloses a lever, worm gearing, motor, friction plates, shaft and spring using friction transmission for automatic drive and manual takeover.",
        "change_zh": ["改变动力传递原理，而非仅改变齿轮尺寸。", "采用可监测的冗余离合或无接触力耦合。", "证明接管力和故障模式具有不同技术效果。"],
        "change_en": ["Change the power-transfer principle, not merely gear dimensions.", "Use monitored redundant clutching or non-contact force coupling.", "Show different takeover-force and failure-mode effects."],
        "tags": ["moving_lever", "motor_drive", "manual_override", "friction_clutch"], "applicable_aircraft": ["aircraft:a320-family", "aircraft:b737ng-family", "aircraft:c919-family"], "source_id": "patent-cn102452481",
    },
    {
        "id": "cn117542251", "publication_no": "CN117542251B", "jurisdiction": "CN",
        "assignee": "北京蓝天航空科技股份有限公司", "priority_date": "2023-10-25",
        "title_zh": "一体化仿真油门台模块", "title_en": "Integrated simulator throttle-quadrant module",
        "status_zh": "公开聚合页显示已授权；须在 CNIPA 复核", "status_en": "Aggregator shows granted; verify at CNIPA",
        "claim_zh": "披露在单一壳体内集成操纵结构、信号采集、模式切换、动力输入和电子系统，并以齿轮吸合/断开切换手动和自动。",
        "claim_en": "Discloses one housing integrating mechanics, sensing, mode switching, power input and electronics, with gear engagement/disengagement for manual/automatic modes.",
        "change_zh": ["避免照搬单壳体五组件一体化和相同齿轮吸合模式。", "采用可更换分区模块、分布式电子或不同模式切换。", "定义面向真机审定而非仿真的不同约束与效果。"],
        "change_en": ["Avoid the same one-housing five-subsystem integration and gear engagement scheme.", "Use replaceable zones, distributed electronics or a different mode switch.", "Define effects and constraints for certified aircraft rather than simulator fidelity."],
        "tags": ["integrated_module", "mode_switch", "motor_drive", "simulator"], "applicable_aircraft": ["aircraft:a320-family", "aircraft:b737ng-family", "aircraft:c919-family"], "source_id": "patent-cn117542251",
    },
]


PILOT_NEEDS = [
    {
        "id": "need-mode-awareness", "severity": 5, "evidence_count": 3,
        "title_zh": "自动油门到底有没有接通，必须一眼确认", "title_en": "Autothrottle engagement must be unmistakable",
        "problem_zh": "ASRS 报告中机组未及时识别自动油门已断开，并对系统是否会“唤醒”存在错误预期。",
        "problem_en": "ASRS reports show delayed recognition of autothrottle disengagement and incorrect expectations about whether it will wake up.",
        "opportunity_zh": "在手柄、主显示和听觉之间形成持续而一致的状态编码；状态变化后要求明确确认。",
        "opportunity_en": "Create persistent, consistent state coding across lever, primary display and audio, with explicit confirmation after changes.",
        "tags": ["mode_awareness", "persistent_status", "autothrottle_status", "confirmation"], "goals": ["safety", "automation"], "source_id": "pilot-asrs-423",
    },
    {
        "id": "need-toga-surprise", "severity": 5, "evidence_count": 2,
        "title_zh": "复飞推力跃变不能让飞行员措手不及", "title_en": "Go-around thrust transients must not surprise the pilot",
        "problem_zh": "飞行员报告按下 TO/GA 后系统指令全推力，未预期的推力跃变导致明显俯仰和速度控制困难。",
        "problem_en": "A pilot report describes an unexpected full-thrust TO/GA response contributing to pitch and airspeed-control difficulty.",
        "opportunity_zh": "在不延误复飞的前提下提供分级触觉预告、推力即将变化的确认或可预测的接管路径。",
        "opportunity_en": "Without delaying go-around, provide graded tactile pre-cueing, confirmation of imminent thrust change or a predictable takeover path.",
        "tags": ["toga_guard", "phase_awareness", "haptic_feedback", "manual_override"], "goals": ["safety", "automation"], "source_id": "pilot-asrs-463",
    },
    {
        "id": "need-toga-mistouch", "severity": 4, "evidence_count": 2,
        "title_zh": "TO/GA 既不能误触，也不能在紧急时难找", "title_en": "TO/GA must resist slips without becoming hard to reach",
        "problem_zh": "ASRS 记录了操作推力杆附近控制时误按 TO/GA 并引发模式混淆。",
        "problem_en": "ASRS records inadvertent TO/GA activation while operating near the thrust levers, followed by mode confusion.",
        "opportunity_zh": "用方向、形态、力阈值或飞行阶段触觉区分按钮，同时保留单手快速触发。",
        "opportunity_en": "Differentiate the button by direction, form, force threshold or phase-aware feel while preserving rapid one-hand activation.",
        "tags": ["toga_guard", "button_protection", "action_slip", "tactile_differentiation"], "goals": ["safety", "ergonomics"], "source_id": "pilot-asrs-370",
    },
    {
        "id": "need-takeoff-confirm", "severity": 5, "evidence_count": 3,
        "title_zh": "起飞推力未设到位，需要独立于流程的最后防线", "title_en": "Incorrect takeoff thrust needs a barrier independent of procedure",
        "problem_zh": "AAIB 事件中 TO/GA 未按下且交叉检查被分心打断，飞机以不足推力起飞；调查认为现有防护并不充分。",
        "problem_en": "In an AAIB event TO/GA was not pressed and cross-checking was disrupted, leading to takeoff with insufficient thrust; existing barriers were judged insufficient.",
        "opportunity_zh": "基于跑道阶段、推力目标与实际杆位建立显著且无法轻易抑制的“未设起飞推力”提示。",
        "opportunity_en": "Use runway phase, target thrust and actual lever state to create a salient, hard-to-suppress takeoff-thrust-not-set cue.",
        "tags": ["takeoff_confirm", "thrust_target_display", "phase_awareness", "persistent_status"], "goals": ["safety", "automation"], "source_id": "pilot-aaib-gjzhl",
    },
    {
        "id": "need-v1-slip", "severity": 5, "evidence_count": 1,
        "title_zh": "高工作负荷阶段要防止动作滑误", "title_en": "High-workload phases need action-slip resistance",
        "problem_zh": "AAIB 记录副驾驶在 V1 附近开始收推力而不是把手移开，说明训练良好人员仍可能执行错误的熟练动作。",
        "problem_en": "AAIB recorded a copilot beginning to retard the levers near V1 instead of removing the hand, showing that trained crews can still execute the wrong practiced action.",
        "opportunity_zh": "研究与飞行阶段相关、但不剥夺控制权的短时触觉门槛、方向性提示或握持释放提示。",
        "opportunity_en": "Explore phase-aware but non-locking tactile thresholds, directional cues or hand-release prompts without removing pilot authority.",
        "tags": ["action_slip", "phase_awareness", "tactile_gate", "takeoff_confirm"], "goals": ["safety", "ergonomics"], "source_id": "pilot-aaib-gviit",
    },
    {
        "id": "need-reach", "severity": 4, "evidence_count": 2,
        "title_zh": "复飞全推力位置必须覆盖不同身高与约束姿态", "title_en": "Go-around full-thrust reach must cover different statures and restraints",
        "problem_zh": "专利背景和 CCAR/FAR 可达性要求共同指出：系紧约束系统时，较矮飞行员可能难以前推至极限，而简单后移/抬高又会牺牲高个飞行员舒适性。",
        "problem_en": "Patent background and Part 25 reach rules show that shorter pilots may struggle to reach full forward travel while restrained, while simply moving the quadrant can hurt taller-pilot comfort.",
        "opportunity_zh": "开发不照搬现有支架权利要求的自适应握把、行程映射或经锁定的多轴调节方案。",
        "opportunity_en": "Develop adaptive grips, travel mapping or locked multi-axis adjustment without reproducing the existing mounting-claim combination.",
        "tags": ["adjustable_reach", "ergonomics", "height_adjust", "full_travel"], "goals": ["ergonomics", "safety"], "source_id": "patent-cn109606705",
    },
]

INVENTION_PATTERNS = [
    {
        "id": "passive_state_morphing", "difficulty": 54,
        "name_zh": "被动形态状态编码", "name_en": "Passive morphing state code",
        "principle_zh": "让控制器表面或轮廓随真实机械状态改变，而不是再增加灯光、文字或振动。",
        "principle_en": "Let the control surface or contour change with the real mechanical state instead of adding another light, label or vibration.",
        "mechanism_zh": "设置与主控制动力路径独立的状态随动件，驱动握把上的可触轮廓、机械窗口或表面凸起变化；失电时由弹簧回到明确的故障形态。",
        "mechanism_en": "Use a state follower independent of the primary control load path to drive a tactile contour, mechanical window or raised surface; a spring returns it to an explicit failure shape on power loss.",
        "why_zh": "创新点不是把已有显示、触觉和手柄相加，而是把“状态信息载体”从电子提示改成与机构状态因果绑定的被动形态。",
        "why_en": "The inventive step is not adding display, haptics and handle features; it changes the information carrier to a passive form causally coupled to mechanism state.",
        "suitable_tags": ["mode_awareness", "persistent_status", "tactile_differentiation", "autothrottle_status"],
        "avoid_tags": ["integrated_indicator", "handle_visual", "lever_vibration", "virtual_detent"],
        "risk_tags": ["handle_visual", "integrated_indicator"],
        "claim_zh": ["推力控制构件", "与主动力路径独立的状态随动构件", "具有至少两种可触几何形态的信息表面", "失能时进入预定安全形态的偏置机构"],
        "claim_en": ["thrust-control member", "state follower independent of the primary load path", "information surface with at least two tactile geometries", "bias element entering a predetermined safe form when unpowered"],
        "validation_zh": ["蒙眼状态识别时间", "失电状态可辨识率", "误触发与卡滞试验", "对主杆操纵力的影响"],
        "validation_en": ["eyes-free state-recognition time", "power-loss recognition rate", "false-actuation and jam testing", "effect on primary lever force"],
    },
    {
        "id": "directional_impedance", "difficulty": 68,
        "name_zh": "方向选择性动作阻抗", "name_en": "Direction-selective action impedance",
        "principle_zh": "只对高风险错误方向增加短时阻抗，对正确方向和紧急超控保持低阻力。",
        "principle_en": "Add temporary impedance only in the high-risk wrong direction while keeping the correct direction and emergency override low-force.",
        "mechanism_zh": "利用非对称凸轮和受飞行阶段许可的旁路件形成单向力阈值；它不在目标位置生成虚拟卡位，而是在错误动作开始时给出方向性阻力并允许确定力超控。",
        "mechanism_en": "An asymmetric cam and phase-permitted bypass create a one-way force threshold. It does not place a virtual detent at a target position; it resists the onset of the wrong action and permits a defined-force override.",
        "why_zh": "不是把传感器、告警和卡位拼接，而是改变错误动作与机构阻力之间的因果时序：在动作形成前干预，而非动作后告警。",
        "why_en": "This is not a sensor-alert-detent bundle; it changes the causal timing between error and resistance by intervening before the action forms rather than warning afterward.",
        "suitable_tags": ["action_slip", "phase_awareness", "tactile_gate", "takeoff_confirm"],
        "avoid_tags": ["virtual_detent", "dynamic_position", "lever_vibration"],
        "risk_tags": ["haptic_feedback", "target_setting"],
        "claim_zh": ["可双向移动的推力控制件", "具有非对称力曲线的阻抗构件", "仅在预定飞行阶段建立错误方向阈值的许可构件", "不依赖目标杆位的人工超控路径"],
        "claim_en": ["bidirectionally movable thrust control", "impedance member with asymmetric force curve", "permission member establishing a wrong-direction threshold only in a defined flight phase", "manual override path independent of target lever position"],
        "validation_zh": ["V1 附近动作滑误模拟", "紧急收推力时间", "误阻挡概率", "磨损后力阈值分布"],
        "validation_en": ["near-V1 action-slip simulation", "emergency retard time", "false-block probability", "post-wear force-threshold distribution"],
    },
    {
        "id": "grip_travel_transform", "difficulty": 63,
        "name_zh": "固定基座的握把行程变换", "name_en": "Fixed-base grip travel transformation",
        "principle_zh": "不移动整个油门台，而是在握把与传感映射之间改变有效臂长和可达行程。",
        "principle_en": "Keep the quadrant base fixed and change effective reach and travel mapping between grip and sensing.",
        "mechanism_zh": "握把沿杆体锁定伸缩或旋转偏置，双通道传感器识别构型并自动重标定有效行程；主轴和安装载荷路径保持不变。",
        "mechanism_en": "The grip locks in telescopic or rotational offset positions; dual-channel sensing identifies the configuration and recalibrates effective travel while the main shaft and mounting load path remain fixed.",
        "why_zh": "不是把现有可调高度支架与普通油门合并，而是把调节自由度从“基座—驾驶舱”界面迁移到“握把—输入映射”界面。",
        "why_en": "This does not combine a known height-adjustable mount with a normal throttle; it moves the adjustment degree of freedom from the base-cockpit interface to the grip-input-mapping interface.",
        "suitable_tags": ["adjustable_reach", "ergonomics", "height_adjust", "full_travel"],
        "avoid_tags": ["mounting_lock", "height_adjust"],
        "risk_tags": ["adjustable_reach", "height_adjust"],
        "claim_zh": ["固定安装的油门台基座", "可相对控制杆锁定改变有效抓握点的握把", "识别握把构型的冗余传感通道", "保持发动机命令全量程的重映射逻辑"],
        "claim_en": ["fixed-mounted quadrant base", "grip lockable relative to the lever to change effective grasp point", "redundant sensing channels identifying grip configuration", "remapping logic preserving full engine-command range"],
        "validation_zh": ["158–190 cm 可达性", "调节后标定误差", "锁定失效载荷", "紧急复飞全推力时间"],
        "validation_en": ["158–190 cm reach", "post-adjustment calibration error", "lock-failure load", "time to full go-around thrust"],
    },
    {
        "id": "intent_vector_gate", "difficulty": 57,
        "name_zh": "意图向量门", "name_en": "Intent-vector gate",
        "principle_zh": "用一个自然的二维手势区分有意操作与直线方向的动作滑误。",
        "principle_en": "Use one natural two-axis gesture to separate deliberate action from a straight-line action slip.",
        "mechanism_zh": "触发件先接受小幅横向/捏合分量，再沿主推力方向完成动作；两分量通过单一连续手势耦合，紧急时不需要寻找第二个分离按钮。",
        "mechanism_en": "The trigger first accepts a small lateral or squeeze component and then completes along the thrust direction. Both components form one continuous gesture without searching for a separate second button.",
        "why_zh": "不是在按钮外增加护圈或再加一次确认，而是重新定义有效输入的运动拓扑，使最常见的直线误动作无法满足意图轨迹。",
        "why_en": "This is not a guard ring or extra confirmation; it redefines the topology of valid input so the common straight-line slip cannot satisfy the intent path.",
        "suitable_tags": ["toga_guard", "button_protection", "action_slip", "distinct_action"],
        "avoid_tags": ["corrective_action", "integrated_indicator", "button_protection"],
        "risk_tags": ["toga_guard", "distinct_action"],
        "claim_zh": ["位于推力握把上的输入构件", "定义第一方向分量和第二方向分量的导向路径", "仅在连续意图轨迹完成时输出指令的判定构件", "允许单手紧急触发的复位结构"],
        "claim_en": ["input member on a thrust grip", "guide path defining first and second directional components", "decision member outputting a command only after a continuous intent path", "reset structure permitting one-hand emergency actuation"],
        "validation_zh": ["误触率", "首次操作学习时间", "戴手套单手操作时间", "高负荷复飞成功率"],
        "validation_en": ["inadvertent-actuation rate", "first-use learning time", "gloved one-hand actuation time", "high-workload go-around success rate"],
    },
    {
        "id": "differential_truth_flag", "difficulty": 61,
        "name_zh": "指令—实效差分真值旗", "name_en": "Command-effect differential truth flag",
        "principle_zh": "只在手柄意图、系统指令与发动机实际响应不一致时显示异常，而非持续显示更多状态。",
        "principle_en": "Show an abnormal state only when lever intent, system command and actual engine response disagree, rather than displaying more status continuously.",
        "mechanism_zh": "独立比较通道计算杆位意图、自动推力命令和实际推力之间的差分；超过时间—幅值包线时驱动基座机械旗或改变握把边缘形态，正常一致时保持隐蔽。",
        "mechanism_en": "An independent comparator evaluates lever intent, autothrottle command and actual thrust. When a time-amplitude envelope is exceeded it drives a base flag or changes grip-edge form; it stays hidden during normal agreement.",
        "why_zh": "不是复制发动机状态灯，而是检测三个信号之间的因果不一致，并把信息压缩为“系统是否按照你的意图工作”。",
        "why_en": "It is not another engine-status light; it detects causal disagreement among three signals and compresses it to whether the system is acting as intended.",
        "suitable_tags": ["mode_awareness", "takeoff_confirm", "thrust_target_display", "persistent_status"],
        "avoid_tags": ["integrated_indicator", "handle_visual", "corrective_action"],
        "risk_tags": ["integrated_indicator", "handle_visual"],
        "claim_zh": ["杆位意图输入", "自动推力命令输入", "发动机实际响应输入", "基于时间—幅值差分包线的独立比较器", "仅在不一致时显现的物理提示构件"],
        "claim_en": ["lever-intent input", "autothrottle-command input", "actual-engine-response input", "independent comparator using a time-amplitude disagreement envelope", "physical cue appearing only on disagreement"],
        "validation_zh": ["错误起飞推力检出率", "误警率", "传感器故障注入", "机组识别和处置时间"],
        "validation_en": ["incorrect-takeoff-thrust detection", "false-alert rate", "sensor-failure injection", "crew recognition and response time"],
    },
    {
        "id": "fail_open_module", "difficulty": 72,
        "name_zh": "失效开路的功能盒", "name_en": "Fail-open functional cartridge",
        "principle_zh": "把创新功能做成可更换旁路模块，任何失效都自动退出主推力载荷路径。",
        "principle_en": "Package the novel feature as a replaceable bypass cartridge that automatically exits the primary thrust load path on any failure.",
        "mechanism_zh": "主杆具有连续机械基线通道，反馈/联动/阻抗功能位于侧挂盒；盒体断电、卡滞或拆除时剪切联接自动释放，主杆恢复规定的基线力感。",
        "mechanism_en": "The main lever retains a continuous mechanical baseline channel while feedback, coupling or impedance sits in a side cartridge. Power loss, jam or removal releases a shear coupling and restores baseline lever feel.",
        "why_zh": "不是把已有电机、离合器和模块外壳组合，而是以“失效时从载荷路径拓扑中消失”作为架构核心。",
        "why_en": "This is not a motor-clutch-module bundle; the architectural core is disappearance from the load-path topology upon failure.",
        "suitable_tags": ["manual_override", "modular_channel", "maintenance", "motor_drive"],
        "avoid_tags": ["friction_clutch", "worm_gear", "integrated_module"],
        "risk_tags": ["motor_drive", "manual_override", "integrated_module"],
        "claim_zh": ["连续的主推力机械通道", "与主通道并联的可更换功能盒", "检测功能盒失效的释放构件", "失效时使功能盒脱离载荷路径的能量偏置机构"],
        "claim_en": ["continuous primary mechanical thrust channel", "replaceable functional cartridge in parallel with the primary channel", "release member detecting cartridge failure", "energy-biased mechanism removing the cartridge from the load path on failure"],
        "validation_zh": ["卡滞释放时间", "拆除后基线操纵力", "重复更换标定", "单故障安全性分析"],
        "validation_en": ["jam-release time", "baseline force after removal", "repeat replacement calibration", "single-failure safety assessment"],
    },
    {
        "id": "reverse_permission_token", "difficulty": 76,
        "name_zh": "分布式反推许可令牌", "name_en": "Distributed reverse-permission token",
        "principle_zh": "把“允许反推”做成必须由多个独立物理事实共同生成的许可，而不是单一软件位或可超控开关。",
        "principle_en": "Make reverse permission a token generated only by multiple independent physical facts, not a single software bit or override switch.",
        "mechanism_zh": "飞行慢车到位、地面/批准包线状态和反推独立动作分别提供机械或电气钥匙；只有三钥在局部许可节点同时成立，反推路径才物理连通，任一失效令令牌消失。",
        "mechanism_en": "Flight-idle arrival, ground/approved-envelope state and the distinct reverse action each provide a mechanical or electrical key. Only their concurrence at a local node physically enables reverse; any failure removes the token.",
        "why_zh": "不是把现有门锁、传感器和告警串联，而是把反推能力本身设计成需要多源事实合成的临时权限。",
        "why_en": "This is not a series connection of a gate, sensor and alert; reverse capability itself becomes a temporary permission synthesized from independent facts.",
        "suitable_tags": ["distinct_action", "flight_idle_gate", "programmable_reverse", "shutdown_safety"],
        "avoid_tags": ["adjustable_detent", "rollout_target", "virtual_detent"],
        "risk_tags": ["programmable_reverse", "flight_idle_gate"],
        "claim_zh": ["反推控制路径", "表示飞行慢车到位的第一许可源", "表示批准反推包线的第二许可源", "表示机组独立动作的第三许可源", "仅在三许可并存时连通反推路径的局部节点"],
        "claim_en": ["reverse-control path", "first permission source indicating flight idle", "second permission source indicating approved reverse envelope", "third permission source indicating distinct crew action", "local node enabling the reverse path only while all three permissions coexist"],
        "validation_zh": ["空中反推误选试验", "多源不一致故障注入", "许可丢失告警时间", "门锁磨损和旁路审查"],
        "validation_en": ["airborne reverse-selection test", "multi-source disagreement injection", "permission-loss caution time", "gate-wear and bypass review"],
    },
    {
        "id": "grip_release_memory", "difficulty": 48,
        "name_zh": "握持释放记忆提示", "name_en": "Grip-release memory cue",
        "principle_zh": "在关键阶段提醒“松开而不是移动”，直接针对熟练动作滑误。",
        "principle_en": "During a critical phase, cue release rather than movement to directly target practiced action slips.",
        "mechanism_zh": "握把掌根区域在阶段窗口内形成短暂的向外弹性位移或表面退让，只有放松握持才会消失；它不锁定杆位，也不阻碍飞行员主动收放推力。",
        "mechanism_en": "During a phase window the palm area develops a temporary outward displacement or yielding surface that clears only when grip pressure relaxes. It does not lock the lever or prevent deliberate thrust movement.",
        "why_zh": "不是再加起飞告警或杆位门锁，而是把提示对象从“推力设置”改为“手的下一步动作”。",
        "why_en": "It is not another takeoff warning or position lock; the cue target changes from thrust setting to the hand's next action.",
        "suitable_tags": ["action_slip", "phase_awareness", "takeoff_confirm", "ergonomics"],
        "avoid_tags": ["virtual_detent", "lever_vibration", "target_setting"],
        "risk_tags": ["haptic_feedback", "phase_awareness"],
        "claim_zh": ["具有掌根接触区的推力握把", "检测预定飞行阶段的阶段输入", "在阶段窗口改变接触区顺应性的提示构件", "响应握持释放而复位且不限制杆位的机构"],
        "claim_en": ["thrust grip with palm-contact region", "phase input detecting a defined flight phase", "cue member changing contact-region compliance during the phase window", "mechanism resetting on grip release without limiting lever position"],
        "validation_zh": ["V1 动作滑误率", "正常推力操作干扰", "紧急收杆最大时间", "不同手型和手套测试"],
        "validation_en": ["near-V1 action-slip rate", "interference with normal thrust use", "maximum emergency-retard time", "hand-size and glove testing"],
    },
]


for patent in PATENT_LANDSCAPE:
    CHUNKS.append((
        f"专利对照：{patent['publication_no']} {patent['title_zh']}",
        f"Patent landscape: {patent['publication_no']} {patent['title_en']}",
        f"权利要求摘要：{patent['claim_zh']} 设计差异提示：{'；'.join(patent['change_zh'])} 状态提示：{patent['status_zh']}",
        f"Claim summary: {patent['claim_en']} Difference prompts: {'; '.join(patent['change_en'])}. Status note: {patent['status_en']}",
        patent["source_id"],
    ))

for need in PILOT_NEEDS:
    CHUNKS.append((
        f"飞行员需求：{need['title_zh']}",
        f"Pilot need: {need['title_en']}",
        f"问题证据：{need['problem_zh']} 设计机会：{need['opportunity_zh']}",
        f"Evidence: {need['problem_en']} Design opportunity: {need['opportunity_en']}",
        need["source_id"],
    ))

# 模块加载时同步 AirworthinessKB（仅一次，结果缓存供 CHUNKS 和 initialize 共用）
# 失败自动降级到 FALLBACK_REGULATORY_CONSTRAINTS
REGULATORY_CONSTRAINTS, REGULATORY_SYNC_META = build_regulatory_constraints()

for item in REGULATORY_CONSTRAINTS:
    component = next(component for component in COMPONENTS if component["id"] == item["component_id"])
    CHUNKS.append((
        f"{item['authority']}：{component['name_zh']}限制",
        f"{item['authority']}: {component['name_en']} constraints",
        f"{item['rule_ref']}。法规/规范要求：{item['requirement_zh']} 工程解读：{item['interpretation_zh']} 适用范围：{item['applicability_zh']}",
        f"{item['rule_ref']}. Requirement: {item['requirement_en']} Engineering reading: {item['interpretation_en']} Applicability: {item['applicability_en']}",
        item["source_id"],
    ))


def initialize(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        allow_rebuild = os.environ.get("ALLOW_DESTRUCTIVE_REBUILD", "").lower() in ("1", "true", "yes")
        if not allow_rebuild:
            raise RuntimeError(
                "refusing to replace an existing knowledge database; "
                "use scripts/migrate_ontology.py or set ALLOW_DESTRUCTIVE_REBUILD=1 after backup"
            )
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        PRAGMA journal_mode=DELETE;
        CREATE TABLE sources (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            quality TEXT NOT NULL,
            organization TEXT NOT NULL,
            title_zh TEXT NOT NULL,
            title_en TEXT NOT NULL,
            url TEXT NOT NULL,
            note_zh TEXT NOT NULL,
            note_en TEXT NOT NULL,
            checked_at TEXT NOT NULL,
            license TEXT NOT NULL,
            disclaimer_zh TEXT NOT NULL,
            disclaimer_en TEXT NOT NULL
        );
        CREATE TABLE models (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            family TEXT NOT NULL,
            nation_zh TEXT NOT NULL,
            nation_en TEXT NOT NULL,
            maker_zh TEXT NOT NULL,
            maker_en TEXT NOT NULL,
            name_zh TEXT NOT NULL,
            name_en TEXT NOT NULL,
            short_zh TEXT NOT NULL,
            short_en TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(id),
            confidence TEXT NOT NULL,
            geometry_json TEXT NOT NULL,
            features_json TEXT NOT NULL
        );
        CREATE TABLE components (
            id TEXT PRIMARY KEY,
            icon TEXT NOT NULL,
            name_zh TEXT NOT NULL,
            name_en TEXT NOT NULL,
            description_zh TEXT NOT NULL,
            description_en TEXT NOT NULL,
            order_index INTEGER NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(id)
        );
        CREATE TABLE regulatory_constraints (
            id TEXT PRIMARY KEY,
            component_id TEXT NOT NULL REFERENCES components(id),
            authority TEXT NOT NULL,
            rule_ref TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(id),
            status_zh TEXT NOT NULL,
            status_en TEXT NOT NULL,
            applicability_zh TEXT NOT NULL,
            applicability_en TEXT NOT NULL,
            requirement_zh TEXT NOT NULL,
            requirement_en TEXT NOT NULL,
            interpretation_zh TEXT NOT NULL,
            interpretation_en TEXT NOT NULL,
            difference_zh TEXT NOT NULL,
            difference_en TEXT NOT NULL,
            order_index INTEGER NOT NULL
        );
        CREATE TABLE design_component_options (
            id TEXT PRIMARY KEY,
            slot_id TEXT NOT NULL,
            slot_zh TEXT NOT NULL,
            slot_en TEXT NOT NULL,
            name_zh TEXT NOT NULL,
            name_en TEXT NOT NULL,
            origin_zh TEXT NOT NULL,
            origin_en TEXT NOT NULL,
            description_zh TEXT NOT NULL,
            description_en TEXT NOT NULL,
            regulation_component_id TEXT NOT NULL REFERENCES components(id),
            change_space_zh TEXT NOT NULL,
            change_space_en TEXT NOT NULL,
            protected_zone_zh TEXT NOT NULL,
            protected_zone_en TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(id),
            order_index INTEGER NOT NULL
        );
        CREATE TABLE patents (
            id TEXT PRIMARY KEY,
            publication_no TEXT NOT NULL,
            jurisdiction TEXT NOT NULL,
            assignee TEXT NOT NULL,
            priority_date TEXT NOT NULL,
            title_zh TEXT NOT NULL,
            title_en TEXT NOT NULL,
            status_zh TEXT NOT NULL,
            status_en TEXT NOT NULL,
            claim_zh TEXT NOT NULL,
            claim_en TEXT NOT NULL,
            change_zh_json TEXT NOT NULL,
            change_en_json TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            applicable_aircraft_json TEXT NOT NULL DEFAULT '[]',
            source_id TEXT NOT NULL REFERENCES sources(id)
        );
        CREATE TABLE pilot_needs (
            id TEXT PRIMARY KEY,
            severity INTEGER NOT NULL,
            evidence_count INTEGER NOT NULL,
            title_zh TEXT NOT NULL,
            title_en TEXT NOT NULL,
            problem_zh TEXT NOT NULL,
            problem_en TEXT NOT NULL,
            opportunity_zh TEXT NOT NULL,
            opportunity_en TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            goals_json TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(id)
        );
        CREATE TABLE invention_patterns (
            id TEXT PRIMARY KEY,
            difficulty INTEGER NOT NULL,
            name_zh TEXT NOT NULL,
            name_en TEXT NOT NULL,
            principle_zh TEXT NOT NULL,
            principle_en TEXT NOT NULL,
            mechanism_zh TEXT NOT NULL,
            mechanism_en TEXT NOT NULL,
            why_zh TEXT NOT NULL,
            why_en TEXT NOT NULL,
            suitable_tags_json TEXT NOT NULL,
            avoid_tags_json TEXT NOT NULL,
            risk_tags_json TEXT NOT NULL,
            claim_zh_json TEXT NOT NULL,
            claim_en_json TEXT NOT NULL,
            validation_zh_json TEXT NOT NULL,
            validation_en_json TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(id)
        );
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_zh TEXT NOT NULL,
            title_en TEXT NOT NULL,
            body_zh TEXT NOT NULL,
            body_en TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(id),
            token_estimate INTEGER NOT NULL
        );
        CREATE TABLE prior_art_patents (
            publication_number TEXT PRIMARY KEY,
            country_code       TEXT NOT NULL,
            title_zh           TEXT NOT NULL,
            title_en           TEXT NOT NULL,
            abstract_zh        TEXT NOT NULL,
            abstract_en        TEXT NOT NULL,
            cpc_codes          TEXT NOT NULL,
            inventors          TEXT NOT NULL,
            assignees          TEXT NOT NULL,
            filing_date        TEXT NOT NULL,
            publication_date   TEXT NOT NULL,
            grant_date         TEXT,
            family_id          TEXT,
            source_id          TEXT NOT NULL REFERENCES sources(id),
            checked_at         TEXT NOT NULL,
            disclaimer_zh      TEXT NOT NULL DEFAULT 'Google Patents Public Data (CC BY 4.0)；中文为多语种字段原文，非翻译'
        );
        CREATE TABLE source_archive_runs (
            id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL,
            total_sources INTEGER NOT NULL DEFAULT 0,
            succeeded INTEGER NOT NULL DEFAULT 0,
            failed INTEGER NOT NULL DEFAULT 0,
            metadata_only INTEGER NOT NULL DEFAULT 0,
            bytes_downloaded INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE source_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL REFERENCES source_archive_runs(id),
            source_id TEXT NOT NULL REFERENCES sources(id),
            fetched_at TEXT NOT NULL,
            final_url TEXT NOT NULL,
            http_status INTEGER,
            content_type TEXT NOT NULL,
            charset TEXT NOT NULL,
            etag TEXT NOT NULL,
            last_modified TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            byte_size INTEGER NOT NULL,
            local_path TEXT NOT NULL,
            status TEXT NOT NULL,
            error TEXT NOT NULL,
            is_current INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE source_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL UNIQUE REFERENCES source_snapshots(id),
            source_id TEXT NOT NULL REFERENCES sources(id),
            title TEXT NOT NULL,
            language TEXT NOT NULL,
            extraction_method TEXT NOT NULL,
            page_count INTEGER NOT NULL DEFAULT 0,
            text_content TEXT NOT NULL,
            text_length INTEGER NOT NULL,
            word_count INTEGER NOT NULL
        );
        CREATE TABLE source_archive_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL REFERENCES source_documents(id),
            source_id TEXT NOT NULL REFERENCES sources(id),
            chunk_index INTEGER NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            char_start INTEGER NOT NULL,
            char_end INTEGER NOT NULL,
            token_estimate INTEGER NOT NULL,
            UNIQUE(document_id, chunk_index)
        );
        CREATE VIRTUAL TABLE source_archive_fts USING fts5(
            text,
            title,
            source_id UNINDEXED,
            document_id UNINDEXED,
            tokenize = 'unicode61'
        );
        CREATE INDEX idx_chunks_source ON chunks(source_id);
        CREATE INDEX idx_snapshots_source ON source_snapshots(source_id, is_current);
        CREATE INDEX idx_snapshots_run ON source_snapshots(run_id);
        CREATE INDEX idx_archive_documents_source ON source_documents(source_id);
        CREATE INDEX idx_archive_chunks_source ON source_archive_chunks(source_id);
        CREATE INDEX idx_archive_chunks_document ON source_archive_chunks(document_id, chunk_index);
        CREATE INDEX idx_models_category ON models(category);
        CREATE INDEX idx_constraints_component ON regulatory_constraints(component_id);
        CREATE INDEX idx_constraints_authority ON regulatory_constraints(authority);
        CREATE INDEX idx_design_slot ON design_component_options(slot_id);
        CREATE INDEX idx_patent_jurisdiction ON patents(jurisdiction);
        CREATE INDEX idx_needs_severity ON pilot_needs(severity DESC);
        CREATE INDEX idx_patterns_difficulty ON invention_patterns(difficulty);
        """
    )
    for source in SOURCES:
        conn.execute(
            """INSERT INTO sources
               (id, kind, quality, organization, title_zh, title_en, url,
                note_zh, note_en, checked_at, license, disclaimer_zh, disclaimer_en)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source["id"], source["kind"], source["quality"], source["org"],
                source["title_zh"], source["title_en"], source["url"],
                source["note_zh"], source["note_en"], "2026-07-29",
                source.get("license", "See source terms"),
                source.get("disclaimer_zh", "公开资料的工程检索摘要；正式使用前须核对原始来源及许可条款。"),
                source.get("disclaimer_en", "Engineering search summary of public material; verify the original source and terms before formal use."),
            ),
        )
    install_ontology(conn)
    create_cross_match_schema(conn)
    for model in MODELS:
        conn.execute(
            """INSERT INTO models VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                model["id"], model["category"], model["family"], model["nation_zh"],
                model["nation_en"], model["maker_zh"], model["maker_en"], model["name_zh"],
                model["name_en"], model["short_zh"], model["short_en"], model["source_id"],
                model["confidence"], json.dumps(model["geometry"], ensure_ascii=False),
                json.dumps(model["features"], ensure_ascii=False),
            ),
        )
    for component in COMPONENTS:
        conn.execute(
            """INSERT INTO components
               (id, icon, name_zh, name_en, description_zh, description_en, order_index, source_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                component["id"], component["icon"], component["name_zh"], component["name_en"],
                component["description_zh"], component["description_en"], component["order_index"],
                component.get("source_id", "hqy-curated-ontology"),
            ),
        )
    for item in REGULATORY_CONSTRAINTS:
        conn.execute(
            """INSERT INTO regulatory_constraints VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item["id"], item["component_id"], item["authority"], item["rule_ref"],
                item["source_id"], item["status_zh"], item["status_en"],
                item["applicability_zh"], item["applicability_en"],
                item["requirement_zh"], item["requirement_en"],
                item["interpretation_zh"], item["interpretation_en"],
                item["difference_zh"], item["difference_en"], item["order_index"],
            ),
        )
    # 记录 AirworthinessKB 同步状态（单一可信源审计追溯）
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS awkb_sync_log (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    for k, v in REGULATORY_SYNC_META.items():
        conn.execute(
            "INSERT OR REPLACE INTO awkb_sync_log(key, value) VALUES (?, ?)",
            (k, str(v)),
        )
    for option in DESIGN_COMPONENT_OPTIONS:
        conn.execute(
            """INSERT INTO design_component_options VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                option["id"], option["slot_id"], option["slot_zh"], option["slot_en"],
                option["name_zh"], option["name_en"], option["origin_zh"], option["origin_en"],
                option["description_zh"], option["description_en"], option["regulation_component_id"],
                option["change_space_zh"], option["change_space_en"],
                option["protected_zone_zh"], option["protected_zone_en"],
                json.dumps(option["tags"], ensure_ascii=False), option["source_id"], option["order_index"],
            ),
        )
    for patent in PATENT_LANDSCAPE:
        conn.execute(
            """INSERT INTO patents VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                patent["id"], patent["publication_no"], patent["jurisdiction"], patent["assignee"],
                patent["priority_date"], patent["title_zh"], patent["title_en"],
                patent["status_zh"], patent["status_en"], patent["claim_zh"], patent["claim_en"],
                json.dumps(patent["change_zh"], ensure_ascii=False),
                json.dumps(patent["change_en"], ensure_ascii=False),
                json.dumps(patent["tags"], ensure_ascii=False),
                json.dumps(patent.get("applicable_aircraft", []), ensure_ascii=False),
                patent["source_id"],
            ),
        )
    for need in PILOT_NEEDS:
        conn.execute(
            """INSERT INTO pilot_needs VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                need["id"], need["severity"], need["evidence_count"],
                need["title_zh"], need["title_en"], need["problem_zh"], need["problem_en"],
                need["opportunity_zh"], need["opportunity_en"],
                json.dumps(need["tags"], ensure_ascii=False),
                json.dumps(need["goals"], ensure_ascii=False), need["source_id"],
            ),
        )
    for pattern in INVENTION_PATTERNS:
        conn.execute(
            """INSERT INTO invention_patterns
               (id, difficulty, name_zh, name_en, principle_zh, principle_en,
                mechanism_zh, mechanism_en, why_zh, why_en, suitable_tags_json,
                avoid_tags_json, risk_tags_json, claim_zh_json, claim_en_json,
                validation_zh_json, validation_en_json, source_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pattern["id"], pattern["difficulty"], pattern["name_zh"], pattern["name_en"],
                pattern["principle_zh"], pattern["principle_en"],
                pattern["mechanism_zh"], pattern["mechanism_en"],
                pattern["why_zh"], pattern["why_en"],
                json.dumps(pattern["suitable_tags"], ensure_ascii=False),
                json.dumps(pattern["avoid_tags"], ensure_ascii=False),
                json.dumps(pattern["risk_tags"], ensure_ascii=False),
                json.dumps(pattern["claim_zh"], ensure_ascii=False),
                json.dumps(pattern["claim_en"], ensure_ascii=False),
                json.dumps(pattern["validation_zh"], ensure_ascii=False),
                json.dumps(pattern["validation_en"], ensure_ascii=False),
                pattern.get("source_id", "hqy-curated-ontology"),
            ),
        )
    for title_zh, title_en, body_zh, body_en, source_id in CHUNKS:
        token_estimate = max(1, (len(body_zh) + len(body_en)) // 4)
        conn.execute(
            """INSERT INTO chunks
               (title_zh, title_en, body_zh, body_en, source_id, token_estimate)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title_zh, title_en, body_zh, body_en, source_id, token_estimate),
        )

    # ===== 知识库扩展接入（2026-07-28）：3 张新表 =====
    # 守纪律 1：所有新表必须 REFERENCES sources(id)
    # 守纪律 3：所有非结构化字段双语并行（_zh + _en）
    # 守纪律 5：每张表的说明必须含边界声明（disclaimer）
    # 数据来源：data/knowledge_base/_generated/*.py（由 _generate_literals.py 从孤儿 JSON 转换）
    # 字面量来源的原始数据：data/knowledge_base/{triz,legal,ontology}/*.json（接入完成后清理）
    try:
        from data.knowledge_base._generated.triz_principles import TRIZ_PRINCIPLES
        from data.knowledge_base._generated.patent_law_articles import PATENT_LAW_ARTICLES
        from data.knowledge_base._generated.ata_chapters import ATA_CHAPTERS
    except ImportError:
        # 兼容直接运行 build_db.py 的场景（不走包导入）
        import importlib.util
        _gen_dir = ROOT / "data" / "knowledge_base" / "_generated"
        _mods = {}
        for _name, _var in [("triz_principles", "TRIZ_PRINCIPLES"),
                            ("patent_law_articles", "PATENT_LAW_ARTICLES"),
                            ("ata_chapters", "ATA_CHAPTERS")]:
            _p = _gen_dir / f"{_name}.py"
            if not _p.exists():
                TRIZ_PRINCIPLES, PATENT_LAW_ARTICLES, ATA_CHAPTERS = [], [], []
                break
            _spec = importlib.util.spec_from_file_location(_name, _p)
            _m = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_m)
            _mods[_var] = getattr(_m, _var)
        else:
            TRIZ_PRINCIPLES = _mods["TRIZ_PRINCIPLES"]
            PATENT_LAW_ARTICLES = _mods["PATENT_LAW_ARTICLES"]
            ATA_CHAPTERS = _mods["ATA_CHAPTERS"]

    # 表 1: triz_principles（解法域方法论，40 条）
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS triz_principles (
            id INTEGER PRIMARY KEY,
            name_zh TEXT NOT NULL,
            name_en TEXT NOT NULL,
            description_zh TEXT NOT NULL,
            description_en TEXT NOT NULL,
            aviation_examples_json TEXT NOT NULL,
            throttle_relevance INTEGER NOT NULL,
            relevance_reason_zh TEXT NOT NULL,
            relevance_reason_en TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(id),
            checked_at TEXT NOT NULL
        )
        """
    )
    for p in TRIZ_PRINCIPLES:
        conn.execute(
            """INSERT INTO triz_principles VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                p["id"], p["name_zh"], p["name_en"],
                p["description_zh"], p["description_en"],
                p["aviation_examples_json"], p["throttle_relevance"],
                p["relevance_reason_zh"], p["relevance_reason_en"],
                p["source_id"], p["checked_at"],
            ),
        )

    # 表 2: patent_law_articles（法律实体法，15 条）
    # 边界声明（守纪律 5）：本表为检索转述，不是法律意见；正式申请须由专利代理师核对官方文本
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_law_articles (
            id TEXT PRIMARY KEY,
            jurisdiction TEXT NOT NULL,
            article TEXT NOT NULL,
            title_zh TEXT NOT NULL,
            title_en TEXT NOT NULL,
            text_zh TEXT NOT NULL,
            text_en TEXT NOT NULL,
            patentability_dimension TEXT NOT NULL,
            application_notes_zh TEXT NOT NULL,
            application_notes_en TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(id),
            checked_at TEXT NOT NULL,
            disclaimer_zh TEXT NOT NULL DEFAULT '检索转述，非法律意见；正式申请须由专利代理师核对官方文本'
        )
        """
    )
    for a in PATENT_LAW_ARTICLES:
        conn.execute(
            """INSERT INTO patent_law_articles VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                a["id"], a["jurisdiction"], a["article"],
                a["title_zh"], a["title_en"], a["text_zh"], a["text_en"],
                a["patentability_dimension"],
                a["application_notes_zh"], a["application_notes_en"],
                a["source_id"], a["checked_at"],
                "检索转述，非法律意见；正式申请须由专利代理师核对官方文本",
            ),
        )

    # 表 3: ata_chapters（元分类骨架，87 条）
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ata_chapters (
            ata_code TEXT PRIMARY KEY,
            title_zh TEXT NOT NULL,
            title_en TEXT NOT NULL,
            parent_code TEXT,
            relevance_to_throttle TEXT NOT NULL,
            notes_zh TEXT NOT NULL,
            notes_en TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES sources(id),
            checked_at TEXT NOT NULL,
            FOREIGN KEY (parent_code) REFERENCES ata_chapters(ata_code)
        )
        """
    )
    # 先插顶层（parent_code=""），再插子层，避免外键失败
    top = [c for c in ATA_CHAPTERS if not c["parent_code"]]
    children = [c for c in ATA_CHAPTERS if c["parent_code"]]
    for c in top + children:
        conn.execute(
            """INSERT OR REPLACE INTO ata_chapters VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                c["ata_code"], c["title_zh"], c["title_en"],
                c["parent_code"] or None,
                c["relevance_to_throttle"],
                c["notes_zh"], c["notes_en"],
                c["source_id"], c["checked_at"],
            ),
        )

    # 把 3 张新表的关键描述字段切片进 chunks（守纪律 3：双语并行 + 一块一焦点）
    for p in TRIZ_PRINCIPLES:
        chunk_title_zh = f"TRIZ 原理 {p['id']}：{p['name_zh']}"
        chunk_title_en = f"TRIZ Principle {p['id']}: {p['name_en']}"
        chunk_body_zh = p["description_zh"]
        chunk_body_en = p["description_en"]
        token = max(1, (len(chunk_body_zh) + len(chunk_body_en)) // 4)
        conn.execute(
            """INSERT INTO chunks
               (title_zh, title_en, body_zh, body_en, source_id, token_estimate)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (chunk_title_zh, chunk_title_en, chunk_body_zh, chunk_body_en, p["source_id"], token),
        )
    for a in PATENT_LAW_ARTICLES:
        chunk_title_zh = f"{a['jurisdiction']} §{a['article']} {a['title_zh']}"
        chunk_title_en = f"{a['jurisdiction']} §{a['article']} {a['title_en']}"
        chunk_body_zh = a["text_zh"]
        chunk_body_en = a["text_en"]
        token = max(1, (len(chunk_body_zh) + len(chunk_body_en)) // 4)
        conn.execute(
            """INSERT INTO chunks
               (title_zh, title_en, body_zh, body_en, source_id, token_estimate)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (chunk_title_zh, chunk_title_en, chunk_body_zh, chunk_body_en, a["source_id"], token),
        )
    for c in ATA_CHAPTERS:
        chunk_title_zh = f"ATA {c['ata_code']} {c['title_zh']}"
        chunk_title_en = f"ATA {c['ata_code']} {c['title_en']}"
        chunk_body_zh = c["notes_zh"] or c["title_zh"]
        chunk_body_en = c["notes_en"] or c["title_en"]
        token = max(1, (len(chunk_body_zh) + len(chunk_body_en)) // 4)
        conn.execute(
            """INSERT INTO chunks
               (title_zh, title_en, body_zh, body_en, source_id, token_estimate)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (chunk_title_zh, chunk_title_en, chunk_body_zh, chunk_body_en, c["source_id"], token),
        )

    conn.commit()
    conn.close()

    manifest = {
        "version": 7,
        "generated_at": "2026-07-29",
        "database": db_path.name,
        "retrieval": "offline lexical ranking",
        "future_vector_fields": ["embedding_model", "embedding_dimensions", "embedding_blob"],
        "citation_key": "source_id",
        "chunk_policy": "one focused claim group per chunk; bilingual parallel text",
        "regulatory_scope": "FAA 14 CFR Part 25, EASA CS-25 and CAAC CCAR-25 transport/large-aeroplane throttle controls",
        "regulatory_tables": ["components", "regulatory_constraints"],
        "innovation_tables": ["design_component_options", "patents", "pilot_needs", "invention_patterns"],
        "methodology_tables": ["triz_principles", "patent_law_articles", "ata_chapters"],
        "ontology_tables": ["ontology_registry", "ontology_entities", "ontology_aliases", "ontology_relations"],
        "cross_source_tables": ["clause_mentions", "cross_match"],
        "ontology_files": ["aircraft_families.yaml", "throttle_components.yaml", "regulatory_clauses.yaml", "cpc_taxonomy.yaml"],
        "local_archive_tables": ["source_archive_runs", "source_snapshots", "source_documents", "source_archive_chunks", "source_archive_fts"],
        "patent_note": "Claim summaries and overlap prompts are search aids, not novelty, freedom-to-operate or patentability opinions.",
        "safety_note": "Public educational material only; not for aircraft operation, maintenance, certification or manufacturing.",
        "legal_note": "patent_law_articles are retrieval paraphrases; a patent professional must verify official text before filing.",
    }
    (db_path.parent / "rag_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    initialize()
    print(f"Built {DB_PATH}")
