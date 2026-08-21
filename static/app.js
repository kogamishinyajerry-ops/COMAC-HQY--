const I18N = {
  zh: {
    nav_overview: "总览", nav_studio: "专利设计", nav_library: "型号库", nav_visual: "三维对比", nav_function: "功能对比", nav_regulations: "法规约束", nav_knowledge: "知识库",
    local_online: "本地系统在线", eyebrow: "航空专利设计与证据平台", hero_title_1: "从现有设计中", hero_title_2: "找到可专利的新解。",
    hero_copy: "从飞行员真实报告选择值得解决的问题，用适航规则划出不可破坏的安全边界，再用专利权利要求定位高重合区域并生成可验证的新方案。",
    start_design: "开始专利设计", inspect_limits: "先看适航边界", stat_models: "代表型号", stat_sources: "可追溯来源", stat_chunks: "双语检索片段", stat_patents: "专利权利要求线索",
    studio_title: "第 2 章，把问题变成可交底的专利设计。", studio_copy: "选择已经核验的问题和解决方向，系统按调研对比、创新点、技术效果、布局规划和市场因素展开完整方案；现有专利用于标出已知路径和待检索边界。",
    project_name: "项目名称", design_goal: "本次创新目标", goal_safety: "降低误操作", goal_ergonomics: "改善人机工效", goal_automation: "自动化透明", goal_maintenance: "模块化维护",
    save_project: "保存到本机", export_project: "导出设计档案", assembly_steps: "参考组件基线", assembly_help: "现有组件不是最终答案；选择最接近的工程基线，帮助共同发明器识别需要改变的原理。",
    coinventor_title: "先确定模块，再由法规与专利逐层收敛创新空间。", coinventor_copy: "系统只对“双重约束后仍然成立”的创新点排序，并展开调研、技术架构、技术效果、布局和市场论证。",
    choose_patent_module: "确定需要申请专利的模块", choose_patent_module_help: "一次聚焦一个权利要求主题，避免把整台油门台写成松散拼装。",
    regulation_fence: "条款限制创新范围", regulation_fence_help: "先锁定不可破坏的安全功能，再讨论结构变化。",
    patent_fence: "现有专利排除已知路径", patent_fence_help: "高重合特征成为负约束，不直接拼进新方案。",
    residual_space: "剩余创新空间", residual_space_help: "只保留满足法规、与已知权利要求形成差异且可验证的方向。",
    rank_residual_innovations: "列举并选择剩余创新点", rank_residual_help: "已排除不符合条款或与现有专利高度重合的方向；请选择一个创新点与当前模块联合设计。",
    module_preserve: "必须保留", module_exclude: "优先排除", module_opportunity: "可创新", module_loading: "正在加载三方条款…",
    problem_source: "问题证据：选择要解决的实际问题", technical_contradiction: "技术矛盾", preferred_principle: "创新点", custom_challenge: "补充联合设计限制（可选）",
    challenge_placeholder: "例如：不能增加电机；戴手套也要操作；失电时必须可辨识……", generate_concepts: "联合设计并生成 3 种方案",
    reason_module: "所选模块", reason_problem: "真实问题", reason_regulation: "法规不变项", reason_exclude: "专利排除项", reason_mechanism: "所选创新点",
    generated_directions: "模块 × 创新点联合设计方案", generated_help: "三种方案采用不同的接口、冗余和失效架构；选择后查看完整第 2 章分析。",
    adopt_concept: "采用此方向，写入发明草案", new_principle: "新原理", technical_architecture: "技术架构", not_combination: "为什么不只是组合",
    claim_skeleton: "权利要求骨架（交代理师深化）", validation_plan: "需要证明的技术效果", concept_score: "概念评估",
    score_pilot: "问题适配", score_novelty: "专利距离", score_cert: "法规适配", score_proto: "原型可行性", score_market: "市场价值", auto_principle: "由系统排序",
    total_score: "综合分", ranking_reason: "排序理由", excluded_routes: "条低适配/高重合路线已排除",
    concept_adopted: "已写入草案",
    chapter_research: "调研情况", chapter_innovation: "创新点", chapter_effects: "技术效果", chapter_layout: "布局规划", chapter_market: "市场因素",
    research_situation: "调研情况与问题来源", research_verified: "证据与推断分开显示", problem_evidence: "问题证据", open_problem_source: "打开问题来源",
    patent_comparison: "与现有专利对比", patent_comparison_help: "不是侵权判断，用于发现已知路径和设计缺口", research_conclusion: "调研结论 / 尚未解决的缺口",
    known_solution: "已知方案", design_response: "本方案改变", no_direct_patent: "当前标签未发现直接重合，仍需扩大分类号与同族检索。",
    innovation_points: "创新点与技术架构", innovation_three_layers: "区分新技术、新架构和旧技术新用途",
    innovation_new_tech: "新技术", innovation_new_tech_title: "新的工作原理", innovation_new_arch: "新架构", innovation_new_arch_title: "新的构件关系",
    innovation_reuse: "旧技术用于新架构", innovation_reuse_title: "成熟构件的新角色", core_innovation: "核心创新点（一句话）",
    concrete_embodiment: "具体实施构想", prototype_parts: "样机构件清单", prototype_parts_help: "编号可直接用于结构草图",
    action_sequence: "完整动作序列", action_sequence_help: "说明何时动作、怎样动作、如何复位", existing_path: "现有常见路径",
    specific_difference: "本构想的具体差异", claim_hook: "独立权利要求抓手",
    innovation_breakdown: "创新点详细拆解", innovation_breakdown_help: "把概念拆成可画图、可做样机、可写权利要求的技术要素",
    innovation_conflict: "要解决的技术矛盾", innovation_elements: "关键构件", innovation_relationship: "构件关系",
    innovation_logic: "控制 / 动作逻辑", innovation_failure: "失效与人工超控", innovation_protection: "申请时重点限定",
    technical_effects: "技术效果与验证方法", effects_pending: "效果为待验证假设，不写成既成事实", effect_structure: "结构变化", effect_action: "作用机制", effect_direct: "直接效果", effect_metric: "可测指标",
    layout_planning: "布局规划", layout_concept_note: "概念分区，不是制造尺寸图", layout_rules: "布局决策", layout_rules_help: "按操作、识别、安全和维护四条线规划",
    market_factors: "市场因素与落地路径", market_no_forecast: "定性筛选，不构成市场规模预测", market_target: "目标应用", market_customer: "潜在客户",
    market_entry: "建议切入路径", market_barrier: "主要商业化障碍", market_screening: "方案筛选指标", patent_negative_constraints: "需要继续检索的专利边界",
    current_concept: "当前概念", change_space: "可以重点创新", protected_boundary: "不可破坏的边界", open_full_rules: "打开三方完整适航条款",
    patent_analysis: "专利重合雷达", patent_documents: "件专利文献", patent_intro: "按当前问题与候选方案的技术特征匹配公开权利要求摘要。高重合不是侵权结论，但意味着申请前必须形成可验证的结构、控制原理或技术效果差异。",
    need_analysis: "飞行员痛点优先级", verified_needs: "条核验证据", need_intro: "来自 NASA ASRS 飞行员报告与 AAIB 调查。优先级结合严重度、证据数量和当前设计目标，不把论坛意见当成事实。",
    invention_brief: "发明问题定义", copy_brief: "复制草案", brief_problem: "待解决问题", brief_mechanism: "拟采用机制", brief_difference: "需要证明的差异", brief_evidence: "建议验证证据",
    patent_legal_note: "本工具用于检索与发明构思，不构成新颖性、创造性、自由实施或可专利性法律意见。正式申请前应由专利代理师检索完整权利要求、同族、引证和法律状态。",
    source_reference: "原始证据", overlap: "重合", difference_prompt: "需形成差异", priority_score: "优先级", saved: "已保存", copied: "已复制",
    primer: "PRIMER · 基础", intro_title: "油门台，不只是“加减速”。", intro_copy: "它连接飞行员意图、发动机控制、自动飞行和任务系统。民航重视程序、可见性与防误操作；军机则将大量任务功能压缩到双手可及范围。",
    concept_civil: "民航中央油门台", concept_civil_copy: "推力、反推、自动油门断开、TO/GA 与明确卡位；方便双人机组观察和交叉检查。",
    concept_hot: "军用 HOTAS", concept_hot_copy: "Hands On Throttle And Stick：把通信、传感器、武器和防御输入留在双手之下。",
    concept_auto: "自动推力逻辑", concept_auto_copy: "有些手柄会随自动系统移动，有些保持在卡位。外观相似，反馈哲学却完全不同。",
    photo_title: "公开影像档案", photo_copy: "实物照片用于认识布局；点击来源可核验作者、时间与许可。", photo_a320: "推力手柄与中央操纵台", photo_boeing: "经典中央油门台布局", photo_f16: "侧置操纵与 HOTAS 环境", photo_typhoon: "台风座舱与 VTAS", photo_su35: "双发战斗机驾驶舱",
    library_title: "选择你的研究对象。", library_copy: "覆盖空客、波音、商飞、美国 F 系列、欧洲系列与俄罗斯苏系列。证据不足的细节会明确标注，不以推测补空白。",
    all_models: "全部", commercial: "商用", military: "军用", evidence_high: "高可信", evidence_limited: "公开细节有限",
    visual_title: "放在同一空间里看。", visual_copy: "选择任意两个型号，拖动旋转、滚轮缩放；并列看结构，叠加看体量与手柄布局差异。",
    model_a: "模型 A", model_b: "模型 B", side_view: "并列", overlay_view: "叠加", auto_rotate: "自动旋转", reset_view: "重置视角", drag_help: "拖动旋转 · 滚轮缩放",
    model_disclaimer_title: "示意模型，不是原厂 CAD。", model_disclaimer: "三维形态依据公开照片与高层功能特征参数化生成，仅比较基座、手柄数量、分体方式和控制密度；不得用于制造、维修或适航。",
    function_title: "功能差异，逐项对齐。", function_copy: "同一字段、同一尺度；差异项自动高亮。", dimension: "对比维度",
    regulation_title: "选一个组件，看三方限制。", regulation_copy: "选择正推力杆、反推力杆等组件，逐栏查看 FAA、EASA、CAAC 的条款、强制性要求与工程含义。法规原文和工程解读明确分开。",
    regulation_scope: "当前范围：运输类 / 大型飞机。具体型号的审定基础、修订版、专用条件和符合性方法可能不同；本模块不是适航批准结论。",
    choose_component: "选择组件", selected_component: "当前组件", common_baseline: "共同设计基线", baseline_copy: "防误动、操作方向明确、控制响应及时，并通过布局和门锁降低机组差错。",
    legal_requirement: "法规 / 规范要求", engineering_reading: "工程解读", authority_difference: "本机构要点", official_source: "官方原文", applicable_scope: "适用范围",
    regulation_note: "条款摘要为便于设计检索的双语转述；做符合性工作时，请打开官方来源核对完整条文与适用修订版。", query_regulation: "反推法规",
    knowledge_title: "每个结论，都能回到出处。", knowledge_copy: "公开网页与 PDF 已按原始来源下载到本机，提取正文、切片并写入 SQLite。检索同时覆盖人工整理知识与本地原文，且保留 URL、下载时间、哈希和引用键。",
    rag_sources: "来源", rag_chunks: "切片", rag_retrieve: "检索", rag_cite: "引用", search_placeholder: "搜索：A320 自动推力为什么不带动手柄？", search: "检索", try_queries: "试试：",
    query_difference: "民航 vs 军用", query_boundary: "证据边界", search_results: "检索结果", db_status: "数据库状态", verified_sources: "条已核验来源",
    db_engine: "引擎", db_mode: "检索", db_language: "语言", db_citation: "引用键", view_all_sources: "查看全部来源", source_register: "来源登记册",
    archive_local: "本地原文", archive_sources: "本地来源", archive_chunks: "原文切片", archive_size: "归档大小", archive_sync: "最近同步", archive_pending: "尚未同步", archive_failed: "项待补采",
    footer_note: "公开资料教育与研究用途 · 不用于实际飞行、维修、适航或制造",
    select_a: "放入 A", select_b: "放入 B", high: "高可信", limited: "有限证据", commercial_label: "商用", military_label: "军用",
    no_results: "没有找到直接匹配。可尝试“自动推力”“HOTAS”“民航 军用”或型号名称。", source_link: "打开原始来源", match: "匹配",
    source_open: "核验来源", close: "关闭",
    feature_engine_channels: "发动机 / 通道", feature_control_philosophy: "控制哲学", feature_automation: "自动化", feature_automation_motion: "自动模式手柄运动",
    feature_detents: "卡位 / 行程", feature_reverse: "反推", feature_afterburner: "加力", feature_hotas: "HOTAS 集成", feature_special: "主要交互", feature_evidence: "证据状态"
  },
  en: {
    nav_overview: "Overview", nav_studio: "Patent design", nav_library: "Model library", nav_visual: "3D compare", nav_function: "Functions", nav_regulations: "Regulations", nav_knowledge: "Knowledge",
    local_online: "Local system online", eyebrow: "Aviation patent-design evidence platform", hero_title_1: "Turn existing designs", hero_title_2: "into a patentable new answer.",
    hero_copy: "Select an urgent problem from real pilot reports, use airworthiness rules to define the safety boundary, then locate claim overlap and generate a testable new solution.",
    start_design: "Start patent design", inspect_limits: "Inspect airworthiness first", stat_models: "representative models", stat_sources: "traceable sources", stat_chunks: "bilingual chunks", stat_patents: "patent-claim leads",
    studio_title: "Chapter 2 turns a problem into an invention disclosure.", studio_copy: "Choose a verified problem and solution direction, then expand it into research comparison, innovation, technical effects, layout planning and market factors. Existing patents mark known paths and boundaries that still require searching.",
    project_name: "Project name", design_goal: "Innovation goal", goal_safety: "Reduce slips", goal_ergonomics: "Improve ergonomics", goal_automation: "Expose automation", goal_maintenance: "Modular maintenance",
    save_project: "Save locally", export_project: "Export design file", assembly_steps: "Reference component baseline", assembly_help: "Existing components are not the answer. Choose the nearest engineering baseline so the co-inventor can identify which principle must change.",
    coinventor_title: "Choose a module, then narrow the innovation space through regulations and patents.", coinventor_copy: "Only ideas that survive both constraint layers are ranked, then expanded into research, architecture, effects, layout and market reasoning.",
    choose_patent_module: "Choose the patent module", choose_patent_module_help: "Keep one claim subject in focus instead of claiming the whole quadrant as a loose aggregation.",
    regulation_fence: "Regulations constrain the design space", regulation_fence_help: "Freeze safety functions that must not be broken before changing the structure.",
    patent_fence: "Existing patents exclude known paths", patent_fence_help: "High-overlap features become negative constraints—not ingredients to copy.",
    residual_space: "Residual innovation space", residual_space_help: "Keep only directions that comply, differ from known claims and can be tested.",
    rank_residual_innovations: "List and choose residual innovation points", rank_residual_help: "Non-compliant and high-overlap directions have been removed. Choose one point to combine with the current module.",
    module_preserve: "Preserve", module_exclude: "Exclude first", module_opportunity: "Open space", module_loading: "Loading three-authority provisions…",
    problem_source: "Problem evidence: choose the real problem", technical_contradiction: "Technical contradiction", preferred_principle: "Innovation point", custom_challenge: "Add joint-design constraints (optional)",
    challenge_placeholder: "For example: no added motor; must work with gloves; power loss must remain evident…", generate_concepts: "Joint-design 3 schemes",
    reason_module: "Selected module", reason_problem: "Real problem", reason_regulation: "Regulatory invariants", reason_exclude: "Patent exclusions", reason_mechanism: "Selected innovation",
    generated_directions: "Module × innovation joint-design schemes", generated_help: "The three schemes use different interface, redundancy and failure architectures. Select one to inspect the complete Chapter 2 analysis.",
    adopt_concept: "Adopt direction into invention brief", new_principle: "New principle", technical_architecture: "Technical architecture", not_combination: "Why this is not mere aggregation",
    claim_skeleton: "Claim skeleton (for patent counsel to refine)", validation_plan: "Technical effects to prove", concept_score: "Concept assessment",
    score_pilot: "Problem fit", score_novelty: "Patent distance", score_cert: "Regulatory fit", score_proto: "Prototype feasibility", score_market: "Market value", auto_principle: "System ranking",
    total_score: "Total", ranking_reason: "Ranking rationale", excluded_routes: "low-fit / high-overlap routes excluded",
    concept_adopted: "Written to brief",
    chapter_research: "Research", chapter_innovation: "Innovation", chapter_effects: "Technical effects", chapter_layout: "Layout plan", chapter_market: "Market factors",
    research_situation: "Research basis and problem source", research_verified: "Evidence and inference shown separately", problem_evidence: "Problem evidence", open_problem_source: "Open problem source",
    patent_comparison: "Comparison with existing patents", patent_comparison_help: "Not an infringement finding; used to expose known paths and design gaps", research_conclusion: "Research conclusion / unresolved gap",
    known_solution: "Known approach", design_response: "Concept change", no_direct_patent: "No direct tag overlap was found; classification and family searching still need to be expanded.",
    innovation_points: "Innovation and technical architecture", innovation_three_layers: "Separate new technology, new architecture and known technology in a new role",
    innovation_new_tech: "New technology", innovation_new_tech_title: "New operating principle", innovation_new_arch: "New architecture", innovation_new_arch_title: "New relationship between elements",
    innovation_reuse: "Known tech in a new architecture", innovation_reuse_title: "New role for mature elements", core_innovation: "Core innovation in one sentence",
    concrete_embodiment: "Concrete embodiment", prototype_parts: "Prototype parts", prototype_parts_help: "Use the labels directly in a structural sketch",
    action_sequence: "Complete action sequence", action_sequence_help: "Show when it acts, how it acts and how it resets", existing_path: "Common existing path",
    specific_difference: "Specific difference in this concept", claim_hook: "Independent-claim hook",
    innovation_breakdown: "Detailed innovation breakdown", innovation_breakdown_help: "Translate the concept into elements that can be drawn, prototyped and claimed",
    innovation_conflict: "Technical contradiction to solve", innovation_elements: "Key elements", innovation_relationship: "Element relationships",
    innovation_logic: "Control / action logic", innovation_failure: "Failure and manual override", innovation_protection: "Key claim limitations",
    technical_effects: "Technical effects and validation", effects_pending: "Effects are hypotheses to prove—not established facts", effect_structure: "Structural change", effect_action: "Operating mechanism", effect_direct: "Direct effect", effect_metric: "Measurable metric",
    layout_planning: "Layout planning", layout_concept_note: "Concept zoning—not a manufacturing drawing", layout_rules: "Layout decisions", layout_rules_help: "Plan around operation, recognition, safety and service",
    market_factors: "Market factors and route to adoption", market_no_forecast: "Qualitative screening—not a market-size forecast", market_target: "Target application", market_customer: "Potential customer",
    market_entry: "Recommended entry path", market_barrier: "Main commercialization barrier", market_screening: "Concept screening metrics", patent_negative_constraints: "Patent boundaries requiring further search",
    current_concept: "Current concept", change_space: "Priority innovation space", protected_boundary: "Boundary to preserve", open_full_rules: "Open full three-authority rules",
    patent_analysis: "Patent overlap radar", patent_documents: "patent documents", patent_intro: "Matches the current problem and candidate concept against public claim summaries. High overlap is not an infringement finding, but it signals that the application needs a verifiable difference in structure, control principle or technical effect.",
    need_analysis: "Pilot-pain priority", verified_needs: "verified evidence items", need_intro: "Drawn from NASA ASRS pilot reports and AAIB investigations. Priority combines severity, evidence count and your design goal rather than treating forum opinion as fact.",
    invention_brief: "Invention problem brief", copy_brief: "Copy draft", brief_problem: "Problem to solve", brief_mechanism: "Proposed mechanism", brief_difference: "Difference to prove", brief_evidence: "Suggested evidence",
    patent_legal_note: "This tool supports search and invention ideation; it is not a novelty, inventive-step, freedom-to-operate or patentability opinion. Before filing, a patent professional should search full claims, families, citations and official legal status.",
    source_reference: "Source evidence", overlap: "overlap", difference_prompt: "difference needed", priority_score: "priority", saved: "Saved", copied: "Copied",
    primer: "PRIMER", intro_title: "A throttle is more than “faster or slower.”", intro_copy: "It connects pilot intent, engine control, autoflight and mission systems. Civil designs favor procedure, visibility and error resistance; fighters compress mission controls under both hands.",
    concept_civil: "Civil center quadrant", concept_civil_copy: "Thrust, reverse, autothrottle disconnect, TO/GA and clear detents—visible to both pilots for cross-checking.",
    concept_hot: "Combat HOTAS", concept_hot_copy: "Hands On Throttle And Stick keeps communications, sensors, weapons and defensive inputs under the pilot's hands.",
    concept_auto: "Automation logic", concept_auto_copy: "Some levers move with automation; others remain in a detent. Similar objects can embody very different feedback philosophies.",
    photo_title: "Public image archive", photo_copy: "Use real photographs to recognize layout; open each source to verify author, date and license.", photo_a320: "Thrust levers and center pedestal", photo_boeing: "Classic center-quadrant layout", photo_f16: "Side control and HOTAS context", photo_typhoon: "Typhoon cockpit and VTAS", photo_su35: "Twin-engine fighter cockpit",
    library_title: "Choose your research subject.", library_copy: "Airbus, Boeing, COMAC, U.S. F-series, European fighters and the Russian Su-series. Where evidence is thin, the gap is marked instead of guessed.",
    all_models: "All", commercial: "Civil", military: "Combat", evidence_high: "High confidence", evidence_limited: "Limited public detail",
    visual_title: "Place both in one space.", visual_copy: "Select any two, drag to rotate and scroll to zoom. Use split view for structure and overlay for volume and lever-layout differences.",
    model_a: "Model A", model_b: "Model B", side_view: "Split", overlay_view: "Overlay", auto_rotate: "Auto rotate", reset_view: "Reset view", drag_help: "Drag to rotate · Scroll to zoom",
    model_disclaimer_title: "Conceptual models—not OEM CAD.", model_disclaimer: "Parametric shapes are based on public photographs and high-level functions. They compare base, lever count, split layout and control density; never use them for manufacturing, maintenance or airworthiness.",
    function_title: "Align functions, field by field.", function_copy: "Same fields, same scale; differences are highlighted automatically.", dimension: "Dimension",
    regulation_title: "Pick a component. See all three limits.", regulation_copy: "Select a forward-thrust lever, reverse-thrust lever or related component to compare FAA, EASA and CAAC provisions, mandatory language and engineering meaning side by side.",
    regulation_scope: "Current scope: transport-category / large aeroplanes. Certification basis, amendment, special conditions and means of compliance vary by project; this module is not an approval finding.",
    choose_component: "Choose component", selected_component: "Selected component", common_baseline: "Common design baseline", baseline_copy: "Resist inadvertent operation, make direction unambiguous, respond promptly, and use layout and gates to reduce crew error.",
    legal_requirement: "Regulation / specification", engineering_reading: "Engineering reading", authority_difference: "Authority note", official_source: "Official text", applicable_scope: "Applicability",
    regulation_note: "Summaries are bilingual design-search paraphrases. For compliance work, open the official source and verify the full text and applicable amendment.", query_regulation: "Reverse rules",
    knowledge_title: "Every conclusion leads back to a source.", knowledge_copy: "Public webpages and PDFs are downloaded locally, text-extracted, chunked and stored in SQLite. Search covers both curated knowledge and archived source text while preserving URLs, fetch time, hashes and citation keys.",
    rag_sources: "Sources", rag_chunks: "Chunks", rag_retrieve: "Retrieve", rag_cite: "Cite", search_placeholder: "Search: Why don't A320 levers move with autothrust?", search: "Search", try_queries: "Try:",
    query_difference: "Civil vs combat", query_boundary: "Evidence limits", search_results: "Search results", db_status: "Database status", verified_sources: "verified sources",
    db_engine: "Engine", db_mode: "Retrieval", db_language: "Languages", db_citation: "Citation key", view_all_sources: "View all sources", source_register: "Source register",
    archive_local: "Local source", archive_sources: "Local sources", archive_chunks: "Source chunks", archive_size: "Archive size", archive_sync: "Last sync", archive_pending: "Not synced", archive_failed: "pending retries",
    footer_note: "Public-source education and research · Not for flight, maintenance, certification or manufacturing",
    select_a: "Set as A", select_b: "Set as B", high: "High confidence", limited: "Limited evidence", commercial_label: "Civil", military_label: "Combat",
    no_results: "No direct match. Try “autothrust”, “HOTAS”, “civil combat”, or a model name.", source_link: "Open primary source", match: "Match",
    source_open: "Verify source", close: "Close",
    feature_engine_channels: "Engine / channels", feature_control_philosophy: "Control philosophy", feature_automation: "Automation", feature_automation_motion: "Lever motion in auto",
    feature_detents: "Detents / travel", feature_reverse: "Reverse thrust", feature_afterburner: "Afterburner", feature_hotas: "HOTAS integration", feature_special: "Primary interactions", feature_evidence: "Evidence status"
  }
};

const FEATURE_ROWS = [
  ["engine_channels", "feature_engine_channels"],
  ["control_philosophy", "feature_control_philosophy"],
  ["automation", "feature_automation"],
  ["automation_motion", "feature_automation_motion"],
  ["detents", "feature_detents"],
  ["reverse", "feature_reverse"],
  ["afterburner", "feature_afterburner"],
  ["hotas", "feature_hotas"],
  ["special", "feature_special"],
  ["evidence", "feature_evidence"]
];

const PATENT_MODULES = [
  {
    id: "thrust_levers", code: "M01", figure: "lever",
    name_zh: "正 / 反推力杆", name_en: "Forward / reverse thrust levers",
    scope_zh: "研究飞行员直接握持和移动的输入构件，包括握把、正推行程、反推动作与卡位界面；不把轮毂传动和自动油门驱动本体混入同一独立权利要求。",
    scope_en: "Covers the pilot-contact input elements, forward travel, reverse action and detent interface. Hub transmission and autothrottle drive remain separate claim subjects.",
    regulatoryIds: ["forward_lever", "reverse_lever", "flight_idle_gate", "retention_layout"],
    patentTags: ["multi_track", "continuous_control", "discrete_detent", "programmable_reverse", "adjustable_detent", "moving_lever", "motor_drive", "haptic_feedback", "integrated_indicator"],
    needTags: ["action_slip", "phase_awareness", "tactile_gate", "autothrottle_status", "ergonomics"],
    preserve_zh: ["前移增加正推力，离开正推力区须有独立明确动作", "防误动且能保持设定位置，主行程连续、人工权威不丢失", "各发动机可独立操纵，也可同时操纵且不混淆"],
    preserve_en: ["Forward motion increases thrust; leaving forward thrust requires a separate distinct action", "Prevent inadvertent operation, hold the selected position and preserve continuous manual authority", "Support individual and simultaneous engine control without ambiguity"],
    exclude_zh: ["电机带动手柄本身", "可编程反推卡位本身", "把显示器或振动器直接装进握把"],
    exclude_en: ["Motor-driven lever motion by itself", "A programmable reverse detent by itself", "Simply placing a display or vibrator in the grip"],
    opportunities_zh: ["用握持形态而非附加按钮表达许可状态", "只在错误动作方向产生确定阻抗", "把反推意图与正推连续载荷路径机械隔离"],
    opportunities_en: ["Encode permission through grip geometry instead of another button", "Create defined resistance only in the erroneous action direction", "Mechanically isolate reverse intent from the continuous forward-thrust load path"],
    mature_zh: "机械止动、弹簧偏置、独立反推手臂", mature_en: "mechanical stops, spring biasing and an independent reverse arm",
    mechanism_zh: "创新应发生在“手—握把—行程”的意图传递关系中，而不是复制已知驱动、显示或卡位功能。",
    mechanism_en: "Innovation should change the hand–grip–travel intent path rather than repeat known drive, display or detent functions.",
    nodes_zh: ["握持输入", "方向判别", "独立门槛", "推力指令"], nodes_en: ["Grip input", "Direction discriminator", "Independent gate", "Thrust command"],
    market_zh: "新研运输机、训练台架及高保真模拟器的人因验证", market_en: "New transport aircraft, bench rigs and high-fidelity simulator validation",
    marketScore: 88, certBase: 78,
    affinity: {passive_state_morphing:88,directional_impedance:96,grip_travel_transform:80,intent_vector_gate:78,differential_truth_flag:72,fail_open_module:58,reverse_permission_token:90,grip_release_memory:92}
  },
  {
    id: "lever_hubs", code: "M02", figure: "hub",
    name_zh: "正 / 反推力轮毂", name_en: "Forward / reverse lever hubs",
    scope_zh: "研究力杆根部的转轴、轴承、扭矩耦合、角度基准和正反推通道隔离；手柄造型、传感器算法和自动油门电机分别作为外部接口。",
    scope_en: "Covers pivot shafts, bearings, torque coupling, angular references and separation of forward/reverse paths at the lever root. Grip shape, sensing algorithms and autothrottle motors remain interfaces.",
    regulatoryIds: ["forward_lever", "reverse_lever", "retention_layout", "engine_grouping"],
    patentTags: ["moving_lever", "friction_clutch", "motor_drive", "manual_override", "multi_track", "continuous_control", "mounting_lock"],
    needTags: ["manual_override", "maintenance", "modular_channel", "tactile_differentiation", "full_travel"],
    preserve_zh: ["足够强度和刚度，振动与载荷下不得滑移", "主推力连续行程和人工最终操纵权不被新耦合件阻断", "双发通道可分离校准且不得互相串扰"],
    preserve_en: ["Provide strength and stiffness without load- or vibration-induced creep", "No new coupling may interrupt continuous travel or final manual authority", "Twin-engine channels remain separately calibratable without cross-coupling"],
    exclude_zh: ["常规摩擦离合器自动/手动切换", "多导轨连续控制本身", "简单可释放安装锁"],
    exclude_en: ["Conventional friction-clutch auto/manual switching", "Multi-track continuous control by itself", "A simple releasable mounting lock"],
    opportunities_zh: ["同轴但力路隔离的正反推轮毂", "可见失效的脱开联轴结构", "免拆主轴的键控标定与模块更换"],
    opportunities_en: ["Coaxial hubs with separated forward/reverse load paths", "A disengaging coupling whose failure state is evident", "Keyed calibration and module replacement without removing the main shaft"],
    mature_zh: "滚动轴承、花键、扭簧和机械索引", mature_en: "rolling bearings, splines, torsion springs and mechanical indexing",
    mechanism_zh: "创新重点是轮毂之间如何传力、隔离和显露失效，而非单个轴承或离合器。",
    mechanism_en: "The inventive focus is how hubs transmit, isolate and reveal torque—not the bearing or clutch alone.",
    nodes_zh: ["主轴基准", "隔离轮毂", "失效脱开", "角度输出"], nodes_en: ["Shaft datum", "Isolated hub", "Fail-disconnect", "Angle output"],
    market_zh: "新研油门台、可维护改型组件和试验台模块", market_en: "New throttle quadrants, maintainable upgrade modules and test-bench assemblies",
    marketScore: 82, certBase: 84,
    affinity: {passive_state_morphing:74,directional_impedance:88,grip_travel_transform:68,intent_vector_gate:64,differential_truth_flag:76,fail_open_module:98,reverse_permission_token:82,grip_release_memory:62}
  },
  {
    id: "interlock", code: "M03", figure: "interlock",
    name_zh: "互锁机构", name_en: "Interlock mechanism",
    scope_zh: "研究 Flight Idle、反推许可、地面状态和燃油切断等高风险动作之间的机械/机电许可关系；不把整套飞控逻辑或反推系统包线作为本模块权利要求。",
    scope_en: "Covers mechanical or electromechanical permission relationships among Flight Idle, reverse permission, ground state and fuel cutoff. Full flight-control logic and reverse-envelope control remain outside this claim subject.",
    regulatoryIds: ["reverse_lever", "flight_idle_gate", "fuel_cutoff"],
    patentTags: ["programmable_reverse", "adjustable_detent", "rollout_target", "multi_track", "mode_switch", "manual_override", "virtual_detent"],
    needTags: ["flight_idle_gate", "shutdown_safety", "action_slip", "distinct_action", "takeoff_confirm"],
    preserve_zh: ["只有到达 Flight Idle 后才能通过另一明确动作离开正推力状态", "防止在批准包线外选择或激活反推，失效不得形成危险超控", "燃油切断同样需要确定止动和独立动作"],
    preserve_en: ["Leaving forward thrust requires Flight Idle plus a separate distinct action", "Prevent reverse selection outside the approved envelope without a hazardous override", "Fuel cutoff likewise requires a positive stop and distinct action"],
    exclude_zh: ["可编程反推卡位", "由单一软件许可位控制的电磁锁", "把常规门锁换成另一种形状"],
    exclude_en: ["A programmable reverse detent", "A solenoid controlled by one software permission bit", "Merely reshaping a conventional gate"],
    opportunities_zh: ["由独立事实共同形成的分布式许可结构", "失电自动退回开放主推力路径的互锁", "许可链断裂时能直接显示故障位置"],
    opportunities_en: ["A distributed permission structure formed by independent facts", "An interlock that loses power into an open primary-thrust path", "Direct localization of the failed condition in the permission chain"],
    mature_zh: "孔板、梭体、弹簧复位和机械止动", mature_en: "apertured plates, shuttles, spring return and mechanical stops",
    mechanism_zh: "创新重点是多个独立事实如何共同形成许可，以及任一事实消失后如何安全解构许可。",
    mechanism_en: "The key is how independent facts jointly create permission and how loss of any fact safely dismantles it.",
    nodes_zh: ["状态输入", "许可对孔", "安全梭体", "动作通道"], nodes_en: ["State inputs", "Permission alignment", "Safety shuttle", "Action path"],
    market_zh: "反推/断油安全机构、新研运输机和审定验证台架", market_en: "Reverse/fuel-cutoff safety mechanisms, new transport aircraft and certification rigs",
    marketScore: 91, certBase: 72,
    affinity: {passive_state_morphing:76,directional_impedance:88,grip_travel_transform:54,intent_vector_gate:94,differential_truth_flag:82,fail_open_module:90,reverse_permission_token:100,grip_release_memory:72}
  },
  {
    id: "fuel_control", code: "M04", figure: "fuel",
    name_zh: "燃油控制开关", name_en: "Fuel-control switch",
    scope_zh: "研究 RUN/CUTOFF 操纵件、保护罩、止动、独立动作和状态呈现；发动机燃油计量本体、FADEC 内部算法及线路保护不属于本模块。",
    scope_en: "Covers RUN/CUTOFF controls, guards, stops, distinct actions and state presentation. Fuel metering, internal FADEC algorithms and wiring protection remain outside the module.",
    regulatoryIds: ["fuel_cutoff", "flight_idle_gate", "retention_layout"],
    patentTags: ["mode_switch", "manual_override", "integrated_indicator", "handle_visual", "corrective_action", "discrete_detent"],
    needTags: ["shutdown_safety", "action_slip", "persistent_status", "mode_awareness", "ergonomics"],
    preserve_zh: ["不得误入 CUTOFF，慢车处必须有确定锁或止动", "进入断油必须采用另一明确动作", "失电、烟雾或低能见度下仍需能辨识真实位置"],
    preserve_en: ["Prevent inadvertent CUTOFF with a positive idle lock or stop", "Entering cutoff requires another distinct action", "True position remains discernible during power loss, smoke or poor visibility"],
    exclude_zh: ["在开关上集成普通视觉指示", "常规模式切换开关", "单纯增加保护罩或灯"],
    exclude_en: ["A conventional visual indicator integrated into the switch", "A conventional mode selector", "Simply adding a guard or lamp"],
    opportunities_zh: ["动作后由开关几何保留机械记忆", "双动作路径共享一个可触状态编码", "失电时暴露真实断油链状态"],
    opportunities_en: ["Mechanical state memory retained in switch geometry after action", "Two-action paths sharing a tactile state code", "Exposure of the true cutoff-chain state after power loss"],
    mature_zh: "保护罩、过中心弹簧、机械旗标和独立止动", mature_en: "guards, over-centre springs, mechanical flags and independent stops",
    mechanism_zh: "创新应把“是否允许、是否已执行、是否真实生效”分开表达，而不是只改变开关外观。",
    mechanism_en: "Innovation should separate permission, commanded action and actual effect rather than merely restyle the switch.",
    nodes_zh: ["手动意图", "独立动作", "机械记忆", "断油状态"], nodes_en: ["Manual intent", "Distinct action", "Mechanical memory", "Cutoff state"],
    market_zh: "运输机燃油控制面板、直升机动力控制和训练设备", market_en: "Transport-aircraft fuel panels, rotorcraft power controls and training devices",
    marketScore: 86, certBase: 80,
    affinity: {passive_state_morphing:96,directional_impedance:78,grip_travel_transform:56,intent_vector_gate:94,differential_truth_flag:92,fail_open_module:82,reverse_permission_token:78,grip_release_memory:88}
  },
  {
    id: "angle_resolver", code: "M05", figure: "resolver",
    name_zh: "角度解算器", name_en: "Angle resolver",
    scope_zh: "研究从力杆轴角到双通道电信号的测量、基准、自检、差异监控和更换标定；推力控制律和执行机构不属于本模块。",
    scope_en: "Covers measurement from lever angle to dual-channel electrical output, datum, self-test, disagreement monitoring and replacement calibration. Thrust-control laws and actuators remain outside the module.",
    regulatoryIds: ["forward_lever", "engine_grouping", "retention_layout"],
    patentTags: ["target_setting", "dynamic_position", "integrated_indicator", "haptic_feedback", "moving_lever", "motor_drive", "corrective_action"],
    needTags: ["mode_awareness", "persistent_status", "thrust_target_display", "maintenance", "modular_channel"],
    preserve_zh: ["每台发动机控制通道可独立识别且响应确定及时", "任何新传感器不得导致控制混淆或隐藏杆位漂移", "拆换后可验证标定，单点故障不得伪装成有效杆位"],
    preserve_en: ["Each engine-control channel remains identifiable with definite and timely response", "No sensor may create control ambiguity or hide lever-position drift", "Replacement calibration is testable and no single failure may masquerade as a valid position"],
    exclude_zh: ["普通单通道角度传感器", "把目标设定显示集成到手柄", "用动态虚拟卡位代替角度测量"],
    exclude_en: ["A conventional single-channel angle sensor", "Target-setting display integrated into the lever", "Replacing angle measurement with a dynamic virtual detent"],
    opportunities_zh: ["异构双通道解算与局部机械基准", "指令角—实际轴角—执行效果的三量差分", "更换后无需主机构重装的自标定接口"],
    opportunities_en: ["Heterogeneous dual-channel resolution with a local mechanical datum", "Three-way comparison of commanded angle, shaft angle and achieved effect", "Self-calibration after replacement without rebuilding the primary mechanism"],
    mature_zh: "旋转变压器、磁编码器、机械零位键和测试绕组", mature_en: "resolvers, magnetic encoders, mechanical zero keys and test windings",
    mechanism_zh: "创新重点是异构测量、局部基准和差异诊断的关系，而非传感器元件本身。",
    mechanism_en: "The invention lies in the relationship among heterogeneous sensing, local datum and disagreement diagnosis—not the sensor element alone.",
    nodes_zh: ["机械零位", "异构测量", "差分诊断", "双通道输出"], nodes_en: ["Mechanical zero", "Diverse sensing", "Difference diagnosis", "Dual-channel output"],
    market_zh: "电子油门台、改进型传感器 LRU 和健康监测系统", market_en: "Electronic throttle quadrants, improved sensor LRUs and health-monitoring systems",
    marketScore: 84, certBase: 88,
    affinity: {passive_state_morphing:82,directional_impedance:64,grip_travel_transform:52,intent_vector_gate:68,differential_truth_flag:100,fail_open_module:94,reverse_permission_token:58,grip_release_memory:70}
  },
  {
    id: "autothrottle", code: "M06", figure: "autothrottle",
    name_zh: "自动油门机构", name_en: "Autothrottle mechanism",
    scope_zh: "研究自动油门电机、减速器、离合/脱开、人工超控、随动或静态杆位反馈之间的机械架构；自动飞行控制律与发动机控制律不在本模块内。",
    scope_en: "Covers the mechanical architecture among autothrottle motor, gearing, clutch/disconnect, manual override and moving- or static-lever feedback. Autoflight and engine-control laws remain outside the module.",
    regulatoryIds: ["forward_lever", "engine_grouping", "retention_layout"],
    patentTags: ["moving_lever", "motor_drive", "manual_override", "friction_clutch", "virtual_detent", "target_setting", "dynamic_position", "haptic_feedback"],
    needTags: ["autothrottle_status", "mode_awareness", "manual_override", "persistent_status", "thrust_target_display"],
    preserve_zh: ["人工最终操纵权和主推力连续行程不得被驱动链阻断", "控制响应应确定及时，各发动机通道可独立/同时操纵", "失电或脱开后不得留下隐蔽驱动力或杆位漂移"],
    preserve_en: ["The drive train must not interrupt final manual authority or continuous primary travel", "Response remains definite and timely with individual/simultaneous engine control", "Power loss or disconnect leaves no hidden drive force or position creep"],
    exclude_zh: ["摩擦离合器连接电机和油门杆", "电机驱动手柄随动本身", "动态虚拟卡位和振动反馈本身"],
    exclude_en: ["A friction clutch between motor and lever", "Motor-driven moving levers by themselves", "Dynamic virtual detents or vibration feedback by themselves"],
    opportunities_zh: ["能量消失即开放人工主路径的失效开放传动盒", "自动指令与真实推力不一致时才出现的机械差分提示", "静态手柄中不依赖屏幕的自动化权威呈现"],
    opportunities_en: ["A fail-open transmission module that clears the manual path when energy disappears", "A mechanical difference cue appearing only when auto command and achieved thrust disagree", "Screen-independent presentation of automation authority with static levers"],
    mature_zh: "电机、齿轮、扭矩限制器、离合器和回位弹簧", mature_en: "motors, gears, torque limiters, clutches and return springs",
    mechanism_zh: "创新重点是自动权威如何接入、退出并被机组感知，尤其是故障时的能量和信息路径。",
    mechanism_en: "The invention should change how automatic authority enters, leaves and becomes perceptible—especially its energy and information paths after failure.",
    nodes_zh: ["自动指令", "失效开放耦合", "人工主路径", "权威反馈"], nodes_en: ["Auto command", "Fail-open coupling", "Manual path", "Authority feedback"],
    market_zh: "新研自动油门、飞控升级、训练/人因验证和技术许可", market_en: "New autothrottle systems, autoflight upgrades, training/human-factors validation and licensing",
    marketScore: 94, certBase: 76,
    affinity: {passive_state_morphing:92,directional_impedance:76,grip_travel_transform:54,intent_vector_gate:72,differential_truth_flag:98,fail_open_module:100,reverse_permission_token:52,grip_release_memory:78}
  }
];

const JOINT_DESIGN_VARIANTS = [
  {
    id: "interface_isolation",
    name_zh: "接口隔离型", name_en: "Interface-isolated architecture",
    focus_zh: "把新功能限制在所选模块与相邻模块的单一接口层，通过可拆换的中间件改变信息或力的传递关系，尽量不修改主载荷路径。",
    focus_en: "Confine the new function to one interface between the selected module and its neighbor, using a replaceable intermediary to change information or force transfer without altering the primary load path.",
    effect_zh: "改动边界明确、样机快，便于先证明单一技术效果和接口兼容性。",
    effect_en: "Creates a clear change boundary and fast prototype path for proving one technical effect and interface compatibility.",
    architecture_zh: "既有模块 → 可拆换创新接口 → 原有输出通道",
    architecture_en: "Existing module → replaceable inventive interface → existing output path",
    reuse_zh: "旧技术作为接口支承、限位和失效旁路使用", reuse_en: "Known technology serves as interface support, stops and a failure bypass",
    market_zh: "适合台架验证、模拟器和新研型号早期供应商联合演示", market_en: "Suited to bench validation, simulators and early supplier demonstrations for new aircraft",
    adjustments: {problem:1, patentDistance:3, regulation:4, effect:0, prototype:6, market:1, total:3}
  },
  {
    id: "diverse_dual_path",
    name_zh: "异构双路径型", name_en: "Diverse dual-path architecture",
    focus_zh: "用两个原理不同的局部路径分别保存操纵意图与实际状态，只在两者一致时输出许可，不以简单复制同一传感器或同一锁为冗余。",
    focus_en: "Use two locally diverse paths to retain commanded intent and actual state, producing permission only when they agree rather than duplicating one sensor or lock.",
    effect_zh: "可提高单点故障可检测性并形成明确的差异诊断，但需要更多符合性和故障组合验证。",
    effect_en: "Improves single-failure detectability and disagreement diagnosis, at the cost of additional compliance and fault-combination evidence.",
    architecture_zh: "意图路径 A + 状态路径 B → 一致性判定 → 安全输出",
    architecture_en: "Intent path A + state path B → agreement test → safe output",
    reuse_zh: "旧技术分别承担两个异构通道的基准和比较输入", reuse_en: "Known technology supplies the datum and comparison input for two diverse paths",
    market_zh: "适合高安全等级新研系统和关键互锁/自动油门功能", market_en: "Suited to safety-critical new systems and key interlock/autothrottle functions",
    adjustments: {problem:3, patentDistance:2, regulation:2, effect:6, prototype:-4, market:3, total:2}
  },
  {
    id: "fail_explicit_lru",
    name_zh: "失效显露模块型", name_en: "Failure-explicit replaceable module",
    focus_zh: "把创新机构封装为可更换功能盒，正常时参与传力或状态编码，失电、卡滞或拆除时自动开放基础人工路径并留下可见/可触的失效形态。",
    focus_en: "Package the invention as a replaceable functional unit that participates in force or state encoding normally, but clears the baseline manual path and leaves a visible/tactile failure state after power loss, seizure or removal.",
    effect_zh: "兼顾维修性、故障定位和人工最终操纵权，适合形成装置、系统和维护方法多层权利要求。",
    effect_en: "Combines maintainability, fault localization and final manual authority, supporting device, system and maintenance-method claim layers.",
    architecture_zh: "基础人工路径 ∥ 失效显露功能盒 → 可测试输出",
    architecture_en: "Baseline manual path ∥ failure-explicit unit → testable output",
    reuse_zh: "旧技术作为失效回退、快拆定位和地面测试接口使用", reuse_en: "Known technology serves as failure fallback, keyed quick release and ground-test interface",
    market_zh: "适合可维护 LRU、新研油门台和维修训练设备", market_en: "Suited to maintainable LRUs, new throttle quadrants and maintenance-training equipment",
    adjustments: {problem:2, patentDistance:4, regulation:5, effect:4, prototype:1, market:5, total:4}
  }
];

const state = {
  lang: localStorage.getItem("throttle-atlas-lang") || "zh",
  models: [],
  sources: [],
  stats: null,
  patentModule: localStorage.getItem("throttle-patent-module") || "thrust_levers",
  moduleConstraints: [],
  moduleConstraintId: "",
  excludedPatternCount: 0,
  residualInnovations: [],
  selectedInnovationPattern: localStorage.getItem("throttle-innovation-pattern") || "",
  components: [],
  constraints: [],
  selectedComponent: "forward_lever",
  designOptions: [],
  patents: [],
  pilotNeeds: [],
  inventionPatterns: [],
  generatedConcepts: [],
  inventorProblem: "need-mode-awareness",
  inventorContradiction: "clear_without_overload",
  inventorChallenge: "",
  selectedConceptId: "",
  adoptedConcept: null,
  designGoal: "safety",
  designSelections: {
    main_lever: "main-fixed-detent",
    reverse: "reverse-separate",
    detent: "detent-mechanical",
    automation_feedback: "feedback-display",
    engine_group: "group-split",
    action_control: "action-toga-guard"
  },
  view: "split",
  filter: "all"
};

const DESIGN_SLOT_ORDER = ["main_lever", "reverse", "detent", "automation_feedback", "engine_group", "action_control"];
const INVENTOR_CONTRADICTIONS = [
  {
    id: "clear_without_overload",
    zh: "状态必须更明确，但不能增加视觉/听觉负担",
    en: "State must be clearer without adding visual or aural load",
    tags: ["mode_awareness", "persistent_status"]
  },
  {
    id: "guard_without_delay",
    zh: "必须防误触，但不能延误紧急操作",
    en: "Prevent inadvertent action without delaying emergency use",
    tags: ["action_slip", "toga_guard", "distinct_action"]
  },
  {
    id: "feedback_without_motion",
    zh: "必须感知自动化动作，但不能依赖手柄随动",
    en: "Expose automation without relying on lever backdrive",
    tags: ["autothrottle_status", "tactile_differentiation"]
  },
  {
    id: "adapt_without_looseness",
    zh: "必须适应不同身高，但不能降低刚度或标定稳定性",
    en: "Adapt to pilot stature without losing stiffness or calibration",
    tags: ["adjustable_reach", "ergonomics", "full_travel"]
  },
  {
    id: "intelligence_without_authority_loss",
    zh: "必须增加智能防护，但不能削弱飞行员最终操纵权",
    en: "Add intelligent protection without reducing final pilot authority",
    tags: ["manual_override", "phase_awareness", "shutdown_safety"]
  },
  {
    id: "modular_without_failure",
    zh: "必须模块化维护，但不能把新故障带入主载荷路径",
    en: "Enable modular maintenance without adding failure to the primary load path",
    tags: ["modular_channel", "maintenance", "manual_override"]
  }
];

const EMBODIMENT_BLUEPRINTS = {
  passive_state_morphing: {
    name_zh: "三瓣式机械状态环", name_en: "Three-segment mechanical state ring",
    summary_zh: "在推力握把根部增加三片可径向伸缩的触觉瓣片。瓣片不显示一般状态，只把“自动推力接通、断开、失能”分别转换为齐平、凸起和故障纹理三种可触几何形态。",
    summary_en: "Add three radially movable tactile segments at the grip root. They do not display general status; they convert autothrottle engaged, disengaged and unavailable into flush, raised and fault-textured geometries.",
    parts_zh: ["A｜握把根部三瓣状态环", "B｜与自动推力离合状态联动的独立随动索", "C｜使瓣片径向伸缩的锥形滑套", "D｜断电后把滑套推入故障位置的偏置弹簧"],
    parts_en: ["A | Three-segment state ring at the grip root", "B | Independent follower cable linked to autothrottle-clutch state", "C | Tapered sleeve moving the segments radially", "D | Bias spring driving the sleeve to the fault position after power loss"],
    sequence_zh: ["自动推力接通：随动索拉住滑套，三片瓣片与握把齐平。", "自动推力断开：滑套移动第一行程，瓣片径向凸起，手不离杆即可感知。", "系统失能或随动链断开：弹簧推动滑套进入第二行程，露出带横纹的故障边。", "飞行员操纵主杆时，状态环不参与主杆载荷传递，卡滞也不限制杆位。"],
    sequence_en: ["Autothrottle engaged: the follower holds the sleeve and all segments remain flush.", "Autothrottle disengaged: the sleeve enters its first stroke and the segments rise for eyes-free recognition.", "System unavailable or follower broken: the spring drives a second stroke and exposes a cross-ribbed fault edge.", "The ring remains outside the primary load path, so a jam cannot restrict lever travel."],
    baseline_zh: "常见路径是在手柄或显示器上增加灯光、文字、声音或振动；状态信息仍依赖观察或电子提示。",
    baseline_en: "A common path adds lights, text, audio or vibration to the handle or display, leaving recognition dependent on visual or electronic annunciation.",
    delta_zh: "本构想把离合器真实机械状态直接变成握把几何形态，并用第二行程专门编码失能；信息载体、失效表现和主载荷隔离关系均发生改变。",
    delta_en: "This concept converts true clutch state directly into grip geometry and reserves a second stroke for unavailability, changing the information carrier, failure presentation and load-path relationship.",
    claim_hook_zh: "重点保护“独立状态随动件—两级锥形滑套—三瓣触觉环—失能偏置弹簧”的空间关系，以及三种状态与三种几何形态的一一对应。",
    claim_hook_en: "Focus claims on the spatial relationship of an independent state follower, two-stage tapered sleeve, three-segment tactile ring and fail-state bias spring, plus the one-to-one mapping of three states to three geometries."
  },
  differential_truth_flag: {
    name_zh: "三输入差分弹出旗", name_en: "Three-input differential pop-up flag",
    summary_zh: "在油门台基座设置一枚平时完全隐藏的机械旗，同时比较杆位意图、自动推力指令和发动机实际响应；只有三者超过时间—幅值包线时，旗标才弹出并指出差异方向。",
    summary_en: "Place a normally hidden mechanical flag in the quadrant base. It compares lever intent, autothrottle command and actual engine response, appearing only when their mismatch exceeds a time–magnitude envelope and indicating the mismatch direction.",
    parts_zh: ["A｜杆位双通道角度输入", "B｜自动推力目标指令输入", "C｜发动机 N1/EPR 实际响应输入", "D｜独立差分比较器与左右方向弹出旗"],
    parts_en: ["A | Dual-channel lever-angle input", "B | Autothrottle target-command input", "C | Actual engine N1/EPR response input", "D | Independent differential comparator and directional pop-up flag"],
    sequence_zh: ["比较器分别形成“杆位—指令”和“指令—实效”两个差值。", "差值必须同时超过幅值门槛并持续超过确认时间，瞬态变化不触发。", "异常成立后，机械旗从基座边缘弹出；左/右边缘分别指示指令偏高或实效偏低。", "差值恢复并经机组确认后旗标复位；比较器不向发动机控制回路写入指令。"],
    sequence_en: ["The comparator forms lever-to-command and command-to-response differences.", "A difference must exceed both magnitude and confirmation-time thresholds; transients do not trigger.", "When confirmed, a mechanical flag emerges from the base, with left/right edges indicating command-high or response-low direction.", "The flag resets after recovery and crew acknowledgement; the comparator never writes to engine control."],
    baseline_zh: "常见方案持续显示多个模式或发动机参数，由飞行员自行判断三者是否一致。",
    baseline_en: "Common systems continuously display several modes or engine parameters and leave the crew to infer whether the three agree.",
    delta_zh: "本构想不增加持续信息量，而是建立一个与主控制器隔离的三输入真值判断，仅在“意图、指令、实效”失配时生成方向性物理提示。",
    delta_en: "The concept adds no continuous information; it creates an isolated three-input truth test that produces a directional physical cue only when intent, command and effect disagree.",
    claim_hook_zh: "重点保护两个差分量、时间—幅值联合包线、只读隔离比较器和仅在失配时显现的方向性机械旗之间的组合关系。",
    claim_hook_en: "Focus claims on the combination of two difference values, a joint time–magnitude envelope, a read-only isolated comparator and a directional mechanical flag visible only during mismatch."
  },
  intent_vector_gate: {
    name_zh: "J 形单手意图导轨", name_en: "J-path one-hand intent gate",
    summary_zh: "把 TO/GA 或类似高风险触发件安装在一条 J 形导轨中：拇指必须先横向内收，再连续向前推到底；直线碰撞或只按压不能闭合触点。",
    summary_en: "Mount TO/GA or a similar high-risk trigger in a J-shaped guide. The thumb must move inward and then continue forward to the end; a straight bump or simple press cannot close the contact.",
    parts_zh: ["A｜握把侧面的 J 形导向槽", "B｜带滚轮的拇指滑块", "C｜仅在导轨末端对准的双触点桥", "D｜允许单手回弹复位的扭簧"],
    parts_en: ["A | J-shaped guide slot on the grip side", "B | Thumb slider with a guide roller", "C | Dual-contact bridge aligned only at the path end", "D | Torsion spring providing one-hand return"],
    sequence_zh: ["拇指先把滑块横向内收，使滚轮进入导轨转角。", "不松手继续向前推，滑块沿第二段导轨移动。", "只有滚轮到达末端时双触点桥同时闭合并输出指令。", "松手后扭簧沿原路径复位；任何直线外力都停在第一段或槽壁。"],
    sequence_en: ["The thumb first moves the slider inward so its roller reaches the guide bend.", "Without release, the thumb continues forward along the second guide segment.", "Only at the path end does the dual-contact bridge close and output the command.", "On release, the torsion spring returns the slider; any straight external force stops against the first segment or slot wall."],
    baseline_zh: "常见防误触依靠护圈、较大按压力或两个分离动作，可能增加紧急操作时间。",
    baseline_en: "Common slip protection uses guards, higher press force or two separate actions, which can add emergency activation time.",
    delta_zh: "本构想用一个连续二维轨迹表达意图，既拒绝直线滑误，又不要求寻找第二按钮或完成两次离散确认。",
    delta_en: "The concept expresses intent through one continuous two-dimensional path, rejecting straight-line slips without a second button or two discrete confirmations.",
    claim_hook_zh: "重点保护 J 形连续导轨、末端才对准的双触点桥，以及“横向分量后连续主方向分量”作为唯一有效触发轨迹。",
    claim_hook_en: "Focus claims on the continuous J-shaped guide, dual-contact bridge aligned only at the end and the inward-then-forward trajectory as the only valid actuation path."
  },
  directional_impedance: {
    name_zh: "首段单向凸轮阻抗器", name_en: "Initial-stroke one-way cam impedance",
    summary_zh: "在主推力轴旁增加一个只作用于错误方向首段行程的滚轮凸轮。关键飞行阶段向后收杆时先遇到力峰，向前推杆完全绕过；超过确定力后仍可人工收杆。",
    summary_en: "Add a roller cam beside the thrust shaft that acts only during the initial stroke in the hazardous direction. Retard motion meets a force peak during the critical phase, forward motion bypasses it, and a defined force still permits manual retard.",
    parts_zh: ["A｜固定在主轴侧面的非对称凸轮片", "B｜弹簧加载滚轮随动臂", "C｜由飞行阶段许可的旁路销", "D｜超过设定力即翻越的机械超控斜面"],
    parts_en: ["A | Asymmetric cam plate beside the main shaft", "B | Spring-loaded roller follower", "C | Flight-phase-permitted bypass pin", "D | Mechanical override ramp crossed above a defined force"],
    sequence_zh: ["正常阶段旁路销缩回，滚轮不接触凸轮，双向力感不变。", "关键阶段旁路销伸出，使滚轮落到凸轮错误方向入口。", "向后首段运动压缩弹簧形成短促力峰；向前运动沿低坡面通过。", "飞行员继续施加超过阈值的力时滚轮翻越斜面，不形成锁止。"],
    sequence_en: ["Outside the critical phase, the bypass pin retracts and the roller does not engage, preserving normal bidirectional feel.", "During the critical phase, the pin places the roller at the hazardous-direction cam entrance.", "Initial retard compresses the spring and creates a brief force peak; forward movement follows the low ramp.", "Continued force above the threshold carries the roller over the override ramp without locking the lever."],
    baseline_zh: "常见卡位在固定杆位产生双向阻力，或用主动电机持续施力。",
    baseline_en: "Common detents act bidirectionally at a fixed lever position, or an active motor continuously generates force.",
    delta_zh: "本构想不按目标杆位设卡位，而是按飞行阶段和动作方向，只在错误动作开始的一小段行程产生被动阻抗。",
    delta_en: "The concept creates no target-position detent; it uses phase and direction to create passive impedance only at the beginning of the hazardous action.",
    claim_hook_zh: "重点保护非对称凸轮、阶段旁路销、首段行程力峰和确定力超控斜面四者的关系，并明确前推方向不增加阻力。",
    claim_hook_en: "Focus claims on the relationship among the asymmetric cam, phase bypass pin, initial-stroke force peak and defined-force override ramp, with no added resistance in the forward direction."
  },
  grip_release_memory: {
    name_zh: "掌根退让式松手提示片", name_en: "Palm-release compliant reminder pad",
    summary_zh: "在握把掌根接触区设置一块可退让提示片。关键阶段开始时提示片向掌根弹出；只有飞行员真正松开握持，提示片才跨过复位缺口并回到齐平位置。",
    summary_en: "Place a compliant reminder pad at the palm-contact zone. It moves outward at the start of a critical phase and can cross its reset notch to become flush only after the pilot actually releases the grip.",
    parts_zh: ["A｜掌根接触区退让片", "B｜小行程压簧与导向柱", "C｜阶段触发释放闩", "D｜只在无握持载荷时通过的复位缺口"],
    parts_en: ["A | Compliant pad at the palm-contact zone", "B | Short-stroke compression spring and guide post", "C | Phase-triggered release latch", "D | Reset notch passable only without grip load"],
    sequence_zh: ["进入预定阶段时释放闩打开，压簧把提示片推出概念目标 2–3 mm。", "手仍紧握时掌根载荷压住导向柱，提示片保持有感位移。", "飞行员松手后载荷消失，提示片越过复位缺口并回到齐平位置。", "任何时候主动收放推力都可压过提示片，它不夹持或锁定主杆。"],
    sequence_en: ["At the selected phase, the latch releases and the spring moves the pad a conceptual 2–3 mm.", "While the hand remains clenched, palm load holds the guide post and the tactile displacement persists.", "After grip release, the load disappears and the pad crosses the reset notch to return flush.", "Intentional thrust movement can always override the pad; it never clamps or locks the lever."],
    baseline_zh: "常见提示要求飞行员看显示、听语音或记住程序动作，系统并不知道手是否真正松开。",
    baseline_en: "Common cues rely on display, audio or procedural memory and do not determine whether the hand was actually released.",
    delta_zh: "本构想把“松手”本身变成机械复位条件：提示是否消失直接证明握持载荷已经解除。",
    delta_en: "The concept makes actual hand release the mechanical reset condition; disappearance of the cue directly proves that grip load was removed.",
    claim_hook_zh: "重点保护掌根载荷控制复位的关系，而不是一般振动或弹性握把；提示片必须在有握持载荷时保持、无载荷时复位且不限制杆位。",
    claim_hook_en: "Focus claims on palm load governing reset, rather than a generic vibration or compliant grip: the pad persists under grip load, resets without load and never restricts lever position."
  },
  grip_travel_transform: {
    name_zh: "三档伸缩握把与行程重映射", name_en: "Three-position telescopic grip with travel remapping",
    summary_zh: "保持油门台基座和主轴不动，只让握把沿杆体在三个锁定位置伸缩；双通道位置编码识别握把档位，控制器把不同有效臂长统一映射为完整推力行程。",
    summary_en: "Keep the quadrant base and main shaft fixed while the grip telescopes to three locked positions. Dual-channel position coding identifies the grip position and remaps different effective arm lengths to full thrust travel.",
    parts_zh: ["A｜带三组锁孔的中空推力杆", "B｜可伸缩握把与双侧锁爪", "C｜两套错位磁编码片和霍尔通道", "D｜构型核对后启用的全行程重映射模块"],
    parts_en: ["A | Hollow thrust lever with three lock-hole sets", "B | Telescopic grip with dual locking pawls", "C | Two offset magnetic code strips and Hall channels", "D | Full-travel remapping enabled after configuration cross-check"],
    sequence_zh: ["飞行前按压双侧锁爪并把握把拉到短、中或长档。", "两套磁编码必须给出同一档位，控制器才接受构型。", "重映射模块根据有效臂长调整握把角度—主轴角度关系，发动机命令仍覆盖全量程。", "任一锁爪未到位或双通道不一致时保持原标定并给出维护提示。"],
    sequence_en: ["Before flight, press both locking pawls and move the grip to short, medium or long.", "Both magnetic channels must report the same position before the configuration is accepted.", "The remapping module adjusts grip-angle to shaft-angle relation for the effective arm length while preserving full engine-command range.", "If either pawl is not seated or channels disagree, retain the baseline calibration and issue a maintenance indication."],
    baseline_zh: "常见可达性方案移动整个油门台、支架或安装高度，改变结构载荷路径和座舱接口。",
    baseline_en: "Common reach solutions move the whole quadrant, bracket or mounting height, changing structural load paths and cockpit interfaces.",
    delta_zh: "本构想固定基座和主轴，仅改变抓握点、局部几何和传感映射，因此调节自由度与承载路径不同。",
    delta_en: "The concept fixes the base and shaft and changes only the grip point, local geometry and sensor mapping, producing a different adjustment degree of freedom and load path.",
    claim_hook_zh: "重点保护固定主轴、三档锁定握把、双通道构型编码和保持全发动机命令量程的重映射之间的闭环关系。",
    claim_hook_en: "Focus claims on the closed-loop relationship among a fixed shaft, three-position locking grip, dual-channel configuration coding and remapping that preserves full engine-command range."
  },
  fail_open_module: {
    name_zh: "侧挂式失效脱开功能匣", name_en: "Sidecar fail-disconnect function cassette",
    summary_zh: "主推力轴保持一根不中断的机械通道；触觉、联动或提示机构全部装进侧挂功能匣，只通过可释放滚轮接触主轴。功能匣断电、卡滞或拆除时自动脱开。",
    summary_en: "Keep one uninterrupted mechanical thrust shaft. Put haptic, coupling or cue functions in a sidecar cassette that touches the shaft only through a releasable roller. Power loss, jam or cassette removal automatically disconnects it.",
    parts_zh: ["A｜不中断的主推力轴和基线摩擦组件", "B｜侧挂可更换功能匣", "C｜功能匣输出滚轮与可剪切联接", "D｜失效检测后弹开滚轮的储能扭簧"],
    parts_en: ["A | Uninterrupted primary thrust shaft and baseline friction unit", "B | Replaceable sidecar function cassette", "C | Cassette output roller and releasable coupling", "D | Stored-energy torsion spring ejecting the roller after fault detection"],
    sequence_zh: ["正常时功能匣滚轮从侧面接触主轴凸轮，提供附加提示或阻抗。", "匣内监测器检测断电、内部行程超限或滚轮不回位。", "故障成立后可剪切联接释放，扭簧把整个滚轮臂弹离主轴。", "主轴继续依靠基线摩擦组件工作；拔出功能匣不需要拆开主轴。"],
    sequence_en: ["Normally, the cassette roller contacts a shaft cam from the side to add a cue or impedance.", "An internal monitor detects power loss, travel overrun or failure of the roller to return.", "After confirmation, the releasable coupling lets the torsion spring eject the roller arm from the shaft.", "The shaft continues on its baseline friction unit, and the cassette can be removed without opening the shaft."],
    baseline_zh: "常见集成模块把电机、齿轮、离合器和传感器串入主传动路径，单个卡滞可能改变操纵力。",
    baseline_en: "Common integrated modules place motors, gears, clutches and sensors in series with the main path, allowing one jam to alter control force.",
    delta_zh: "本构想让新增功能始终与主轴并联、侧向接触并以储能方式脱开，功能失效等同于功能消失，而不是主操纵受阻。",
    delta_en: "The new function remains parallel to the shaft, contacts it laterally and disconnects with stored energy, so failure removes the function rather than obstructing primary control.",
    claim_hook_zh: "重点保护不中断主轴、侧向滚轮耦合、故障释放联接和储能脱开方向之间的几何关系。",
    claim_hook_en: "Focus claims on the geometry among the uninterrupted shaft, lateral roller coupling, fault-release connection and stored-energy disconnect direction."
  },
  reverse_permission_token: {
    name_zh: "三钥对孔式反推许可梭", name_en: "Three-key aligned-aperture reverse shuttle",
    summary_zh: "在反推路径前设置一枚局部许可梭。飞行慢车到位、地面许可和机组抬起反推手柄分别移动三块带孔闸片；只有三个孔同时对正，许可梭才能穿过并接通反推。",
    summary_en: "Place a local permission shuttle before the reverse path. Flight-idle position, ground permission and crew lifting the reverse lever each move an apertured gate; only three aligned apertures let the shuttle pass and connect reverse.",
    parts_zh: ["A｜由飞行慢车止动驱动的第一孔板", "B｜由地面/批准包线驱动的第二孔板", "C｜由机组独立抬杆动作驱动的第三孔板", "D｜弹簧常闭的反推许可梭与位置监测触点"],
    parts_en: ["A | First apertured plate driven by the flight-idle stop", "B | Second plate driven by ground/approved-envelope state", "C | Third plate driven by the crew's independent reverse-lever lift", "D | Spring-closed reverse permission shuttle with position-monitor contact"],
    sequence_zh: ["正推区内第一孔板未对正，许可梭被机械挡住。", "到达飞行慢车后第一孔对正；地面许可使第二孔对正。", "机组抬起反推手柄后第三孔对正，梭体才可横向穿过三孔接通反推路径。", "任一许可消失，相关孔板在弹簧作用下错开并把梭体推回断开位。"],
    sequence_en: ["In forward thrust, the first aperture is misaligned and mechanically blocks the shuttle.", "At flight idle, the first aperture aligns; ground permission aligns the second.", "Lifting the reverse lever aligns the third, allowing the shuttle to cross all three apertures and connect reverse.", "Loss of any permission spring-misaligns its plate and returns the shuttle to disconnect."],
    baseline_zh: "常见反推联锁依赖一个软件许可位、单一电磁锁或一个可超控开关。",
    baseline_en: "Common reverse interlocks depend on one software permission bit, one solenoid lock or one overrideable switch.",
    delta_zh: "本构想把三个独立事实分别保存为局部机械孔位，许可不是逻辑计算结果，而是三个物理通道同时对孔形成的瞬时结构状态。",
    delta_en: "The concept stores three independent facts as local mechanical aperture positions; permission is not merely a logic result but a temporary structural state formed by three aligned physical channels.",
    claim_hook_zh: "重点保护三块孔板由不同事实独立驱动、只在三孔同时对正时梭体穿过，以及任一许可消失即弹簧错孔断开的关系。",
    claim_hook_en: "Focus claims on three independently driven apertured plates, shuttle passage only during simultaneous alignment and spring misalignment after loss of any permission."
  }
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const t = key => I18N[state.lang][key] || key;
const modelText = (model, field) => model[`${field}_${state.lang}`];
const featureText = (model, key) => (model.features[key] || ["—", "—"])[state.lang === "zh" ? 0 : 1];
const localized = (item, field) => item?.[`${field}_${state.lang}`] || "";
const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[char]);

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const unit = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / (1024 ** unit)).toFixed(unit ? 1 : 0)} ${units[unit]}`;
}

function formatSyncTime(value) {
  if (!value) return t("archive_pending");
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(state.lang === "zh" ? "zh-CN" : "en-GB", {
    month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit"
  });
}

function renderArchiveStats() {
  const stats = state.stats;
  if (!stats) return;
  $("#archive-source-count").textContent = `${stats.archived_sources} / ${stats.sources}`;
  $("#archive-chunk-count").textContent = stats.archive_chunks;
  $("#archive-size").textContent = formatBytes(stats.archive_bytes);
  $("#archive-sync-time").textContent = formatSyncTime(stats.archive_last_sync);
  const status = $("#archive-state");
  const ready = stats.archived_sources > 0;
  status.textContent = ready
    ? `${String(stats.archive_run_status || "ready").toUpperCase()}${stats.archive_failed ? ` · ${stats.archive_failed} ${t("archive_failed")}` : ""}`
    : t("archive_pending").toUpperCase();
  status.classList.toggle("has-errors", Boolean(stats.archive_failed));
}

function applyLanguage() {
  document.body.classList.toggle("lang-en", state.lang === "en");
  document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
  $$("[data-i18n]").forEach(el => el.textContent = t(el.dataset.i18n));
  $$("[data-i18n-placeholder]").forEach(el => el.placeholder = t(el.dataset.i18nPlaceholder));
  $$("[data-i18n-alt]").forEach(el => el.alt = t(el.dataset.i18nAlt));
  localStorage.setItem("throttle-atlas-lang", state.lang);
  if (state.models.length) {
    renderModelCards();
    populateSelects(true);
    updateComparison();
    updateCanvasLabels();
  }
  if (state.sources.length) renderSources();
  if (state.stats) renderArchiveStats();
  if (state.components.length) {
    renderComponents();
    renderRegulations();
  }
  if (state.designOptions.length) renderDesignStudio();
}

function modelById(id) {
  return state.models.find(m => m.id === id);
}

function optionLabel(model) {
  return `${modelText(model, "name")} · ${modelText(model, "maker")}`;
}

function populateSelect(select, selectedId) {
  const previous = selectedId || select.value;
  select.innerHTML = state.models.map(m => `<option value="${m.id}">${optionLabel(m)}</option>`).join("");
  if (state.models.some(m => m.id === previous)) select.value = previous;
}

function populateSelects(preserve = false) {
  const defaults = {
    "model-a": "a320", "model-b": "f16c",
    "function-a": "a320", "function-b": "f16c"
  };
  ["model-a", "model-b", "function-a", "function-b"].forEach(id => {
    const select = $(`#${id}`);
    populateSelect(select, preserve ? select.value : defaults[id]);
  });
}

function silhouette(model) {
  const count = model.geometry.levers;
  const levers = count === 1
    ? `<i class="mini-lever one"></i>`
    : `<i class="mini-lever left"></i><i class="mini-lever right"></i>`;
  return `<div class="model-silhouette"><span class="mini-base"></span>${levers}</div>`;
}

function renderModelCards() {
  const models = state.filter === "all" ? state.models : state.models.filter(m => m.category === state.filter);
  $("#model-grid").innerHTML = models.map((m, index) => {
    const limited = m.confidence === "limited";
    return `<article class="model-card" data-id="${m.id}">
      <div class="model-card-head">
        <span>${String(index + 1).padStart(2, "0")} · ${m.family.toUpperCase()}</span>
        <div class="confidence ${limited ? "limited" : ""}"><i></i>${limited ? t("limited") : t("high")}</div>
      </div>
      ${silhouette(m)}
      <h3>${modelText(m, "name")}</h3>
      <div class="maker">${modelText(m, "maker")} · ${m.category === "commercial" ? t("commercial_label") : t("military_label")}</div>
      <p>${modelText(m, "short")}</p>
      <div class="model-card-actions">
        <button type="button" data-slot="a">${t("select_a")}</button>
        <button type="button" data-slot="b">${t("select_b")}</button>
      </div>
    </article>`;
  }).join("");
  $$(".model-card-actions button").forEach(button => button.addEventListener("click", () => {
    const id = button.closest(".model-card").dataset.id;
    const slot = button.dataset.slot;
    $(`#model-${slot}`).value = id;
    $(`#function-${slot}`).value = id;
    updateAllComparators();
    $("#visual").scrollIntoView({behavior: "smooth"});
  }));
}

function updateCanvasLabels() {
  const a = modelById($("#model-a").value);
  const b = modelById($("#model-b").value);
  if (!a || !b) return;
  $("#canvas-name-a").textContent = modelText(a, "name");
  $("#canvas-name-b").textContent = modelText(b, "name");
  renderer?.setModels(a, b);
}

function updateComparison() {
  const a = modelById($("#function-a").value);
  const b = modelById($("#function-b").value);
  if (!a || !b) return;
  $("#function-name-a").textContent = modelText(a, "name");
  $("#function-name-b").textContent = modelText(b, "name");
  $("#comparison-rows").innerHTML = FEATURE_ROWS.map(([key, labelKey]) => {
    const av = featureText(a, key);
    const bv = featureText(b, key);
    const different = av.toLowerCase() !== bv.toLowerCase();
    return `<div class="comparison-row ${different ? "different" : ""}" role="row">
      <div role="cell">${t(labelKey)}</div><div role="cell">${av}</div><div role="cell">${bv}</div>
    </div>`;
  }).join("");
}

function updateAllComparators() {
  updateCanvasLabels();
  updateComparison();
}

async function runSearch(query) {
  const trimmed = query.trim();
  if (!trimmed) return;
  $("#knowledge-query").value = trimmed;
  const container = $("#search-results");
  container.innerHTML = `<div class="empty-results">···</div>`;
  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(trimmed)}`);
    const data = await response.json();
    $("#result-count").textContent = data.results.length;
    if (!data.results.length) {
      container.innerHTML = `<div class="empty-results">${t("no_results")}</div>`;
      return;
    }
    container.innerHTML = data.results.map((r, index) => `<article class="result-card ${r.archive ? "archive-result" : ""}">
      <div class="result-card-head">
        <h3>${escapeHtml(state.lang === "zh" ? r.title_zh : r.title_en)}</h3>
        <span class="source-badge">${escapeHtml(r.organization.toUpperCase())} · ${escapeHtml(r.quality.toUpperCase())}${r.archive ? ` · ${t("archive_local").toUpperCase()}` : ""}</span>
      </div>
      <p>${escapeHtml(state.lang === "zh" ? r.body_zh : r.body_en)}</p>
      <div class="result-meta">
        <span>${String(index + 1).padStart(2, "0")} · ${t("match")} ${r.score} · source_id:${escapeHtml(r.source_id)}</span>
        <a href="${escapeHtml(r.url)}" target="_blank" rel="noreferrer">${t("source_link")} ↗</a>
      </div>
    </article>`).join("");
  } catch (error) {
    container.innerHTML = `<div class="empty-results">${error.message}</div>`;
  }
}

function renderSources() {
  $("#source-list").innerHTML = state.sources.map(s => `<article class="source-item">
    <small>${s.organization.toUpperCase()} · ${s.kind.toUpperCase()} · ${s.quality.toUpperCase()}${s.archive_status === "ok" ? ` · ${t("archive_local").toUpperCase()}` : ""}</small>
    <h4>${state.lang === "zh" ? s.title_zh : s.title_en}</h4>
    <p>${state.lang === "zh" ? s.note_zh : s.note_en}</p>
    <a href="${s.url}" target="_blank" rel="noreferrer">${t("source_open")} ↗</a>
  </article>`).join("");
}

function selectedComponent() {
  return state.components.find(component => component.id === state.selectedComponent);
}

function renderComponents() {
  $("#component-count").textContent = String(state.components.length).padStart(2, "0");
  $("#component-list").innerHTML = state.components.map(component => `
    <button class="component-button ${component.id === state.selectedComponent ? "active" : ""}" type="button" data-component="${component.id}">
      <b>${component.icon}</b>
      <span><strong>${localized(component, "name")}</strong><small>${localized(component, "description")}</small></span>
      <i>→</i>
    </button>`).join("");
  $$(".component-button").forEach(button => button.addEventListener("click", async () => {
    state.selectedComponent = button.dataset.component;
    renderComponents();
    await loadConstraints(state.selectedComponent);
  }));
  const component = selectedComponent();
  if (!component) return;
  $("#selected-component-icon").textContent = component.icon;
  $("#selected-component-name").textContent = localized(component, "name");
  $("#selected-component-description").textContent = localized(component, "description");
}

async function loadConstraints(componentId) {
  $("#regulation-results").innerHTML = `<div class="regulation-loading">LOADING · ${state.lang === "zh" ? "正在载入法规条款" : "Loading official provisions"}</div>`;
  try {
    const response = await fetch(`/api/constraints?component=${encodeURIComponent(componentId)}`);
    const data = await response.json();
    if (componentId !== state.selectedComponent) return;
    state.constraints = data.constraints;
    renderRegulations();
  } catch (error) {
    $("#regulation-results").innerHTML = `<div class="regulation-loading">${error.message}</div>`;
  }
}

function renderRegulations() {
  const component = selectedComponent();
  if (component) {
    $("#selected-component-icon").textContent = component.icon;
    $("#selected-component-name").textContent = localized(component, "name");
    $("#selected-component-description").textContent = localized(component, "description");
  }
  $("#constraint-count").textContent = String(state.constraints.length).padStart(2, "0");
  if (!state.constraints.length) return;
  $("#regulation-results").innerHTML = state.constraints.map(item => `
    <article class="regulation-card" data-authority="${item.authority}">
      <div class="authority-head">
        <div>
          <strong>${item.authority}</strong>
          <span><h4>${item.authority}</h4><small>${localized(item, "applicability")}</small></span>
        </div>
        <span>${localized(item, "status")}</span>
      </div>
      <div class="rule-ref">${item.rule_ref}</div>
      <div class="regulation-block requirement">
        <span><i></i>${t("legal_requirement")}</span>
        <p>${localized(item, "requirement")}</p>
      </div>
      <div class="regulation-block interpretation">
        <span><i></i>${t("engineering_reading")}</span>
        <p>${localized(item, "interpretation")}</p>
      </div>
      <div class="authority-difference">
        <span>${t("authority_difference")}</span>
        <p>${localized(item, "difference")}</p>
      </div>
      <div class="regulation-source">
        <span>${state.lang === "zh" ? item.source_title_zh : item.source_title_en}</span>
        <a href="${item.url}" target="_blank" rel="noreferrer">${t("official_source")} ↗</a>
      </div>
    </article>`).join("");
}

function selectedDesignOptions() {
  return DESIGN_SLOT_ORDER.map(slotId => state.designOptions.find(option => option.id === state.designSelections[slotId])).filter(Boolean);
}

function selectedInventorNeed() {
  return state.pilotNeeds.find(need => need.id === state.inventorProblem) || state.pilotNeeds[0];
}

function selectedInventorContradiction() {
  return INVENTOR_CONTRADICTIONS.find(item => item.id === state.inventorContradiction) || INVENTOR_CONTRADICTIONS[0];
}

function selectedPatentModule() {
  return PATENT_MODULES.find(module => module.id === state.patentModule) || PATENT_MODULES[0];
}

function clampScore(value, minimum = 0, maximum = 100) {
  return Math.max(minimum, Math.min(maximum, Math.round(value)));
}

function getModulePatentMatches(module = selectedPatentModule()) {
  const tags = new Set(module.patentTags);
  return state.patents.map(patent => {
    const matched = patent.tags.filter(tag => tags.has(tag));
    const moduleScore = patent.tags.length ? Math.round(matched.length / patent.tags.length * 100) : 0;
    return {...patent, matched, moduleScore};
  }).filter(patent => patent.moduleScore > 0)
    .sort((a, b) => b.moduleScore - a.moduleScore || b.priority_date.localeCompare(a.priority_date));
}

function chooseRecommendedNeed(module = selectedPatentModule()) {
  const target = new Set(module.needTags);
  const ranked = state.pilotNeeds.map(need => ({
    need,
    hits: need.tags.filter(tag => target.has(tag)).length
  })).sort((a, b) => b.hits - a.hits || b.need.severity - a.need.severity || b.need.evidence_count - a.need.evidence_count);
  if (ranked[0]) state.inventorProblem = ranked[0].need.id;
}

function renderPatentModules() {
  const module = selectedPatentModule();
  $("#patent-module-list").innerHTML = PATENT_MODULES.map(item => `
    <button type="button" class="patent-module-card ${item.id === module.id ? "active" : ""}" data-module="${item.id}">
      <span>${item.code}</span>
      <b>${localized(item, "name")}</b>
      <i>→</i>
    </button>`).join("");
  $("#module-scope-note").innerHTML = `<span>${module.code} · CLAIM SCOPE</span><p>${localized(module, "scope")}</p>`;
  $$(".patent-module-card").forEach(button => {
    button.onclick = async () => {
      if (button.dataset.module === state.patentModule) return;
      state.patentModule = button.dataset.module;
      localStorage.setItem("throttle-patent-module", state.patentModule);
      state.generatedConcepts = [];
      state.residualInnovations = [];
      state.selectedConceptId = "";
      state.adoptedConcept = null;
      state.moduleConstraints = [];
      state.moduleConstraintId = "";
      chooseRecommendedNeed();
      renderPatentModules();
      renderInventorControls();
      await loadPatentModuleContext(true);
    };
  });
}

function renderModuleBoundaries() {
  const module = selectedPatentModule();
  const groups = ["FAA", "EASA", "CAAC"].map(authority => ({
    authority,
    items: state.moduleConstraints.filter(item => item.authority === authority)
  })).filter(group => group.items.length);
  $("#module-regulation-count").textContent = String(state.moduleConstraints.length).padStart(2, "0");
  $("#module-regulation-boundaries").innerHTML = groups.length
    ? groups.map(group => {
      const rules = [...new Set(group.items.map(item => item.rule_ref))].join(" · ");
      const requirement = group.items.map(item => localized(item, "requirement")).filter(Boolean).slice(0, 2).join(" ");
      const source = group.items[0];
      return `<article>
        <div><b>${group.authority}</b><a href="${source.url}" target="_blank" rel="noreferrer">↗</a></div>
        <span>${rules}</span><p>${requirement}</p>
      </article>`;
    }).join("")
    : `<p class="module-loading">${t("module_loading")}</p>`;

  const patentMatches = getModulePatentMatches(module);
  $("#module-patent-count").textContent = String(patentMatches.length).padStart(2, "0");
  $("#module-patent-boundaries").innerHTML = patentMatches.slice(0, 3).map(patent => `
    <article>
      <div><b>${patent.publication_no}</b><a href="${patent.url}" target="_blank" rel="noreferrer">↗</a></div>
      <span>${patent.moduleScore}% ${t("overlap")} · ${patent.matched.join(" / ")}</span>
      <p>${localized(patent, "claim")}</p>
    </article>`).join("") || `<p>${t("no_direct_patent")}</p>`;
}

function derivedContradictionForModule(module = selectedPatentModule()) {
  const target = new Set(module.needTags);
  const ranked = INVENTOR_CONTRADICTIONS.map(item => ({
    item,
    hits: item.tags.filter(tag => target.has(tag)).length
  })).sort((a, b) => b.hits - a.hits);
  return ranked[0]?.item || INVENTOR_CONTRADICTIONS[0];
}

function renderResidualInnovations() {
  $("#module-residual-count").textContent = String(state.residualInnovations.length).padStart(2, "0");
  $("#residual-innovation-list").innerHTML = state.residualInnovations.map((item, index) => {
    const pattern = item.pattern;
    const ranking = item.ranking;
    const active = pattern.id === state.selectedInnovationPattern;
    return `<button type="button" class="residual-innovation-card ${active ? "active" : ""}" data-pattern="${pattern.id}">
      <div><span>${String(index + 1).padStart(2, "0")}</span><b>${t("total_score")} ${ranking.total}</b></div>
      <h5>${localized(pattern, "name")}</h5>
      <p>${localized(pattern, "principle")}</p>
      <dl>
        <div><dt>${t("score_cert")}</dt><dd>${ranking.regulation}</dd></div>
        <div><dt>${t("score_novelty")}</dt><dd>${ranking.patentDistance}</dd></div>
        <div><dt>${t("score_proto")}</dt><dd>${ranking.prototype}</dd></div>
        <div><dt>${t("score_market")}</dt><dd>${ranking.market}</dd></div>
      </dl>
      <small>${state.lang === "zh" ? ranking.reason_zh : ranking.reason_en}</small>
      <i>${active ? (state.lang === "zh" ? "已选择" : "SELECTED") : (state.lang === "zh" ? "选择此创新点 →" : "SELECT →")}</i>
    </button>`;
  }).join("");
  $("#residual-exclusion-note").textContent = state.lang === "zh"
    ? `已排除 ${state.excludedPatternCount} 条模块适配不足、法规适配不足或专利距离过近的路线。排序仅用于概念筛选，不构成专利性结论。`
    : `${state.excludedPatternCount} routes were excluded for weak module fit, weak regulatory fit or insufficient patent distance. Ranking supports concept screening only and is not a patentability opinion.`;
  $$(".residual-innovation-card").forEach(button => {
    button.onclick = () => {
      state.selectedInnovationPattern = button.dataset.pattern;
      localStorage.setItem("throttle-innovation-pattern", state.selectedInnovationPattern);
      renderResidualInnovations();
      updateInventorReasoning();
      generateConcepts();
    };
  });
}

function rankResidualInnovations() {
  const module = selectedPatentModule();
  const need = selectedInventorNeed();
  const contradiction = derivedContradictionForModule(module);
  state.inventorContradiction = contradiction.id;
  const patentMatches = getModulePatentMatches(module);
  const ranked = state.inventionPatterns.map(pattern => ({
    pattern,
    ranking: scorePatternForModule(pattern, module, need, contradiction, patentMatches)
  })).sort((a, b) => b.ranking.total - a.ranking.total || b.ranking.patentDistance - a.ranking.patentDistance);
  state.residualInnovations = ranked.filter(item =>
    item.ranking.affinity >= 60 &&
    item.ranking.regulation >= 50 &&
    item.ranking.patentDistance >= 50
  );
  if (state.residualInnovations.length < 3) state.residualInnovations = ranked.slice(0, 3);
  state.excludedPatternCount = state.inventionPatterns.length - state.residualInnovations.length;
  if (!state.residualInnovations.some(item => item.pattern.id === state.selectedInnovationPattern)) {
    state.selectedInnovationPattern = state.residualInnovations[0]?.pattern.id || "";
    if (state.selectedInnovationPattern) {
      localStorage.setItem("throttle-innovation-pattern", state.selectedInnovationPattern);
    }
  }
  renderResidualInnovations();
}

async function loadPatentModuleContext(force = false) {
  const module = selectedPatentModule();
  renderModuleBoundaries();
  if (!force && state.moduleConstraintId === module.id && state.moduleConstraints.length) {
    rankResidualInnovations();
    generateConcepts();
    return;
  }
  state.moduleConstraintId = "";
  state.moduleConstraints = [];
  renderModuleBoundaries();
  try {
    const responses = await Promise.all(module.regulatoryIds.map(id =>
      fetch(`/api/constraints?component=${encodeURIComponent(id)}`)
    ));
    const payloads = await Promise.all(responses.map(response => response.json()));
    const seen = new Set();
    state.moduleConstraints = payloads.flatMap(payload => payload.constraints).filter(item => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
    state.moduleConstraintId = module.id;
  } catch {
    state.moduleConstraints = [];
  }
  renderModuleBoundaries();
  rankResidualInnovations();
  generateConcepts();
}

function updateInventorReasoning() {
  const module = selectedPatentModule();
  const patents = getModulePatentMatches(module).slice(0, 2);
  const selected = state.residualInnovations.find(item => item.pattern.id === state.selectedInnovationPattern);
  const preserve = state.lang === "zh" ? module.preserve_zh : module.preserve_en;
  const exclude = state.lang === "zh" ? module.exclude_zh : module.exclude_en;
  $("#reason-module").textContent = `${localized(module, "name")}：${localized(module, "scope")}`;
  $("#reason-regulation").textContent = preserve.slice(0, 2).join(state.lang === "zh" ? "；" : "; ");
  $("#reason-patent").textContent = patents.length
    ? `${patents.map(item => item.publication_no).join(" / ")}：${exclude.slice(0, 2).join(state.lang === "zh" ? "；" : "; ")}`
    : exclude.slice(0, 2).join(state.lang === "zh" ? "；" : "; ");
  $("#reason-residual").textContent = selected
    ? `${localized(selected.pattern, "name")}：${localized(selected.pattern, "principle")}`
    : "—";
}

function expectedEffectForNeed(need) {
  const tags = new Set(need.tags);
  if (tags.has("mode_awareness") || tags.has("persistent_status")) {
    return {
      zh: "预期缩短自动推力状态识别时间，降低错误模式判断率，同时不增加持续视觉监控负担。",
      en: "Expected to shorten autothrottle-state recognition time and reduce mode misidentification without adding continuous visual-monitoring load."
    };
  }
  if (tags.has("action_slip") || tags.has("toga_guard")) {
    return {
      zh: "预期降低错误动作的启动概率，同时保持紧急操作时间和人工最终操纵权不劣化。",
      en: "Expected to reduce initiation of the wrong action while preserving emergency operation time and final manual authority."
    };
  }
  if (tags.has("adjustable_reach") || tags.has("ergonomics")) {
    return {
      zh: "预期提高不同身高与约束姿态下的全行程可达率，同时保持刚度、标定和双人观察条件。",
      en: "Expected to improve full-travel reach across statures and restrained postures while preserving stiffness, calibration and crew observability."
    };
  }
  if (tags.has("takeoff_confirm")) {
    return {
      zh: "预期提高未正确设置起飞推力的发现率，并减少对单一流程检查或单一显示通道的依赖。",
      en: "Expected to increase detection of incorrectly set takeoff thrust and reduce dependence on one procedural check or display channel."
    };
  }
  return {
    zh: "预期降低与该问题相关的操作差错，并保持主操纵功能、人工超控和失效安全不劣化。",
    en: "Expected to reduce task-related operating errors without degrading primary control, manual override or fail-safe behavior."
  };
}

function marketPlanForGoal(goal, difficulty) {
  const plans = {
    safety: {
      target_zh: "运输类飞机中央油门台安全增强、新研驾驶舱控制器及高保真验证平台",
      target_en: "Safety-enhanced center quadrants for transport aircraft, new cockpit controls and high-fidelity validation platforms",
      customer_zh: "飞机主制造商、驾驶舱控制/飞控供应商、适航人因与模拟验证机构",
      customer_en: "Aircraft OEMs, cockpit-control and flight-control suppliers, certification human-factors and simulation organizations"
    },
    ergonomics: {
      target_zh: "不同身高飞行员可达性改进、新研驾驶舱人机界面及模拟训练设备",
      target_en: "Stature-reach improvement, new cockpit HMI and simulation/training equipment",
      customer_zh: "飞机主制造商、驾驶舱内饰与控制器供应商、人因实验室和训练设备企业",
      customer_en: "Aircraft OEMs, cockpit-interior and control suppliers, human-factors laboratories and training-equipment firms"
    },
    automation: {
      target_zh: "自动推力状态透明化、新研飞控交互界面及自动化改装验证平台",
      target_en: "Autothrottle-state transparency, new autoflight interfaces and automation retrofit-validation platforms",
      customer_zh: "飞机主制造商、飞控/航电供应商、自动驾驶系统集成商和模拟验证机构",
      customer_en: "Aircraft OEMs, flight-control and avionics suppliers, autoflight integrators and simulation organizations"
    },
    maintenance: {
      target_zh: "可更换油门台功能模块、新研驾驶舱控制器及台架维护训练设备",
      target_en: "Replaceable quadrant-function modules, new cockpit controls and bench maintenance-training equipment",
      customer_zh: "飞机主制造商、控制器供应商、MRO 工程机构和训练设备企业",
      customer_en: "Aircraft OEMs, control suppliers, MRO engineering organizations and training-equipment firms"
    }
  };
  const selected = plans[goal] || plans.safety;
  const entryZh = difficulty >= 70
    ? "先做独立台架和高保真模拟器原型，完成人因与故障注入验证后，以供应商联合开发或技术许可进入新研型号。"
    : "先做可运行样机和对照试验，以人因数据证明效果，再与驾驶舱控制供应商联合进入新研型号；改装市场需另行评估审定成本。";
  const entryEn = difficulty >= 70
    ? "Begin with an isolated bench and high-fidelity simulator prototype, complete human-factors and failure-injection evidence, then enter new aircraft through supplier co-development or licensing."
    : "Build an operating prototype and controlled tests first, use human-factors evidence to prove the effect, then co-develop for a new aircraft with a cockpit-control supplier; retrofit certification cost needs separate assessment.";
  return {
    ...selected,
    entry_zh: entryZh,
    entry_en: entryEn,
    barrier_zh: "适航符合性、单点故障与耐久性证据、供应链集成成本、完整专利检索以及旧机改装的接口兼容性。",
    barrier_en: "Certification compliance, single-failure and durability evidence, supply-chain integration cost, full patent searching and interface compatibility for retrofit aircraft."
  };
}

function scorePatternForModule(pattern, module, need, contradiction, patentMatches) {
  const needTags = new Set([...need.tags, ...contradiction.tags]);
  const moduleTags = new Set(module.needTags);
  const knownPatentTags = new Set(patentMatches.flatMap(item => item.tags));
  const suitableHits = pattern.suitable_tags.filter(tag => needTags.has(tag) || moduleTags.has(tag)).length;
  const moduleNeedHits = need.tags.filter(tag => moduleTags.has(tag)).length;
  const avoidHits = pattern.avoid_tags.filter(tag => knownPatentTags.has(tag)).length;
  const riskHits = pattern.risk_tags.filter(tag => knownPatentTags.has(tag)).length;
  const affinity = module.affinity[pattern.id] || 45;
  const problem = clampScore(43 + suitableHits * 8 + moduleNeedHits * 7 + need.severity * 3 + affinity * .16, 30, 98);
  const patentDistance = clampScore(67 + avoidHits * 7 - riskHits * 12 + affinity * .12, 24, 96);
  const regulation = clampScore(module.certBase + affinity * .18 - pattern.difficulty * .28 - riskHits * 3, 28, 96);
  const effect = clampScore(49 + suitableHits * 9 + need.evidence_count * 2 + affinity * .18, 35, 97);
  const prototype = clampScore(105 - pattern.difficulty * .62 + affinity * .18, 30, 94);
  const market = clampScore(module.marketScore + moduleNeedHits * 3 - pattern.difficulty * .12, 40, 96);
  const total = clampScore(
    problem * .23 + regulation * .20 + patentDistance * .23 +
    effect * .17 + prototype * .07 + market * .10,
    0, 99
  );
  const hardConflict = regulation < 42 || patentDistance < 38 || affinity < 50;
  const reason_zh = `模块适配 ${affinity}/100；命中 ${suitableHits} 个问题/矛盾标签；绕开 ${avoidHits} 个已知专利特征，仍有 ${riskHits} 个高重合风险需要检索。`;
  const reason_en = `Module affinity ${affinity}/100; ${suitableHits} problem/contradiction tags matched; ${avoidHits} known patent features avoided, with ${riskHits} high-overlap risks still requiring search.`;
  return {total, problem, patentDistance, regulation, effect, prototype, market, affinity, suitableHits, avoidHits, riskHits, hardConflict, reason_zh, reason_en};
}

function adjustRankingForVariant(ranking, variant) {
  const adjusted = {...ranking};
  ["problem", "patentDistance", "regulation", "effect", "prototype", "market"].forEach(key => {
    adjusted[key] = clampScore(ranking[key] + (variant.adjustments[key] || 0), 0, 99);
  });
  adjusted.total = clampScore(ranking.total + (variant.adjustments.total || 0), 0, 99);
  adjusted.reason_zh = `${ranking.reason_zh} 联合架构采用“${variant.name_zh}”，评分已计入其验证与实施特征。`;
  adjusted.reason_en = `${ranking.reason_en} The joint design uses the ${variant.name_en}; its validation and implementation characteristics are included in the score.`;
  return adjusted;
}

function buildInventiveConcept(pattern, rank, context) {
  const {need, contradiction, selected, targetTags, patentTags, patentMatches, module, ranking, variant} = context;
  const adjustedRanking = adjustRankingForVariant(ranking, variant);
  const suitableHits = pattern.suitable_tags.filter(tag => targetTags.has(tag)).length;
  const avoidedHits = pattern.avoid_tags.filter(tag => patentTags.has(tag)).length;
  const riskHits = pattern.risk_tags.filter(tag => patentTags.has(tag)).length;
  const pilotValue = adjustedRanking.problem;
  const differenceOpportunity = adjustedRanking.patentDistance;
  const certificationDifficulty = Math.max(25, Math.min(95, pattern.difficulty));
  const prototypeFeasibility = adjustedRanking.prototype;
  const nearestPatents = patentMatches.filter(item => item.score > 0).slice(0, 2).map(item => item.publication_no);
  const customZh = state.inventorChallenge ? `；用户补充约束：${state.inventorChallenge}` : "";
  const customEn = state.inventorChallenge ? `; user constraint: ${state.inventorChallenge}` : "";
  const avoidanceZh = nearestPatents.length
    ? `以 ${nearestPatents.join("、")} 的高重合特征作为负约束，具体权利要求仍须进一步检索核对。`
    : "以当前专利库中的已知显示、振动、动态卡位和传动路径作为负约束，具体权利要求仍须进一步检索核对。";
  const avoidanceEn = nearestPatents.length
    ? `Treat the high-overlap features in ${nearestPatents.join(" and ")} as negative constraints; full claims still require further searching.`
    : "Treat known display, vibration, dynamic-detent and drive paths in the patent set as negative constraints; full claims still require further searching.";
  const effect = expectedEffectForNeed(need);
  const market = marketPlanForGoal(need.goals?.[0] || "safety", certificationDifficulty);
  market.target_zh = `${module.market_zh}；${variant.market_zh}；${market.target_zh}`;
  market.target_en = `${module.market_en}; ${variant.market_en}; ${market.target_en}`;
  market.entry_zh = `${variant.effect_zh} 市场进入建议：${market.entry_zh}`;
  market.entry_en = `${variant.effect_en} Market-entry recommendation: ${market.entry_en}`;
  const comparisonRows = patentMatches.slice(0, 3).map(patent => ({
    publication_no: patent.publication_no,
    score: patent.score,
    title_zh: patent.title_zh,
    title_en: patent.title_en,
    known_zh: patent.claim_zh,
    known_en: patent.claim_en,
    response_zh: patent.change_zh?.[0] || "扩大结构、控制原理和技术效果检索。",
    response_en: patent.change_en?.[0] || "Expand the search across structure, control principle and technical effect.",
    url: patent.url
  }));
  const mainLever = selected.find(item => item.slot_id === "main_lever") || selected[0];
  const stateOption = selected.find(item => item.slot_id === "automation_feedback") || selected[1];
  const safetyOption = selected.find(item => item.slot_id === "action_control") || selected.find(item => item.slot_id === "reverse") || selected[2];
  const serviceOption = selected.find(item => item.slot_id === "engine_group") || selected.find(item => item.slot_id === "detent") || selected[3];
  const reusedZh = selected.slice(0, 3).map(item => item.name_zh).join("、") || module.mature_zh;
  const reusedEn = selected.slice(0, 3).map(item => item.name_en).join(", ") || module.mature_en;
  const structureZh = `${variant.architecture_zh}；关键限定：${pattern.claim_zh.slice(0, 2).join(" + ")}`;
  const structureEn = `${variant.architecture_en}; key limitations: ${pattern.claim_en.slice(0, 2).join(" + ")}`;
  const embodiment = EMBODIMENT_BLUEPRINTS[pattern.id];
  const figureNodesZh = [module.nodes_zh[0], pattern.name_zh, variant.name_zh, module.nodes_zh[3]];
  const figureNodesEn = [module.nodes_en[0], pattern.name_en, variant.name_en, module.nodes_en[3]];
  const validationZh = [
    `对“${variant.name_zh}”执行接口断开、单点故障和人工超控试验，证明基础操纵路径不被阻断。`,
    ...pattern.validation_zh
  ];
  const validationEn = [
    `Run interface-disconnect, single-failure and manual-override tests on the ${variant.name_en} to prove that the baseline control path is not interrupted.`,
    ...pattern.validation_en
  ];

  return {
    id: `${module.id}-${need.id}-${pattern.id}-${variant.id}`,
    code: `${module.code} / SCHEME ${String(rank + 1).padStart(2, "0")}`,
    module_id: module.id,
    pattern_id: pattern.id,
    selected_innovation_id: pattern.id,
    selected_innovation_name_zh: pattern.name_zh,
    selected_innovation_name_en: pattern.name_en,
    variant_id: variant.id,
    variant,
    source_need_id: need.id,
    contradiction_id: contradiction.id,
    title_zh: `${module.name_zh} · ${variant.name_zh}`,
    title_en: `${module.name_en} · ${variant.name_en}`,
    problem_zh: `${module.name_zh}范围内：${need.problem_zh}${customZh}`,
    problem_en: `Within the ${module.name_en} scope: ${need.problem_en}${customEn}`,
    principle_zh: `所选创新点“${pattern.name_zh}”与${module.name_zh}联合：${pattern.principle_zh}`,
    principle_en: `Jointly apply the selected innovation point “${pattern.name_en}” to the ${module.name_en}: ${pattern.principle_en}`,
    mechanism_zh: `${variant.architecture_zh}。${variant.focus_zh} 具体机构基础为：${embodiment.summary_zh}`,
    mechanism_en: `${variant.architecture_en}. ${variant.focus_en} The concrete mechanism is based on: ${embodiment.summary_en}`,
    reuse_zh: `保留${reusedZh}等成熟构件，但使其在新架构中承担“${variant.reuse_zh}”的用途；不主张成熟构件本身为新。`,
    reuse_en: `Retain mature ${reusedEn}, but use them so that ${variant.reuse_en}; the mature elements alone are not asserted as new.`,
    core_zh: `核心不是把现有部件并排组合，而是用“${variant.name_zh}”把${pattern.name_zh}嵌入${module.name_zh}，形成“${variant.architecture_zh}”的限定关系。${embodiment.delta_zh}`,
    core_en: `The core is not a side-by-side aggregation. The ${variant.name_en} embeds the ${pattern.name_en} in the ${module.name_en} through the limited relationship “${variant.architecture_en}”. ${embodiment.delta_en}`,
    why_zh: `${pattern.why_zh}${variant.effect_zh} ${avoidanceZh}`,
    why_en: `${pattern.why_en} ${variant.effect_en} ${avoidanceEn}`,
    research: {
      source_organization: need.organization,
      source_title_zh: need.source_title_zh,
      source_title_en: need.source_title_en,
      source_url: need.url,
      severity: need.severity,
      evidence_count: need.evidence_count,
      comparisons: comparisonRows,
      gap_zh: `${need.opportunity_zh} 对于${module.name_zh}，法规要求保留“${module.preserve_zh[0]}”，专利负约束优先排除“${module.exclude_zh[0]}”。经筛选后选择“${pattern.name_zh}”，并用“${variant.name_zh}”解决剩余缺口：${module.opportunities_zh[0]}。`,
      gap_en: `${need.opportunity_en} For the ${module.name_en}, regulation preserves “${module.preserve_en[0]}”, while the patent filter excludes “${module.exclude_en[0]}”. After filtering, the ${pattern.name_en} is implemented through the ${variant.name_en} to address the residual gap: ${module.opportunities_en[0]}.`
    },
    effects: {
      structure_zh: structureZh,
      structure_en: structureEn,
      action_zh: `${pattern.principle_zh}；${variant.focus_zh}`,
      action_en: `${pattern.principle_en}; ${variant.focus_en}`,
      direct_zh: `${effect.zh} ${variant.effect_zh}`,
      direct_en: `${effect.en} ${variant.effect_en}`,
      metric_zh: pattern.validation_zh.slice(0, 2).join("；"),
      metric_en: pattern.validation_en.slice(0, 2).join("; ")
    },
    layout: {
      primary_zh: mainLever?.name_zh || module.nodes_zh[0],
      primary_en: mainLever?.name_en || module.nodes_en[0],
      state_zh: `${pattern.name_zh}状态区`,
      state_en: `${pattern.name_en} state zone`,
      safety_zh: safetyOption?.name_zh || "独立安全动作区",
      safety_en: safetyOption?.name_en || "Independent safety-action zone",
      service_zh: serviceOption?.name_zh || module.nodes_zh[3],
      service_en: serviceOption?.name_en || module.nodes_en[3],
      rules_zh: [
        `操作：${module.preserve_zh[0]}；新机构不得把该不变项改写成可选功能。`,
        `联合关系：${variant.architecture_zh}；${pattern.name_zh}只在该限定关系中发挥新作用。`,
        `识别：${pattern.name_zh}布置在动作发生处可触或可见的位置，并与相邻按钮和卡位形成形态区分。`,
        `安全：${module.preserve_zh[1]}。`,
        `维护：新功能件与${stateOption?.name_zh || "状态反馈通道"}采用可测试接口，拆换后可校验且不改变基础机械标定。`
      ],
      rules_en: [
        `Operation: ${module.preserve_en[0]}; the new mechanism cannot turn that invariant into an optional feature.`,
        `Joint relationship: ${variant.architecture_en}; the ${pattern.name_en} performs its new role only within this limited relationship.`,
        `Recognition: place the ${pattern.name_en} cue where the action occurs and distinguish it in form from adjacent buttons and detents.`,
        `Safety: ${module.preserve_en[1]}.`,
        `Service: connect the new function to ${stateOption?.name_en || "the state-feedback channel"} through a testable interface that can be calibrated after replacement without changing the base mechanical setting.`
      ]
    },
    innovation_details: {
      conflict_zh: `${contradiction.zh}。在${module.name_zh}内，既要解决“${need.title_zh}”，又必须保留：${module.preserve_zh.join("；")}。`,
      conflict_en: `${contradiction.en}. Within the ${module.name_en}, solve “${need.title_en}” while preserving: ${module.preserve_en.join("; ")}.`,
      elements_zh: embodiment.parts_zh.join("；"),
      elements_en: embodiment.parts_en.join("; "),
      relationship_zh: `${variant.architecture_zh}。${embodiment.summary_zh}`,
      relationship_en: `${variant.architecture_en}. ${embodiment.summary_en}`,
      logic_zh: `${variant.name_zh}：${embodiment.sequence_zh.join(" → ")}`,
      logic_en: `${variant.name_en}: ${embodiment.sequence_en.join(" → ")}`,
      failure_zh: `${variant.focus_zh} ${embodiment.sequence_zh[embodiment.sequence_zh.length - 1]} 同时要求任何单点故障不得阻断主推力连续行程。`,
      failure_en: `${variant.focus_en} ${embodiment.sequence_en[embodiment.sequence_en.length - 1]} No single failure may interrupt continuous primary thrust travel.`,
      protection_zh: `优先保护“${module.name_zh} + ${pattern.name_zh} + ${variant.name_zh}”形成的结构与因果关系。${embodiment.claim_hook_zh} ${avoidanceZh}`,
      protection_en: `Prioritize the structural and causal relationship formed by the ${module.name_en} + ${pattern.name_en} + ${variant.name_en}. ${embodiment.claim_hook_en} ${avoidanceEn}`
    },
    embodiment,
    market,
    ranking: adjustedRanking,
    figure_kind: module.figure,
    figure_nodes_zh: figureNodesZh,
    figure_nodes_en: figureNodesEn,
    figure_caption_zh: `图示为“${module.name_zh} × ${pattern.name_zh} × ${variant.name_zh}”的联合关系草图：${figureNodesZh.join(" → ")}。它用于定义权利要求构件关系，不代表最终制造尺寸。`,
    figure_caption_en: `Joint relationship sketch for “${module.name_en} × ${pattern.name_en} × ${variant.name_en}”: ${figureNodesEn.join(" → ")}. It defines claim relationships, not final manufacturing dimensions.`,
    claims_zh: [
      `独立装置框架：一种${module.name_zh}，包括${pattern.claim_zh.join("、")}，上述构件按“${variant.architecture_zh}”连接。`,
      `结构关系限定：上述构件以“${pattern.principle_zh}”在${variant.name_zh}中形成不同于参考基线的因果关系。`,
      `失效与超控从属项：限定单点故障后的安全形态、人工最终操纵权和主载荷路径隔离。`,
      `方法从属项：依据状态或动作方向改变信息/阻抗，并产生可测的人因或安全效果。`
    ],
    claims_en: [
      `Independent apparatus frame: a ${module.name_en} comprising ${pattern.claim_en.join(", ")}, connected according to “${variant.architecture_en}”.`,
      `Structural relationship: the elements implement “${pattern.principle_en}” through the ${variant.name_en} as a causal path distinct from the reference baseline.`,
      "Failure/override dependent claim: define the safe state after a single failure, final manual authority and isolation from the primary load path.",
      "Method dependent claim: change information or impedance according to state or action direction to create a measurable human-factors or safety effect."
    ],
    validation_zh: validationZh,
    validation_en: validationEn,
    negative_patent_constraints: nearestPatents,
    scores: {
      pilot: pilotValue,
      novelty: differenceOpportunity,
      cert: adjustedRanking.regulation,
      proto: prototypeFeasibility,
      market: adjustedRanking.market
    }
  };
}

function generateConcepts() {
  const need = selectedInventorNeed();
  const module = selectedPatentModule();
  const contradiction = derivedContradictionForModule(module);
  if (!need || !contradiction || !state.inventionPatterns.length) return;
  if (!state.residualInnovations.length) rankResidualInnovations();
  const residual = state.residualInnovations.find(item => item.pattern.id === state.selectedInnovationPattern)
    || state.residualInnovations[0];
  if (!residual) return;
  state.selectedInnovationPattern = residual.pattern.id;
  localStorage.setItem("throttle-innovation-pattern", state.selectedInnovationPattern);
  if (state.adoptedConcept && (
    state.adoptedConcept.module_id !== module.id ||
    state.adoptedConcept.source_need_id !== need.id ||
    state.adoptedConcept.pattern_id !== residual.pattern.id
  )) state.adoptedConcept = null;
  state.inventorChallenge = $("#inventor-challenge")?.value.trim() || "";
  const selected = [];
  const targetTags = new Set([...need.tags, ...contradiction.tags, ...module.needTags]);
  const modulePatentMatches = getModulePatentMatches(module);
  const patentTags = new Set(modulePatentMatches.flatMap(item => item.tags));
  const patentMatches = getPatentMatches(selected, [...targetTags, ...module.patentTags]);
  const previousConceptId = state.selectedConceptId;
  state.generatedConcepts = JOINT_DESIGN_VARIANTS.map((variant, index) => buildInventiveConcept(
    residual.pattern,
    index,
    {need, contradiction, selected, targetTags, patentTags, patentMatches, module, ranking: residual.ranking, variant}
  ));
  state.selectedConceptId = state.generatedConcepts.some(item => item.id === previousConceptId)
    ? previousConceptId
    : (state.generatedConcepts[0]?.id || "");
  updateInventorReasoning();
  renderModuleBoundaries();
  renderGeneratedConcepts();
  renderConceptDetail();
  renderDesignAnalysis();
}

function renderGeneratedConcepts() {
  $("#generated-count").textContent = String(state.generatedConcepts.length).padStart(2, "0");
  $("#generated-concepts").innerHTML = state.generatedConcepts.map(concept => `
    <button class="generated-concept ${concept.id === state.selectedConceptId ? "active" : ""}" type="button" data-concept="${concept.id}">
      <span>${concept.code}</span><strong>${t("total_score")} ${concept.ranking.total}</strong>
      <h4>${localized(concept, "title")}</h4>
      <p>${state.lang === "zh" ? concept.variant.focus_zh : concept.variant.focus_en}</p>
      <dl>
        <div><dt>${t("score_pilot")}</dt><dd>${concept.ranking.problem}</dd></div>
        <div><dt>${t("score_cert")}</dt><dd>${concept.ranking.regulation}</dd></div>
        <div><dt>${t("score_novelty")}</dt><dd>${concept.ranking.patentDistance}</dd></div>
        <div><dt>${t("score_market")}</dt><dd>${concept.ranking.market}</dd></div>
      </dl>
      <div><b>${t("ranking_reason")}</b><i>${state.lang === "zh" ? concept.ranking.reason_zh : concept.ranking.reason_en}</i></div>
    </button>`).join("");
  $$(".generated-concept").forEach(button => {
    button.onclick = () => {
      state.selectedConceptId = button.dataset.concept;
      renderGeneratedConcepts();
      renderConceptDetail();
      renderDesignAnalysis();
    };
  });
}

function conceptFigureMarkup(concept) {
  const nodes = state.lang === "zh" ? concept.figure_nodes_zh : concept.figure_nodes_en;
  return `
    <div class="figure-hardware figure-${concept.figure_kind}" aria-hidden="true">
      <i class="figure-part part-a"></i>
      <i class="figure-part part-b"></i>
      <i class="figure-part part-c"></i>
      <i class="figure-part part-d"></i>
      <em class="figure-axis"></em>
      <b class="figure-callout callout-a">A</b>
      <b class="figure-callout callout-b">B</b>
      <b class="figure-callout callout-c">C</b>
      <b class="figure-callout callout-d">D</b>
    </div>
    <div class="figure-logic">
      ${nodes.map((node, index) => `<div><span>${String.fromCharCode(65 + index)}</span><b>${node}</b></div>${index < nodes.length - 1 ? "<i>→</i>" : ""}`).join("")}
    </div>`;
}

function renderConceptDetail() {
  const concept = state.generatedConcepts.find(item => item.id === state.selectedConceptId);
  if (!concept) return;
  const module = PATENT_MODULES.find(item => item.id === concept.module_id) || selectedPatentModule();
  const need = state.pilotNeeds.find(item => item.id === concept.source_need_id);
  $("#concept-detail-code").textContent = concept.code;
  $("#concept-detail-title").textContent = localized(concept, "title");
  $("#research-problem-title").textContent = need ? localized(need, "title") : localized(concept, "title");
  $("#research-problem-copy").textContent = localized(concept, "problem");
  $("#research-source-org").textContent = `${concept.research.source_organization} · ${state.lang === "zh" ? concept.research.source_title_zh : concept.research.source_title_en} · SEV ${concept.research.severity}/5`;
  $("#research-source-link").href = concept.research.source_url;
  $("#research-patent-table").innerHTML = concept.research.comparisons.length
    ? concept.research.comparisons.map(patent => `
      <article>
        <div><b>${patent.publication_no}</b><span>${patent.score}% ${t("overlap")}</span><a href="${patent.url}" target="_blank" rel="noreferrer">↗</a></div>
        <h5>${state.lang === "zh" ? patent.title_zh : patent.title_en}</h5>
        <dl>
          <div><dt>${t("known_solution")}</dt><dd>${state.lang === "zh" ? patent.known_zh : patent.known_en}</dd></div>
          <div><dt>${t("design_response")}</dt><dd>${state.lang === "zh" ? patent.response_zh : patent.response_en}</dd></div>
        </dl>
      </article>`).join("")
    : `<p class="empty-patent-comparison">${t("no_direct_patent")}</p>`;
  $("#research-gap").textContent = state.lang === "zh" ? concept.research.gap_zh : concept.research.gap_en;
  const embodiment = concept.embodiment;
  const embodimentParts = state.lang === "zh" ? embodiment.parts_zh : embodiment.parts_en;
  const embodimentSequence = state.lang === "zh" ? embodiment.sequence_zh : embodiment.sequence_en;
  $("#embodiment-name").textContent = state.lang === "zh" ? embodiment.name_zh : embodiment.name_en;
  $("#embodiment-summary").textContent = state.lang === "zh" ? embodiment.summary_zh : embodiment.summary_en;
  embodimentParts.slice(0, 4).forEach((part, index) => {
    $(`#embodiment-part-${String.fromCharCode(97 + index)}`).textContent = part.replace(/^[A-D]\s*[｜|]\s*/, "");
  });
  $("#embodiment-parts").innerHTML = embodimentParts.map(item => `<li>${item}</li>`).join("");
  $("#embodiment-sequence").innerHTML = embodimentSequence.map(item => `<li>${item}</li>`).join("");
  $("#embodiment-baseline").textContent = state.lang === "zh" ? embodiment.baseline_zh : embodiment.baseline_en;
  $("#embodiment-delta").textContent = state.lang === "zh" ? embodiment.delta_zh : embodiment.delta_en;
  $("#embodiment-claim-hook").textContent = state.lang === "zh" ? embodiment.claim_hook_zh : embodiment.claim_hook_en;
  $("#concept-figure-module").textContent = localized(module, "name");
  $("#concept-figure-canvas").innerHTML = conceptFigureMarkup(concept);
  $("#concept-figure-caption").textContent = state.lang === "zh" ? concept.figure_caption_zh : concept.figure_caption_en;
  $("#concept-principle").textContent = localized(concept, "principle");
  $("#concept-mechanism").textContent = localized(concept, "mechanism");
  $("#innovation-reuse-copy").textContent = localized(concept, "reuse");
  $("#innovation-core-copy").textContent = localized(concept, "core");
  $("#concept-why").textContent = localized(concept, "why");
  $("#innovation-conflict-copy").textContent = state.lang === "zh" ? concept.innovation_details.conflict_zh : concept.innovation_details.conflict_en;
  $("#innovation-elements-copy").textContent = state.lang === "zh" ? concept.innovation_details.elements_zh : concept.innovation_details.elements_en;
  $("#innovation-relationship-copy").textContent = state.lang === "zh" ? concept.innovation_details.relationship_zh : concept.innovation_details.relationship_en;
  $("#innovation-logic-copy").textContent = state.lang === "zh" ? concept.innovation_details.logic_zh : concept.innovation_details.logic_en;
  $("#innovation-failure-copy").textContent = state.lang === "zh" ? concept.innovation_details.failure_zh : concept.innovation_details.failure_en;
  $("#innovation-protection-copy").textContent = state.lang === "zh" ? concept.innovation_details.protection_zh : concept.innovation_details.protection_en;
  $("#effect-structure").textContent = state.lang === "zh" ? concept.effects.structure_zh : concept.effects.structure_en;
  $("#effect-action").textContent = state.lang === "zh" ? concept.effects.action_zh : concept.effects.action_en;
  $("#effect-direct").textContent = state.lang === "zh" ? concept.effects.direct_zh : concept.effects.direct_en;
  $("#effect-metric").textContent = state.lang === "zh" ? concept.effects.metric_zh : concept.effects.metric_en;
  $("#layout-primary").textContent = state.lang === "zh" ? concept.layout.primary_zh : concept.layout.primary_en;
  $("#layout-state").textContent = state.lang === "zh" ? concept.layout.state_zh : concept.layout.state_en;
  $("#layout-safety").textContent = state.lang === "zh" ? concept.layout.safety_zh : concept.layout.safety_en;
  $("#layout-service").textContent = state.lang === "zh" ? concept.layout.service_zh : concept.layout.service_en;
  const layoutRules = state.lang === "zh" ? concept.layout.rules_zh : concept.layout.rules_en;
  $("#layout-rules").innerHTML = layoutRules.map(item => `<li>${item}</li>`).join("");
  $("#market-target").textContent = state.lang === "zh" ? concept.market.target_zh : concept.market.target_en;
  $("#market-customer").textContent = state.lang === "zh" ? concept.market.customer_zh : concept.market.customer_en;
  $("#market-entry").textContent = state.lang === "zh" ? concept.market.entry_zh : concept.market.entry_en;
  $("#market-barrier").textContent = state.lang === "zh" ? concept.market.barrier_zh : concept.market.barrier_en;
  const claims = state.lang === "zh" ? concept.claims_zh : concept.claims_en;
  const validation = state.lang === "zh" ? concept.validation_zh : concept.validation_en;
  $("#concept-claims").innerHTML = claims.map(item => `<li>${item}</li>`).join("");
  $("#concept-validation").innerHTML = validation.map(item => `<li>${item}</li>`).join("");
  $("#claim-negative-constraints").innerHTML = concept.research.comparisons.length
    ? concept.research.comparisons.map(patent => `<a href="${patent.url}" target="_blank" rel="noreferrer"><b>${patent.publication_no}</b><span>${state.lang === "zh" ? patent.title_zh : patent.title_en}</span><i>${patent.score}%</i></a>`).join("")
    : `<p>${t("no_direct_patent")}</p>`;
  Object.entries(concept.scores).forEach(([key, score]) => {
    $(`#score-${key}`).style.width = `${score}%`;
    $(`#score-${key}-value`).textContent = `${score}/100`;
  });
  const adopted = state.adoptedConcept?.id === concept.id;
  const label = $("#adopt-concept span");
  label.dataset.i18n = adopted ? "concept_adopted" : "adopt_concept";
  label.textContent = t(label.dataset.i18n);
}

function adoptSelectedConcept() {
  const concept = state.generatedConcepts.find(item => item.id === state.selectedConceptId);
  if (!concept) return;
  state.adoptedConcept = concept;
  renderConceptDetail();
  renderDesignAnalysis();
}

function renderInventorControls() {
  if (!state.pilotNeeds.length || !state.inventionPatterns.length) return;
  const module = selectedPatentModule();
  const moduleNeedTags = new Set(module.needTags);
  const orderedNeeds = [...state.pilotNeeds].sort((a, b) => {
    const aHits = a.tags.filter(tag => moduleNeedTags.has(tag)).length;
    const bHits = b.tags.filter(tag => moduleNeedTags.has(tag)).length;
    return bHits - aHits || b.severity - a.severity || b.evidence_count - a.evidence_count;
  });
  if (!state.pilotNeeds.some(need => need.id === state.inventorProblem)) {
    state.inventorProblem = orderedNeeds[0].id;
  }
  $("#inventor-problem").innerHTML = orderedNeeds.map(need =>
    `<option value="${need.id}">${localized(need, "title")}</option>`
  ).join("");
  $("#inventor-problem").value = state.inventorProblem;
  $("#inventor-challenge").value = state.inventorChallenge;
  $("#inventor-problem").onchange = event => {
    state.inventorProblem = event.target.value;
    rankResidualInnovations();
    updateInventorReasoning();
    generateConcepts();
  };
  $("#inventor-challenge").oninput = event => {
    state.inventorChallenge = event.target.value;
  };
  $("#generate-concepts").onclick = generateConcepts;
  $("#adopt-concept").onclick = adoptSelectedConcept;
  updateInventorReasoning();
  if (state.generatedConcepts.length) {
    renderGeneratedConcepts();
    renderConceptDetail();
  }
}

function renderDesignStudio() {
  renderPatentModules();
  renderInventorControls();
  renderModuleBoundaries();
  void loadPatentModuleContext();
  renderDesignAnalysis();
}

function getPatentMatches(selected = [], contextualTags = []) {
  const selectedTags = new Set([...selected.flatMap(option => option.tags), ...contextualTags]);
  return state.patents.map(patent => {
    const matched = patent.tags.filter(tag => selectedTags.has(tag));
    const score = patent.tags.length ? Math.round(matched.length / patent.tags.length * 100) : 0;
    return {...patent, matched, score};
  }).sort((a, b) => b.score - a.score || b.priority_date.localeCompare(a.priority_date));
}

function getNeedPriorities(selected, contextualTags = []) {
  const selectedTags = new Set([...selected.flatMap(option => option.tags), ...contextualTags]);
  return state.pilotNeeds.map(need => {
    const tagHits = need.tags.filter(tag => selectedTags.has(tag)).length;
    const score = Math.min(99, need.severity * 10 + need.evidence_count * 4 + tagHits * 7);
    return {...need, score, tagHits};
  }).sort((a, b) => b.score - a.score || b.severity - a.severity);
}

function renderDesignAnalysis() {
  const workingConcept = state.adoptedConcept || state.generatedConcepts.find(item => item.id === state.selectedConceptId);
  const selectedNeed = selectedInventorNeed();
  const pattern = state.inventionPatterns.find(item => item.id === workingConcept?.pattern_id);
  const module = selectedPatentModule();
  const contextualTags = [...module.patentTags, ...module.needTags, ...(selectedNeed?.tags || []), ...(pattern?.suitable_tags || [])];
  const patentMatches = getPatentMatches([], contextualTags);
  $("#patent-count").textContent = String(state.patents.length).padStart(2, "0");
  $("#patent-matches").innerHTML = patentMatches.slice(0, 4).map(patent => {
    const level = patent.score >= 50 ? "high" : patent.score >= 25 ? "medium" : "low";
    const changes = state.lang === "zh" ? patent.change_zh : patent.change_en;
    return `<article class="patent-match ${level}">
      <div class="overlap-score">${patent.score}%<small>${t("overlap")}</small></div>
      <div><h4>${patent.publication_no} · ${localized(patent, "title")}</h4><p>${localized(patent, "claim")}</p></div>
      <a href="${patent.url}" target="_blank" rel="noreferrer">${t("source_reference")} ↗</a>
      <div class="patent-change"><b>${t("difference_prompt")}：</b>${changes[0] || "—"}</div>
    </article>`;
  }).join("");

  const priorities = getNeedPriorities([], module.needTags);
  $("#need-count").textContent = String(state.pilotNeeds.length).padStart(2, "0");
  $("#need-priorities").innerHTML = priorities.slice(0, 4).map((need, index) => `
    <article class="need-card">
      <div class="need-rank">${String(index + 1).padStart(2, "0")}</div>
      <div>
        <h4>${localized(need, "title")}</h4>
        <p>${localized(need, "problem")}</p>
        <div class="need-opportunity">${localized(need, "opportunity")}</div>
        <div class="need-meta"><span>${t("priority_score")} ${need.score} · SEV ${need.severity}/5</span><a href="${need.url}" target="_blank" rel="noreferrer">${need.organization} ↗</a></div>
      </div>
    </article>`).join("");

  const topNeed = priorities[0];
  const topPatent = patentMatches[0];
  const changes = state.lang === "zh" ? topPatent?.change_zh : topPatent?.change_en;
  if (workingConcept) {
    const validation = state.lang === "zh" ? workingConcept.validation_zh : workingConcept.validation_en;
    $("#brief-problem").textContent = localized(workingConcept, "problem");
    $("#brief-mechanism").textContent = localized(workingConcept, "mechanism");
    $("#brief-difference").textContent = localized(workingConcept, "why");
    $("#brief-evidence").textContent = validation.join(state.lang === "zh" ? "；" : "; ");
  } else {
    $("#brief-problem").textContent = topNeed ? `${localized(topNeed, "title")}：${localized(topNeed, "problem")}` : "—";
    $("#brief-mechanism").textContent = "—";
    $("#brief-difference").textContent = changes?.[0] || "—";
    $("#brief-evidence").textContent = state.lang === "zh"
      ? "完成任务场景可用性试验、误操作序列试验、力—位移曲线、故障注入和不同身高飞行员可达性验证，并把结果与现有方案对照。"
      : "Run task-based usability, erroneous-sequence, force-travel, failure-injection and stature-reach tests, then compare measured results against prior designs.";
  }
}

function designProjectPayload() {
  const selected = [];
  const workingConcept = state.adoptedConcept || state.generatedConcepts.find(item => item.id === state.selectedConceptId);
  const chapterTwo = workingConcept ? {
    status: state.adoptedConcept?.id === workingConcept.id ? "adopted" : "working_draft",
    concept_id: workingConcept.id,
    "2.1_research_situation": {
      problem_zh: workingConcept.problem_zh,
      problem_en: workingConcept.problem_en,
      source: {
        organization: workingConcept.research.source_organization,
        title_zh: workingConcept.research.source_title_zh,
        title_en: workingConcept.research.source_title_en,
        url: workingConcept.research.source_url
      },
      patent_comparisons: workingConcept.research.comparisons,
      unresolved_gap_zh: workingConcept.research.gap_zh,
      unresolved_gap_en: workingConcept.research.gap_en
    },
    "2.2_innovation_points": {
      selected_residual_innovation: {
        id: workingConcept.selected_innovation_id,
        name_zh: workingConcept.selected_innovation_name_zh,
        name_en: workingConcept.selected_innovation_name_en,
        ranking: workingConcept.ranking
      },
      joint_design_variant: workingConcept.variant,
      new_technology_zh: workingConcept.principle_zh,
      new_technology_en: workingConcept.principle_en,
      new_architecture_zh: workingConcept.mechanism_zh,
      new_architecture_en: workingConcept.mechanism_en,
      known_technology_in_new_architecture_zh: workingConcept.reuse_zh,
      known_technology_in_new_architecture_en: workingConcept.reuse_en,
      core_innovation_zh: workingConcept.core_zh,
      core_innovation_en: workingConcept.core_en,
      why_not_aggregation_zh: workingConcept.why_zh,
      why_not_aggregation_en: workingConcept.why_en,
      concrete_embodiment: workingConcept.embodiment,
      detailed_breakdown: workingConcept.innovation_details
    },
    "2.3_technical_effects": workingConcept.effects,
    "2.4_layout_plan": workingConcept.layout,
    "2.5_market_factors": workingConcept.market,
    claim_skeleton_zh: workingConcept.claims_zh,
    claim_skeleton_en: workingConcept.claims_en,
    validation_plan_zh: workingConcept.validation_zh,
    validation_plan_en: workingConcept.validation_en
  } : null;
  return {
    schema: "throttle-patent-project/v5",
    saved_at: new Date().toISOString(),
    name: $("#project-name")?.value || localized(workingConcept, "title") || "Throttle concept",
    goal: state.designGoal,
    language: state.lang,
    selections: {},
    invention_inputs: {
      module_id: state.patentModule,
      need_id: state.inventorProblem,
      contradiction_id: state.inventorContradiction,
      selected_innovation_id: state.selectedInnovationPattern,
      user_constraint: state.inventorChallenge
    },
    module_scope: selectedPatentModule(),
    constraint_summary: {
      regulation_ids: selectedPatentModule().regulatoryIds,
      regulation_records: state.moduleConstraints.map(item => ({
        authority: item.authority,
        rule_ref: item.rule_ref,
        source_id: item.source_id,
        source_url: item.url
      })),
      patent_negative_constraints: getModulePatentMatches().slice(0, 5).map(item => ({
        publication_no: item.publication_no,
        overlap_score: item.moduleScore,
        matched_features: item.matched,
        source_url: item.url
      }))
    },
    residual_innovation_ranking: state.residualInnovations.map((item, index) => ({
      rank: index + 1,
      id: item.pattern.id,
      name_zh: item.pattern.name_zh,
      name_en: item.pattern.name_en,
      principle_zh: item.pattern.principle_zh,
      principle_en: item.pattern.principle_en,
      ranking: item.ranking,
      selected: item.pattern.id === state.selectedInnovationPattern
    })),
    joint_design_schemes: state.generatedConcepts,
    invention_concept: workingConcept,
    chapter_2: chapterTwo,
    components: selected.map(option => ({
      id: option.id,
      slot: localized(option, "slot"),
      name: localized(option, "name"),
      innovation_space: localized(option, "change_space"),
      protected_boundary: localized(option, "protected_zone"),
      source_id: option.source_id,
      source_url: option.url
    })),
    patent_matches: getModulePatentMatches().slice(0, 5).map(patent => ({
      publication_no: patent.publication_no,
      overlap_score: patent.moduleScore,
      matched_features: patent.matched,
      source_url: patent.url
    })),
    pilot_priorities: getNeedPriorities(selected, selectedPatentModule().needTags).slice(0, 5).map(need => ({
      id: need.id,
      priority_score: need.score,
      source_url: need.url
    })),
    disclaimer: "Search and ideation aid only; not a patentability, novelty or freedom-to-operate opinion."
  };
}

function briefText() {
  const concept = state.adoptedConcept || state.generatedConcepts.find(item => item.id === state.selectedConceptId);
  const projectName = $("#project-name")?.value || localized(concept, "title") || "Throttle concept";
  if (!concept) return projectName;
  const zh = state.lang === "zh";
  const comparisons = concept.research.comparisons.map(item =>
    `- ${item.publication_no} · ${zh ? item.title_zh : item.title_en}\n  ${t("design_response")}: ${zh ? item.response_zh : item.response_en}`
  ).join("\n");
  const validation = (zh ? concept.validation_zh : concept.validation_en).map(item => `- ${item}`).join("\n");
  const layout = (zh ? concept.layout.rules_zh : concept.layout.rules_en).map(item => `- ${item}`).join("\n");
  const claims = (zh ? concept.claims_zh : concept.claims_en).map(item => `- ${item}`).join("\n");
  const embodimentParts = (zh ? concept.embodiment.parts_zh : concept.embodiment.parts_en).map(item => `- ${item}`).join("\n");
  const embodimentSequence = (zh ? concept.embodiment.sequence_zh : concept.embodiment.sequence_en).map((item, index) => `${index + 1}. ${item}`).join("\n");
  const module = PATENT_MODULES.find(item => item.id === concept.module_id) || selectedPatentModule();
  const preserve = zh ? module.preserve_zh : module.preserve_en;
  const exclude = zh ? module.exclude_zh : module.exclude_en;
  const selectedInnovation = zh ? concept.selected_innovation_name_zh : concept.selected_innovation_name_en;
  const jointVariant = zh ? concept.variant.name_zh : concept.variant.name_en;
  return [
    projectName,
    `${concept.code} · ${localized(concept, "title")}`,
    `${t("choose_patent_module")}: ${localized(module, "name")}\n${localized(module, "scope")}\n\n${t("regulation_fence")}\n${preserve.map(item => `- ${item}`).join("\n")}\n\n${t("patent_fence")}\n${exclude.map(item => `- ${item}`).join("\n")}\n\n${t("rank_residual_innovations")}: ${selectedInnovation}\n${t("generated_directions")}: ${jointVariant}\n${t("total_score")}: ${concept.ranking.total}/100\n${t("ranking_reason")}: ${zh ? concept.ranking.reason_zh : concept.ranking.reason_en}`,
    `2.1 ${t("chapter_research")}\n${localized(concept, "problem")}\n${comparisons}\n${t("research_conclusion")}: ${zh ? concept.research.gap_zh : concept.research.gap_en}`,
    `2.2 ${t("chapter_innovation")}\n${t("concrete_embodiment")}: ${zh ? concept.embodiment.name_zh : concept.embodiment.name_en}\n${zh ? concept.embodiment.summary_zh : concept.embodiment.summary_en}\n\n${t("prototype_parts")}\n${embodimentParts}\n\n${t("action_sequence")}\n${embodimentSequence}\n\n${t("existing_path")}: ${zh ? concept.embodiment.baseline_zh : concept.embodiment.baseline_en}\n${t("specific_difference")}: ${zh ? concept.embodiment.delta_zh : concept.embodiment.delta_en}\n${t("claim_hook")}: ${zh ? concept.embodiment.claim_hook_zh : concept.embodiment.claim_hook_en}\n\n${t("innovation_new_tech")}: ${localized(concept, "principle")}\n${t("innovation_new_arch")}: ${localized(concept, "mechanism")}\n${t("innovation_reuse")}: ${localized(concept, "reuse")}\n${t("core_innovation")}: ${localized(concept, "core")}\n${t("innovation_conflict")}: ${zh ? concept.innovation_details.conflict_zh : concept.innovation_details.conflict_en}\n${t("innovation_elements")}: ${zh ? concept.innovation_details.elements_zh : concept.innovation_details.elements_en}\n${t("innovation_relationship")}: ${zh ? concept.innovation_details.relationship_zh : concept.innovation_details.relationship_en}\n${t("innovation_logic")}: ${zh ? concept.innovation_details.logic_zh : concept.innovation_details.logic_en}\n${t("innovation_failure")}: ${zh ? concept.innovation_details.failure_zh : concept.innovation_details.failure_en}\n${t("innovation_protection")}: ${zh ? concept.innovation_details.protection_zh : concept.innovation_details.protection_en}`,
    `2.3 ${t("chapter_effects")}\n${zh ? concept.effects.direct_zh : concept.effects.direct_en}\n${validation}`,
    `2.4 ${t("chapter_layout")}\n${layout}`,
    `2.5 ${t("chapter_market")}\n${t("market_target")}: ${zh ? concept.market.target_zh : concept.market.target_en}\n${t("market_customer")}: ${zh ? concept.market.customer_zh : concept.market.customer_en}\n${t("market_entry")}: ${zh ? concept.market.entry_zh : concept.market.entry_en}\n${t("market_barrier")}: ${zh ? concept.market.barrier_zh : concept.market.barrier_en}`,
    `${t("claim_skeleton")}\n${claims}`
  ].join("\n\n");
}

function shade(hex, factor = 1, alpha = 1) {
  const clean = hex.replace("#", "");
  const n = parseInt(clean.length === 3 ? clean.split("").map(c => c + c).join("") : clean, 16);
  const r = Math.max(0, Math.min(255, Math.round(((n >> 16) & 255) * factor)));
  const g = Math.max(0, Math.min(255, Math.round(((n >> 8) & 255) * factor)));
  const b = Math.max(0, Math.min(255, Math.round((n & 255) * factor)));
  return `rgba(${r},${g},${b},${alpha})`;
}

class Software3D {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.rotX = -0.33;
    this.rotY = -0.58;
    this.zoom = 1;
    this.auto = true;
    this.view = "split";
    this.dragging = false;
    this.last = {x: 0, y: 0};
    this.modelA = null;
    this.modelB = null;
    this.faces = [];
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(canvas.parentElement);
    this.bind();
    this.resize();
    this.loop();
  }
  bind() {
    this.canvas.addEventListener("pointerdown", e => {
      this.dragging = true; this.last = {x: e.clientX, y: e.clientY};
      this.canvas.setPointerCapture(e.pointerId);
    });
    this.canvas.addEventListener("pointermove", e => {
      if (!this.dragging) return;
      this.rotY += (e.clientX - this.last.x) * .008;
      this.rotX += (e.clientY - this.last.y) * .006;
      this.rotX = Math.max(-1.05, Math.min(.35, this.rotX));
      this.last = {x: e.clientX, y: e.clientY};
    });
    this.canvas.addEventListener("pointerup", () => this.dragging = false);
    this.canvas.addEventListener("pointercancel", () => this.dragging = false);
    this.canvas.addEventListener("wheel", e => {
      e.preventDefault();
      this.zoom = Math.max(.62, Math.min(1.75, this.zoom - e.deltaY * .0008));
    }, {passive: false});
  }
  resize() {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = Math.min(devicePixelRatio || 1, 2);
    this.canvas.width = Math.max(1, Math.floor(rect.width * dpr));
    this.canvas.height = Math.max(1, Math.floor(rect.height * dpr));
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.width = rect.width;
    this.height = rect.height;
  }
  setModels(a, b) { this.modelA = a; this.modelB = b; }
  reset() { this.rotX = -0.33; this.rotY = -0.58; this.zoom = 1; }
  setView(view) { this.view = view; }
  rotateLocal(p, rx = 0, ry = 0, rz = 0) {
    let {x, y, z} = p;
    let c = Math.cos(rx), s = Math.sin(rx);
    [y, z] = [y * c - z * s, y * s + z * c];
    c = Math.cos(ry); s = Math.sin(ry);
    [x, z] = [x * c + z * s, -x * s + z * c];
    c = Math.cos(rz); s = Math.sin(rz);
    [x, y] = [x * c - y * s, x * s + y * c];
    return {x, y, z};
  }
  transform(p) {
    let {x, y, z} = p;
    let c = Math.cos(this.rotY), s = Math.sin(this.rotY);
    [x, z] = [x * c + z * s, -x * s + z * c];
    c = Math.cos(this.rotX); s = Math.sin(this.rotX);
    [y, z] = [y * c - z * s, y * s + z * c];
    return {x, y, z};
  }
  project(p) {
    const q = this.transform(p);
    const camera = 8.4;
    const perspective = camera / (camera + q.z);
    const scale = Math.min(this.width, this.height) * .155 * this.zoom * perspective;
    return {x: this.width / 2 + q.x * scale, y: this.height * .50 - q.y * scale, z: q.z, perspective};
  }
  addBox(cx, cy, cz, w, h, d, color, opts = {}) {
    const raw = [
      [-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
      [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]
    ].map(([x,y,z]) => ({x:x*w/2,y:y*h/2,z:z*d/2}));
    const verts = raw.map(p => {
      const r = this.rotateLocal(p, opts.rx || 0, opts.ry || 0, opts.rz || 0);
      return {x:r.x+cx,y:r.y+cy,z:r.z+cz};
    });
    const faces = [
      [0,1,2,3,.58],[4,7,6,5,1.0],[0,4,5,1,.72],
      [3,2,6,7,1.22],[1,5,6,2,.86],[0,3,7,4,.66]
    ];
    faces.forEach(([a,b,c,d2,light]) => {
      const points = [verts[a],verts[b],verts[c],verts[d2]].map(v => this.project(v));
      this.faces.push({
        points, z: points.reduce((n,p)=>n+p.z,0)/4,
        fill: shade(color, light, opts.alpha ?? 1),
        stroke: opts.stroke || `rgba(220,238,237,${(opts.alpha ?? 1)*.10})`
      });
    });
  }
  addModel(model, offset, color, alpha = 1) {
    const g = model.geometry;
    const baseWidth = {wide:2.5,pedestal:2.25,modern:2.35,side:1.85}[g.base] || 2.0;
    const baseDepth = g.base === "side" ? 1.45 : 1.8;
    this.addBox(offset, -.68, 0, baseWidth, .48, baseDepth, color, {alpha});
    this.addBox(offset, -.38, -.05, baseWidth*.82, .18, baseDepth*.75, color, {alpha, rx:-.08});
    const positions = g.levers === 1 ? [0] : [-g.split*.31, g.split*.31];
    positions.forEach((pos, index) => {
      const leverX = offset + pos;
      const lean = g.base === "side" ? -.20 : -.14;
      this.addBox(leverX, .35, .03, .16, 1.38, .18, "#354653", {alpha, rx:lean, rz: g.levers > 1 ? (index ? -.025 : .025) : 0});
      const gripY = 1.08;
      const fighter = g.grip === "fighter" || g.grip === "euro" || g.grip === "flanker";
      const gripWidth = fighter ? .53 : .48;
      const gripDepth = fighter ? .56 : .43;
      this.addBox(leverX, gripY, -.07, gripWidth, fighter ? .48 : .37, gripDepth, fighter ? "#1b2933" : "#202d36", {alpha, rx:lean*.55});
      if (!fighter) {
        this.addBox(leverX, gripY-.10, -.32, gripWidth*.62, .07, .12, index ? "#59dbe8" : "#ff7448", {alpha});
      } else {
        const buttonCount = Math.min(4, Math.max(2, Math.round(g.buttons / 3)));
        for (let b=0;b<buttonCount;b++) {
          const bx = leverX + (b % 2 ? .12 : -.12);
          const by = gripY + (b > 1 ? .12 : -.10);
          this.addBox(bx, by, -.39, .09, .09, .06, b === 0 ? "#ccff38" : "#61717b", {alpha});
        }
      }
      if (g.category === "commercial" || model.category === "commercial") {
        this.addBox(leverX, .82, .18, .22, .50, .12, "#111b22", {alpha, rx:-.34});
      }
    });
    const panelCount = Math.min(5, Math.max(2, Math.round(g.buttons/2)));
    for (let i=0;i<panelCount;i++) {
      const px = offset - baseWidth*.31 + i*(baseWidth*.62/Math.max(1,panelCount-1));
      this.addBox(px, -.23, -.52, .12, .07, .12, i%2 ? "#44545e" : "#ccff38", {alpha});
    }
    if (g.levers === 2) {
      this.addBox(offset, -.12, .48, .62, .15, .22, "#121d25", {alpha});
    }
  }
  drawGrid() {
    const ctx = this.ctx;
    ctx.save();
    ctx.lineWidth = .7;
    for (let i=-5;i<=5;i++) {
      const a = this.project({x:i,y:-.94,z:-4});
      const b = this.project({x:i,y:-.94,z:4});
      ctx.strokeStyle = i === 0 ? "rgba(204,255,56,.18)" : "rgba(151,180,190,.08)";
      ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();
      const c = this.project({x:-5,y:-.94,z:i});
      const d = this.project({x:5,y:-.94,z:i});
      ctx.strokeStyle = i === 0 ? "rgba(89,219,232,.16)" : "rgba(151,180,190,.08)";
      ctx.beginPath();ctx.moveTo(c.x,c.y);ctx.lineTo(d.x,d.y);ctx.stroke();
    }
    ctx.restore();
  }
  drawAxis() {
    const ctx = this.ctx;
    const o = this.project({x:0,y:-.9,z:0});
    [
      [{x:1.2,y:-.9,z:0},"#ff7448"],
      [{x:0,y:.3,z:0},"#ccff38"],
      [{x:0,y:-.9,z:1.2},"#59dbe8"]
    ].forEach(([point,color]) => {
      const p=this.project(point);ctx.strokeStyle=color;ctx.lineWidth=1.2;
      ctx.beginPath();ctx.moveTo(o.x,o.y);ctx.lineTo(p.x,p.y);ctx.stroke();
    });
  }
  render() {
    const ctx = this.ctx;
    ctx.clearRect(0,0,this.width,this.height);
    this.drawGrid();
    this.faces = [];
    if (this.modelA && this.modelB) {
      if (this.view === "split") {
        this.addModel(this.modelA, -2.0, "#51636e", 1);
        this.addModel(this.modelB, 2.0, "#3e6670", 1);
      } else {
        this.addModel(this.modelA, -.12, "#ff7448", .55);
        this.addModel(this.modelB, .12, "#59dbe8", .55);
      }
    }
    this.faces.sort((a,b) => b.z - a.z);
    this.faces.forEach(face => {
      ctx.beginPath();
      face.points.forEach((p,i) => i ? ctx.lineTo(p.x,p.y) : ctx.moveTo(p.x,p.y));
      ctx.closePath();ctx.fillStyle=face.fill;ctx.fill();
      ctx.strokeStyle=face.stroke;ctx.lineWidth=.65;ctx.stroke();
    });
    this.drawAxis();
  }
  loop() {
    if (this.auto && !this.dragging) this.rotY += .0026;
    this.render();
    requestAnimationFrame(() => this.loop());
  }
}

let renderer;

function bindUI() {
  $("#lang-toggle").addEventListener("click", () => {
    state.lang = state.lang === "zh" ? "en" : "zh";
    applyLanguage();
    const defaultQuery = state.lang === "zh" ? "A320 自动推力" : "A320 autothrust";
    runSearch(defaultQuery);
  });
  $(".menu-button").addEventListener("click", () => document.body.classList.toggle("menu-open"));
  $$(".nav a").forEach(a => a.addEventListener("click", () => document.body.classList.remove("menu-open")));
  $("#copy-brief").addEventListener("click", async event => {
    try {
      await navigator.clipboard.writeText(briefText());
    } catch {
      const area = document.createElement("textarea");
      area.value = briefText();
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
    }
    const label = $("span", event.currentTarget);
    const original = label.textContent;
    label.textContent = t("copied");
    setTimeout(() => { label.textContent = original; }, 1200);
  });
  $$(".segmented button").forEach(button => button.addEventListener("click", () => {
    $$(".segmented button").forEach(b => b.classList.remove("active"));
    button.classList.add("active");
    state.filter = button.dataset.filter;
    renderModelCards();
  }));
  ["model-a","model-b"].forEach(id => $(`#${id}`).addEventListener("change", e => {
    const slot = id.endsWith("a") ? "a" : "b";
    $(`#function-${slot}`).value = e.target.value;
    updateAllComparators();
  }));
  ["function-a","function-b"].forEach(id => $(`#${id}`).addEventListener("change", updateComparison));
  $("#swap-models").addEventListener("click", () => {
    const a = $("#model-a").value, b = $("#model-b").value;
    $("#model-a").value = b; $("#model-b").value = a;
    $("#function-a").value = b; $("#function-b").value = a;
    updateAllComparators();
  });
  $$(".view-toggle button").forEach(button => button.addEventListener("click", () => {
    $$(".view-toggle button").forEach(b => b.classList.remove("active"));
    button.classList.add("active");
    state.view = button.dataset.view;
    renderer.setView(state.view);
    $(".canvas-shell").classList.toggle("overlay", state.view === "overlay");
  }));
  $("#auto-rotate").addEventListener("click", e => {
    renderer.auto = !renderer.auto;
    e.currentTarget.classList.toggle("active", renderer.auto);
  });
  $("#reset-view").addEventListener("click", () => renderer.reset());
  $("#search-form").addEventListener("submit", e => {
    e.preventDefault(); runSearch($("#knowledge-query").value);
  });
  $$(".quick-queries button").forEach(button => button.addEventListener("click", () => {
    runSearch(state.lang === "zh" ? button.dataset.queryZh : button.dataset.queryEn);
  }));
  $("#show-sources").addEventListener("click", () => {
    $("#source-drawer").hidden = false;
    document.body.style.overflow = "hidden";
  });
  $("#close-sources").addEventListener("click", () => {
    $("#source-drawer").hidden = true;
    document.body.style.overflow = "";
  });
  const sectionNames = {overview:"OVERVIEW",studio:"PATENT DESIGN",library:"MODEL LIBRARY",visual:"3D COMPARE",function:"FUNCTIONS",regulations:"REGULATIONS",knowledge:"KNOWLEDGE"};
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      $$(".nav a").forEach(a => a.classList.toggle("active", a.getAttribute("href") === `#${entry.target.id}`));
      $("#current-section").textContent = sectionNames[entry.target.id] || entry.target.id.toUpperCase();
    });
  }, {rootMargin:"-38% 0px -56% 0px"});
  ["overview","studio","library","visual","function","regulations","knowledge"].forEach(id => observer.observe($(`#${id}`)));
}

async function init() {
  applyLanguage();
  try {
    const saved = JSON.parse(localStorage.getItem("throttle-patent-project") || "null");
    if (saved?.selections) state.designSelections = {...state.designSelections, ...saved.selections};
    if (saved?.goal) state.designGoal = saved.goal;
    if (saved?.name && $("#project-name")) $("#project-name").value = saved.name;
    if (saved?.invention_inputs) {
      if (PATENT_MODULES.some(module => module.id === saved.invention_inputs.module_id)) {
        state.patentModule = saved.invention_inputs.module_id;
      }
      state.inventorProblem = saved.invention_inputs.need_id || state.inventorProblem;
      state.inventorContradiction = saved.invention_inputs.contradiction_id || state.inventorContradiction;
      state.selectedInnovationPattern = saved.invention_inputs.selected_innovation_id
        || saved.invention_inputs.preferred_pattern_id
        || state.selectedInnovationPattern;
      state.inventorChallenge = saved.invention_inputs.user_constraint || "";
    }
    if (saved?.invention_concept?.module_id && saved?.invention_concept?.variant_id && saved?.invention_concept?.innovation_details && saved.invention_concept?.embodiment) {
      state.adoptedConcept = saved.invention_concept;
    }
  } catch {}
  renderer = new Software3D($("#compare-canvas"));
  bindUI();
  try {
    const [modelsResponse, statsResponse, sourcesResponse, componentsResponse, designResponse, patentsResponse, needsResponse, patternsResponse] = await Promise.all([
      fetch("/api/models"), fetch("/api/stats"), fetch("/api/sources"), fetch("/api/components"),
      fetch("/api/design-components"), fetch("/api/patents"), fetch("/api/pilot-needs"), fetch("/api/invention-patterns")
    ]);
    state.models = await modelsResponse.json();
    const stats = await statsResponse.json();
    state.stats = stats;
    state.sources = await sourcesResponse.json();
    state.components = await componentsResponse.json();
    state.designOptions = await designResponse.json();
    state.patents = await patentsResponse.json();
    state.pilotNeeds = await needsResponse.json();
    state.inventionPatterns = await patternsResponse.json();
    $("#stat-models").textContent = stats.models;
    $("#stat-sources").textContent = stats.sources;
    $("#stat-chunks").textContent = stats.chunks;
    $("#stat-patents").textContent = stats.patents;
    $("#db-source-count").textContent = stats.sources;
    renderArchiveStats();
    renderModelCards();
    populateSelects();
    renderSources();
    renderComponents();
    renderDesignStudio();
    updateAllComparators();
    await loadConstraints(state.selectedComponent);
    runSearch(state.lang === "zh" ? "A320 自动推力" : "A320 autothrust");
  } catch (error) {
    $("#search-results").innerHTML = `<div class="empty-results">${error.message}</div>`;
  }
}

document.addEventListener("DOMContentLoaded", init);
