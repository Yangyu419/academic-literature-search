"""Conservative ambiguity detection: ask only when a search could clearly drift."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ResearchRequest, SearchPlan


@dataclass(slots=True)
class ClarificationDecision:
    needed: bool
    score: float
    questions: list[str]
    reason: str = ""


_BROAD = {"核燃料", "nuclear fuel", "燃料", "agent", "llm agent", "人工智能", "ai", "材料", "能源", "深度学习", "machine learning"}
_TYPE_HINTS = {"论文", "期刊", "学位", "博士", "硕士", "会议", "报告", "article", "thesis", "dissertation", "review"}
_SPECIFIC_MARKERS = {"包壳", "芯块", "燃料棒", "组件", "锆合金", "辐照", "cladding", "pellet", "fuel rod", "assembly", "irradiation", "memory", "planning", "retrieval", "evaluation"}


def assess(request: ResearchRequest) -> ClarificationDecision:
    text = request.topic.strip()
    folded = text.casefold()
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9+.#-]*|[\u4e00-\u9fff]+", text)
    score = 0.0
    if folded in _BROAD or len(tokens) <= 2:
        score += 0.65
    if len(text) < 12:
        score += 0.2
    if not any(h in folded for h in _TYPE_HINTS) and request.start_year is None and request.end_year is None:
        score += 0.05
    if len(text) >= 8:
        score -= 0.15
    if any(marker.casefold() in folded for marker in _SPECIFIC_MARKERS):
        score -= 0.25
    if any(char in text for char in ("重点", "关注", "研究", "design", "focusing", "question")):
        score -= 0.25
    score = max(0.0, min(1.0, score))
    needed = score >= 0.65
    return ClarificationDecision(needed, score, _questions_for(folded) if needed else [], _reason(folded) if needed else "")


def _questions_for(topic: str) -> list[str]:
    if "核燃料" in topic or "nuclear fuel" in topic:
        return ["你希望重点研究燃料材料、芯块、包壳、燃料棒/组件、热工水力、辐照行为、事故容错燃料、燃耗、制造工艺还是堆芯设计？也可以选择综合检索。"]
    if "agent" in topic or "llm" in topic:
        return ["你希望重点研究 Agent architecture、memory、planning、tool use、multi-agent、evaluation、RAG、reasoning、computer use，还是综合综述？"]
    return ["请补充研究对象、核心研究问题或技术方向；如有需要，也请说明年份、文献类型和目标数量。"]


def _reason(topic: str) -> str:
    if topic in _BROAD:
        return "The topic matches a broad term with multiple established subfields."
    return "The topic is too short to constrain a reliable multi-source search."


def clarification_prompt(request: ResearchRequest) -> str | None:
    decision = assess(request)
    if not decision.needed:
        return None
    return "当前主题可能对应多个明显不同的研究方向。" + "\n" + "\n".join(f"{i}. {q}" for i, q in enumerate(decision.questions, 1))


def plan_requires_clarification(plan: SearchPlan) -> bool:
    return plan.clarification_needed or plan.ambiguity_score >= 0.65
