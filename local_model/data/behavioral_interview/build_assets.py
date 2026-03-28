from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
QUESTION_BANK_PATH = ROOT / "question_bank.json"
QUESTION_CATALOG_PATH = ROOT / "question_catalog.json"
GENERATED_CORPUS_PATH = ROOT / "generated_corpus.source.json"
GOLD_EVAL_PATH = ROOT / "gold_eval.json"

LEVELS = ("intern", "new_grad")
TRAIN_PROFILES = ("strong", "adequate", "weak", "missing_result", "we_language", "rambling")
EVAL_EXTRA_PROFILES = ("strong", "missing_result", "we_language", "rambling", "no_example", "emotional")

GROUP_TAGS = {
    "Leadership & Influence": ["leadership", "influence", "ownership"],
    "Conflict & Collaboration": ["collaboration", "communication", "conflict"],
    "Problem Solving & Technical Judgment": ["problem-solving", "technical-judgment", "tradeoffs"],
    "Failure & Resilience": ["resilience", "reflection", "accountability"],
    "Achievement & Impact": ["impact", "execution", "delivery"],
    "Adaptability & Growth": ["adaptability", "learning", "growth"],
}

FOLLOW_UP_BY_INTENT = {
    "clarify_situation": "Can you tighten the context and explain the core challenge in one or two sentences?",
    "clarify_task": "What exactly were you personally responsible for in that situation?",
    "clarify_action": "What did you personally do that changed the direction of the situation?",
    "clarify_result": "What happened because of your actions, and can you quantify it if possible?",
    "reduce_we_language": "I want to hear your individual contribution. Which part did you personally own?",
    "tighten_rambling": "Let's tighten the setup. What was the core challenge, and what did you do about it?",
    "reframe_no_example": "A class project, hackathon, club, internship, or research project can all work. Which related example comes closest?",
    "support_emotional": "That sounds difficult. How would you summarize how you responded and what you learned in a professional interview setting?",
    "praise_strong": "Strong answer. If you wanted to make it even sharper, what metric or reflection would you add?",
}

SCORE_TEMPLATES = {
    5: "This part is clear, specific, and interview-ready.",
    4: "This part is solid, but one more concrete detail would make it stronger.",
    3: "This part is present, but it still feels generic.",
    2: "This part is vague and needs more detail.",
    1: "This part is missing or not clear enough to help an interviewer.",
}


@dataclass(frozen=True)
class Scenario:
    question_id: str
    tags: tuple[str, ...]
    follow_up_intent: str
    intern_context: str
    new_grad_context: str
    task: str
    action: str
    result: str
    lesson: str
    weak_focus: str


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_question_bank() -> list[dict[str, Any]]:
    with QUESTION_BANK_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _make(
    question_id: str,
    tags: list[str],
    follow_up_intent: str,
    intern_context: str,
    new_grad_context: str,
    task: str,
    action: str,
    result: str,
    lesson: str,
    weak_focus: str,
) -> Scenario:
    return Scenario(
        question_id=question_id,
        tags=tuple(tags),
        follow_up_intent=follow_up_intent,
        intern_context=intern_context,
        new_grad_context=new_grad_context,
        task=task,
        action=action,
        result=result,
        lesson=lesson,
        weak_focus=weak_focus,
    )


def build_scenario(question: str, group: str) -> Scenario:
    q = question.lower()
    if "formal authority" in q:
        return _make("lead_without_authority", ["leadership", "alignment", "initiative"], "clarify_action",
                     "our software engineering capstone team drifted after the first sprint because nobody owned cross-team coordination",
                     "a release working group was slipping because engineers were waiting on each other and no single person owned the delivery rhythm",
                     "create clarity and momentum without an official lead title",
                     "I created a lightweight task board, proposed short unblocker check-ins, and used those meetings to surface ownership gaps early",
                     "the team recovered the schedule, reduced duplicate work, and delivered the agreed scope on time",
                     "leadership often means creating structure before anyone asks for it", "action")
    if "influence a decision" in q:
        return _make("influence_decision", ["influence", "technical-judgment", "stakeholder-management"], "clarify_action",
                     "my team wanted to change the database schema right before a demo even though the API integration was already stable",
                     "a cross-functional team wanted to launch a brittle implementation quickly, but I believed it would create avoidable operational risk",
                     "present a different direction without creating unnecessary conflict",
                     "I gathered examples of the regression risk, framed the tradeoffs in terms of delivery impact, and proposed a safer phased alternative",
                     "the group adopted the phased approach, met the deadline, and avoided the failure mode I had raised",
                     "influence works best when I anchor disagreement in evidence and shared goals", "action")
    if "mentored or coached" in q:
        return _make("mentor_teammate", ["mentorship", "communication", "growth"], "clarify_result",
                     "a teammate in my project group was struggling to debug asynchronous code and had started avoiding backend tasks",
                     "a junior teammate on a delivery squad was hesitant to touch an unfamiliar service and kept getting blocked on the same kind of issue",
                     "help them grow without taking over the work",
                     "I paired on one debugging session, broke the process into a repeatable checklist, and reviewed the next change with them after they tried it independently",
                     "they started solving similar issues on their own and the team depended less on me for the same class of problem",
                     "good mentoring builds confidence and independence, not dependence", "result")
    if "rally a team" in q:
        return _make("rally_team_goal", ["leadership", "motivation", "delivery"], "clarify_result",
                     "our hackathon team had a working core demo but morale dropped when a late integration failed the night before judging",
                     "a product team had to hit an aggressive launch window even after an important dependency slipped",
                     "keep the team focused on a realistic version of success",
                     "I reframed the goal around the must-have experience, cut nonessential work, and kept everyone aligned on the next few hours of execution",
                     "we delivered a polished core experience instead of a broken ambitious one, and the team stayed engaged through the finish",
                     "teams rally when the goal becomes concrete and emotionally believable", "result")
    if "outside your role" in q:
        return _make("ownership_outside_role", ["ownership", "initiative", "cross-functional"], "clarify_result",
                     "a testing gap was repeatedly slowing our class project even though QA was nobody's formal responsibility",
                     "a recurring support issue was frustrating internal users, but it sat between engineering and operations and nobody owned it directly",
                     "step in without creating territorial friction",
                     "I proposed a narrow fix, built the first version myself, and documented the handoff so the team could keep using it",
                     "the repeated issue stopped consuming the same time every week and the team adopted the new process",
                     "taking ownership outside my role works when I reduce friction instead of creating more", "result")
    if "technical decision" in q and "disagreed" in q:
        return _make("disagree_technical_decision", ["technical-judgment", "conflict", "tradeoffs"], "clarify_action",
                     "a teammate wanted to remove validation checks to speed up delivery right before our demo",
                     "a design review proposed a shortcut that would have shipped faster but created support and reliability risk",
                     "challenge the decision without turning it personal",
                     "I used concrete examples of the failure mode, compared the time tradeoff to the recovery cost, and suggested a smaller safe compromise",
                     "the team kept the critical safeguards, still hit the deadline, and avoided the class of bug I had highlighted",
                     "I try to disagree on tradeoffs, not on people", "action")
    if "conflict with a coworker" in q:
        return _make("coworker_conflict", ["conflict", "communication", "collaboration"], "clarify_result",
                     "a teammate and I kept stepping on each other's changes because our task boundaries were unclear",
                     "a coworker and I had tension around ownership because we were making overlapping changes to the same release area",
                     "resolve the conflict while protecting delivery",
                     "I asked for a direct conversation, clarified responsibilities, and agreed on a handoff and review process for overlapping work",
                     "the tension dropped, the workstream became smoother, and we stopped reworking each other's changes",
                     "conflict improves when I replace assumptions with explicit agreements", "result")
    if "difficult stakeholder" in q:
        return _make("difficult_stakeholder", ["stakeholder-management", "communication", "alignment"], "clarify_action",
                     "a student organization sponsor kept changing expectations for a project portal without explaining the priority behind each request",
                     "a nontechnical stakeholder wanted frequent changes but was not seeing the engineering tradeoffs or sequencing constraints",
                     "understand the real concern and reset expectations",
                     "I translated the requests into priorities, walked through the impact of each change, and proposed a ranked roadmap instead of reacting request by request",
                     "the stakeholder stopped changing direction every few days and we delivered the highest-value improvements first",
                     "difficult stakeholders become easier when I surface the real priorities underneath the requests", "action")
    if "critical feedback to a peer" in q:
        return _make("critical_feedback_peer", ["feedback", "communication", "teamwork"], "clarify_action",
                     "a teammate kept merging changes without tests, which caused avoidable breakages in our shared project branch",
                     "a peer on my team was shipping code quickly but skipping an agreed quality step that created cleanup work for others",
                     "raise the issue respectfully and make it actionable",
                     "I gave the feedback privately, used recent examples, and suggested a lightweight checklist so the ask felt concrete rather than personal",
                     "the quality issue improved and the peer responded positively because the feedback was specific and respectful",
                     "critical feedback lands better when it is private, concrete, and tied to team impact", "action")
    if "wasn't pulling their weight" in q:
        return _make("underperforming_teammate", ["accountability", "collaboration", "support"], "clarify_action",
                     "one teammate stopped finishing assigned tasks during our group project and the rest of us were quietly covering for it",
                     "a team member repeatedly missed commitments on a shared deliverable and the impact started spreading to everyone else",
                     "address the issue fairly before it damaged the whole team",
                     "I checked in first to understand the blocker, then reset expectations and narrowed the next commitment to something concrete and observable",
                     "either the teammate re-engaged on a realistic scope or we escalated earlier instead of absorbing the problem silently",
                     "accountability works best when I combine empathy with explicit expectations", "action")
    if "hardest technical problem" in q:
        return _make("hardest_technical_problem", ["debugging", "systems", "problem-solving"], "clarify_result",
                     "our project had a race condition that only appeared under parallel requests and none of our basic tests reproduced it",
                     "a production-adjacent service had an intermittent data inconsistency issue that was hard to reproduce and easy to dismiss",
                     "find the real root cause instead of treating the symptom",
                     "I reduced the problem to a smaller repro, added targeted logging, and isolated the timing assumption that was breaking under load",
                     "the fix removed the intermittent failure and gave the team a clearer mental model of the system",
                     "hard problems usually get easier once I make the failure reproducible", "result")
    if "incomplete information" in q:
        return _make("decision_incomplete_info", ["ambiguity", "technical-judgment", "risk-management"], "clarify_action",
                     "we had to choose an implementation approach before we had complete user feedback or enough time for a full spike",
                     "I needed to make a technical decision even though usage patterns and stakeholder expectations were still evolving",
                     "move forward with enough confidence while limiting downside",
                     "I identified the assumptions that mattered most, chose the option with the safest rollback path, and documented what signal would trigger a change",
                     "we moved forward without blocking delivery and still had a clear path to adjust when new information arrived",
                     "with incomplete information, I try to optimize for reversibility and learning speed", "action")
    if "technical debt" in q:
        return _make("technical_debt_tradeoff", ["technical-debt", "delivery", "tradeoffs"], "clarify_action",
                     "our project needed one more feature before demo day, but the code path we wanted to extend was already messy and fragile",
                     "the team needed to ship an important capability, but a quick implementation would have deepened debt in a risky part of the codebase",
                     "balance delivery pressure against long-term maintainability",
                     "I scoped the minimum clean-up needed to ship safely, deferred the noncritical refactor, and documented the debt that still remained",
                     "we shipped on time without creating the worst version of the long-term maintenance problem",
                     "the right debt decision is rarely yes or no; it is about how much risk to buy today", "action")
    if "identified a problem before it became critical" in q:
        return _make("identified_problem_early", ["proactivity", "monitoring", "risk-management"], "clarify_result",
                     "I noticed a growing pattern of flaky tests and duplicate failures before the project team treated it as a real issue",
                     "I saw an early signal in logs and support complaints that suggested a reliability problem was forming",
                     "investigate before the issue became urgent",
                     "I traced the pattern back to one common dependency, raised it early, and proposed a preventive fix before the next milestone",
                     "we avoided a more visible failure later and saved time that would have gone into reactive cleanup",
                     "small signals are often worth following before everyone agrees they matter", "result")
    if "simplified a complex system or process" in q:
        return _make("simplified_system", ["simplification", "process", "impact"], "clarify_result",
                     "our team had a manual release checklist spread across messages, docs, and memory, which made every deployment stressful",
                     "a recurring engineering process had become too complex, slow, and dependent on tribal knowledge",
                     "remove unnecessary complexity without losing the important safeguards",
                     "I mapped the workflow end to end, removed redundant steps, and turned the essential parts into one documented path",
                     "the process became faster, easier to onboard to, and less likely to fail because of missed handoffs",
                     "simplification is valuable when it preserves the guardrails that actually matter", "result")
    if "project that failed" in q:
        return _make("project_failed", ["failure", "reflection", "ownership"], "clarify_result",
                     "our team built too much before validating the core user need, and the project did not land the way we expected",
                     "a project I worked on missed its core goal because we optimized for implementation speed before validating assumptions",
                     "own what I could have done differently and learn from it",
                     "I reviewed where our assumptions went unchecked, identified the decision points we rushed past, and changed how I approached the next project",
                     "the failure itself stood, but the lesson improved how I scoped and validated future work",
                     "good failure stories show ownership and changed behavior, not blame", "result")
    if "missed a deadline" in q:
        return _make("missed_deadline", ["deadline", "communication", "accountability"], "clarify_action",
                     "I underestimated integration work on a class project and realized too late that I would miss the milestone I had committed to",
                     "I owned a deliverable that slipped because I underestimated the dependency and did not surface the risk early enough",
                     "mitigate the miss responsibly and improve my planning",
                     "I communicated the risk as soon as I understood it, cut the scope to the most important pieces, and changed how I estimated similar work afterward",
                     "the deadline miss still happened, but the impact was contained and my future planning improved",
                     "missing a deadline matters less than how quickly and honestly I respond once I see it", "action")
    if "harsh feedback" in q or "received harsh feedback" in q:
        return _make("harsh_feedback", ["feedback", "growth", "communication"], "clarify_result",
                     "my manager told me my updates were too detailed and slowed decision-making because the blockers were buried",
                     "I received direct feedback that my communication style made it harder for the team to act quickly",
                     "process the feedback without defensiveness and change my behavior",
                     "I asked for examples, changed the format, and checked the next few updates with the reviewer to make sure the improvement was real",
                     "the feedback translated into clearer communication and faster decisions from the team",
                     "difficult feedback is most useful when I turn it into a repeatable habit change", "result")
    if "regret" in q and "technical decision" in q:
        return _make("regretted_decision", ["reflection", "technical-judgment", "learning"], "clarify_action",
                     "I chose a shortcut implementation for a project because it looked faster, but it created cleanup work later",
                     "I made a technical decision that optimized for speed but cost the team flexibility and cleanup time later",
                     "explain the original logic honestly and show what I learned",
                     "I revisited the assumptions, identified why the shortcut was attractive in the moment, and changed how I now evaluate reversibility and maintenance cost",
                     "I would still explain the context, but I would choose the more maintainable option next time",
                     "regret stories land better when I show honest reasoning and changed judgment", "action")
    if "didn't go as planned" in q:
        return _make("midproject_change", ["adaptability", "execution", "resilience"], "clarify_action",
                     "midway through the project, a core dependency failed and our original plan stopped making sense",
                     "a project changed shape midstream because an assumption or dependency broke, and we had to reorient quickly",
                     "reassess the plan and protect the most valuable outcome",
                     "I re-scoped the work, reset priorities with the team, and communicated the revised plan clearly instead of pretending the original one still worked",
                     "we delivered a narrower but reliable result instead of missing the milestone entirely",
                     "adaptability is strongest when I update the plan openly instead of clinging to a broken one", "action")
    if "proudest technical achievement" in q:
        return _make("proudest_technical_achievement", ["achievement", "technical-depth", "impact"], "clarify_result",
                     "I built the most reliable part of our capstone demo after several earlier attempts had failed under realistic load",
                     "I led a technical improvement that solved a problem the team had been working around for weeks",
                     "show why the achievement was hard and why it mattered",
                     "I broke the problem down, chose a practical design, and kept iterating until it held up under the real usage pattern",
                     "the final result was stable, visible, and clearly improved the product or user experience",
                     "the best achievement stories connect technical difficulty to real impact", "result")
    if "under pressure or tight constraints" in q:
        return _make("deliver_under_pressure", ["delivery", "prioritization", "execution"], "clarify_result",
                     "our team had one night left to stabilize the demo after a late integration failure",
                     "we had a fixed delivery deadline and fewer resources than expected, so every decision had to favor the critical path",
                     "deliver the core outcome without getting distracted by lower-value work",
                     "I cut scope, protected the essential flow, and coordinated the team around the smallest set of tasks that would make the result credible",
                     "we delivered something polished enough to meet the moment instead of missing it while chasing completeness",
                     "under pressure, clear priorities matter more than heroic effort", "result")
    if "above and beyond" in q:
        return _make("above_and_beyond", ["ownership", "initiative", "impact"], "clarify_result",
                     "after finishing my assigned backend work, I saw that onboarding the rest of the team was still taking too long",
                     "I noticed a repeated pain point beyond my assigned scope and chose to solve it because the team kept losing time to it",
                     "do extra work that materially helps, not just work that looks impressive",
                     "I built a small internal tool or guide that removed the repeated friction and documented how to use it",
                     "the team moved faster afterward because the extra work solved a real bottleneck",
                     "going above and beyond is strongest when the extra effort solves the right problem", "result")
    if "measurable impact on the business" in q:
        return _make("business_impact", ["impact", "metrics", "stakeholder-value"], "clarify_result",
                     "a recurring issue in our student project workflow kept wasting time and causing avoidable rework",
                     "my work improved a process tied to internal stakeholders, time savings, or reliability in a way the team could actually measure",
                     "connect technical work to a metric that matters",
                     "I identified the root cause, changed the workflow or system behavior, and tracked the before-and-after effect",
                     "the result was measurable in time saved, reliability improved, or incidents reduced",
                     "impact stories are stronger when the metric reflects a stakeholder problem, not just technical elegance", "result")
    if "improved a process or system significantly" in q:
        return _make("improved_process", ["process", "impact", "execution"], "clarify_result",
                     "a repeated setup or release task was wasting effort every week and confusing newer teammates",
                     "an internal workflow had become slow and fragile, and the team had normalized the pain even though it was fixable",
                     "improve the system in a way that lasts beyond one sprint",
                     "I mapped the friction, automated or simplified the highest-leverage step, and documented the new path",
                     "the process became faster, easier to repeat, and less dependent on one person remembering hidden steps",
                     "significant improvements usually come from fixing repeated friction, not one-off heroics", "result")
    if "learn a new technology quickly" in q:
        return _make("learn_new_technology", ["learning", "adaptability", "delivery"], "clarify_result",
                     "our project needed Docker to stop environment drift, but I had never used it before",
                     "a delivery goal required me to get productive in a new tool quickly instead of learning it passively",
                     "learn only what I needed to unblock delivery and then document it well",
                     "I focused on the official docs, built the smallest working version, and wrote down the repeatable setup for others",
                     "the team got unblocked and the new tool became immediately useful instead of staying theoretical",
                     "I learn new tools fastest when I tie them to a concrete delivery problem", "result")
    if "priorities shifted dramatically" in q:
        return _make("priorities_shifted", ["adaptability", "prioritization", "communication"], "clarify_action",
                     "mid-sprint, a higher-priority user issue forced us to pause planned feature work",
                     "our sprint priorities changed quickly because new information made the original plan less valuable",
                     "re-prioritize cleanly without leaving everyone confused",
                     "I helped re-sequence the work, explained what was changing and why, and protected the most important deliverables first",
                     "the team adjusted faster because the new priorities were explicit and the tradeoffs were communicated clearly",
                     "priority shifts feel manageable once the reasoning and next steps are both visible", "action")
    if "joined a new team or codebase" in q:
        return _make("join_new_codebase", ["ramp-up", "learning", "execution"], "clarify_action",
                     "I joined a new codebase shortly before I was expected to contribute to a meaningful milestone",
                     "I joined a new team and needed to become useful quickly without pretending I understood the system already",
                     "ramp up fast while building trust and avoiding careless mistakes",
                     "I mapped the main flows, asked targeted questions, followed one feature end to end, and chose a first task that was small but real",
                     "I became productive quickly and my first contribution landed without needing a risky amount of rework",
                     "fast ramp-up comes from targeted learning, not reading everything equally", "action")
    if "change your approach based on new information" in q:
        return _make("change_approach_new_info", ["adaptability", "judgment", "learning"], "clarify_action",
                     "I started with one implementation approach, but new evidence showed it was solving the wrong problem",
                     "new data or stakeholder input made my original plan less effective than I first thought",
                     "pivot early enough that the new information still mattered",
                     "I reassessed the goal, changed the implementation strategy, and explained the pivot so the team understood the reason behind it",
                     "the revised approach better matched the real problem and saved us from doubling down on the wrong path",
                     "good adaptation means changing the plan when the evidence changes, not when it is too late", "action")
    if "outside your comfort zone" in q:
        return _make("outside_comfort_zone", ["growth", "learning", "adaptability"], "clarify_result",
                     "I had to take on a part of the stack I had not worked in before because the team needed coverage there",
                     "I stepped into an unfamiliar domain because the project needed someone to move it forward and waiting was worse than learning",
                     "deliver despite being uncomfortable and learn quickly enough to be useful",
                     "I broke the problem into smaller steps, used documentation and feedback loops, and kept validating my progress instead of guessing silently",
                     "I produced a useful result in an unfamiliar area and expanded what I could take on later",
                     "comfort zones grow fastest when I stay honest about what I do not know and keep feedback loops short", "result")
    return _make(slugify(question)[:48], GROUP_TAGS.get(group, ["behavioral"]), "clarify_action",
                 "I handled a meaningful project challenge that mattered to my team",
                 "I handled a meaningful work challenge that required judgment and communication",
                 "own a clear piece of the problem",
                 "I clarified the priorities, took action, and kept the relevant people aligned",
                 "the work moved forward and the team benefited from the clearer execution",
                 "clear ownership and reflection make behavioral stories stronger", "action")


def build_catalog_entry(raw: dict[str, Any]) -> dict[str, Any]:
    scenario = build_scenario(raw["question"], raw["category"])
    return {
        "question_id": scenario.question_id,
        "group": raw["category"],
        "tags": list(dict.fromkeys([*GROUP_TAGS.get(raw["category"], []), *scenario.tags])),
        "question": raw["question"],
        "ideal_answer_beats": raw["ideal_answer_beats"],
    }


def compose_strong_answer(question: str, scenario: Scenario, level: str) -> str:
    context = scenario.intern_context if level == "intern" else scenario.new_grad_context
    level_prefix = "In a recent software engineering project" if level == "intern" else "During my internship"
    return (
        f"{level_prefix}, {context}. "
        f"My responsibility was to {scenario.task}. "
        f"{scenario.action}. "
        f"As a result, {scenario.result}. "
        f"The experience taught me that {scenario.lesson}."
    )


def strip_result(answer: str) -> str:
    return re.sub(r"As a result, .*?(?:\.|$)", "", answer).replace("  ", " ").strip()


def replace_i_with_we(answer: str) -> str:
    replacements = {
        " I ": " we ",
        " My ": " Our ",
        " my ": " our ",
        " me ": " us ",
        "I ": "We ",
    }
    output = f" {answer} "
    for old, new in replacements.items():
        output = output.replace(old, new)
    return output.strip()


def compose_profile_answer(question: str, scenario: Scenario, level: str, profile: str) -> str:
    strong = compose_strong_answer(question, scenario, level)
    if profile == "strong":
        return strong
    if profile == "adequate":
        return re.sub(r"The experience taught me.*", "", strong).replace("As a result, ", "The result was that ").strip()
    if profile == "missing_result":
        return strip_result(strong)
    if profile == "we_language":
        return replace_i_with_we(strip_result(strong) + " We delivered a good outcome for the team.")
    if profile == "rambling":
        return (
            "To give a little background, this happened during a period when several priorities were moving at once and there were more details than anyone really needed in the interview. "
            + strong
            + " Looking back, I would probably tell the story more directly."
        )
    if profile == "weak":
        return f"I have dealt with something similar before. {question.split('?')[0]}. I tried to help where I could and things turned out okay in the end."
    if profile == "no_example":
        return "I do not have a perfect example of that, but I think I would stay calm, communicate clearly, and try to solve the problem with the team."
    if profile == "emotional":
        return f"This was a difficult one for me emotionally. {strip_result(strong)} At the time I felt stressed and disappointed, but I tried to handle it professionally and learn from it."
    if profile == "short":
        return "I ran into a tough situation, adjusted quickly, and it ended well."
    return strong


def profile_scores(profile: str, weak_focus: str) -> dict[str, int]:
    if profile == "strong":
        return {"situation": 5, "task": 5, "action": 5, "result": 5}
    if profile == "adequate":
        return {"situation": 4, "task": 4, "action": 4, "result": 3}
    if profile == "weak":
        scores = {"situation": 2, "task": 2, "action": 2, "result": 2}
        scores[weak_focus] = 1
        return scores
    if profile == "missing_result":
        return {"situation": 4, "task": 4, "action": 4, "result": 1}
    if profile == "we_language":
        return {"situation": 4, "task": 2, "action": 2, "result": 3}
    if profile == "rambling":
        return {"situation": 2, "task": 3, "action": 4, "result": 3}
    if profile == "no_example":
        return {"situation": 1, "task": 1, "action": 2, "result": 1}
    if profile == "emotional":
        return {"situation": 3, "task": 3, "action": 3, "result": 2}
    if profile == "short":
        return {"situation": 2, "task": 2, "action": 2, "result": 2}
    return {"situation": 3, "task": 3, "action": 3, "result": 3}


def follow_up_intent(profile: str, weak_focus: str) -> str:
    if profile == "missing_result":
        return "clarify_result"
    if profile == "we_language":
        return "reduce_we_language"
    if profile == "rambling":
        return "tighten_rambling"
    if profile == "no_example":
        return "reframe_no_example"
    if profile == "emotional":
        return "support_emotional"
    if profile == "strong":
        return "praise_strong"
    if weak_focus == "situation":
        return "clarify_situation"
    if weak_focus == "task":
        return "clarify_task"
    if weak_focus == "result":
        return "clarify_result"
    return "clarify_action"


def build_feedback(question: str, scenario: Scenario, level: str, profile: str) -> dict[str, Any]:
    scores = profile_scores(profile, scenario.weak_focus)
    intent = follow_up_intent(profile, scenario.weak_focus)
    improved_answer = compose_strong_answer(question, scenario, level)
    strengths = []
    improvements = []

    if scores["action"] >= 4:
        strengths.append("You describe what you personally did instead of hiding behind the team.")
    if scores["situation"] >= 4:
        strengths.append("The setup is easy to follow and clearly tied to a real engineering context.")
    if scores["result"] >= 4:
        strengths.append("The answer closes with a concrete outcome instead of stopping at effort.")
    if not strengths:
        strengths.append("The example is at least directionally related to the question.")

    if profile == "missing_result":
        improvements.append("Add the final outcome and, if possible, one measurable result.")
    if profile == "we_language":
        improvements.append("Shift the action into first-person language so your role is unmistakable.")
    if profile == "rambling":
        improvements.append("Shorten the setup and get to the challenge faster.")
    if profile == "weak":
        improvements.append("Replace general claims with one specific story and a clear outcome.")
    if profile == "no_example":
        improvements.append("Pick a real story from a project, internship, hackathon, or class instead of answering hypothetically.")
    if profile == "emotional":
        improvements.append("Keep the emotional context, but spend more time on how you responded and what changed.")

    for part, score in scores.items():
        if score <= 3:
            improvements.append(f"Strengthen the {part} portion with more concrete detail.")
    if not improvements:
        improvements.append("Add one metric or reflection if you want to make the answer even sharper.")

    if profile == "strong":
        overall = "Strong answer. The ownership, actions, and impact are all clear."
        interviewer_reply = "Great answer. You clearly articulated your contribution and the outcome."
    elif profile == "adequate":
        overall = "This is a solid foundation, but it would be stronger with a clearer result and a bit more precision."
        interviewer_reply = "Good answer. I can follow the story, and one more concrete outcome would make it stronger."
    elif profile == "missing_result":
        overall = "The story is credible, but it stops before the interviewer learns what changed because of your actions."
        interviewer_reply = "You explained the situation and action well. Now close the loop with the outcome."
    elif profile == "we_language":
        overall = "The answer sounds collaborative, but your individual ownership is still blurry."
        interviewer_reply = "I can hear the team effort, but I want to understand what you personally drove."
    elif profile == "rambling":
        overall = "There is a useful example here, but the setup is longer than it needs to be and dilutes the key point."
        interviewer_reply = "There is a solid story here. Let's tighten it so the key action lands faster."
    elif profile == "no_example":
        overall = "This does not answer the question directly because it stays hypothetical."
        interviewer_reply = "That answer is thoughtful, but interviewers usually want a real example."
    elif profile == "emotional":
        overall = "The answer has real emotional weight, but it needs a clearer professional summary of your response and learning."
        interviewer_reply = "That sounds like a difficult experience. Let's shape it into a concise interview story."
    else:
        overall = "The answer is too general to be convincing yet."
        interviewer_reply = "The theme fits, but I need a more specific story to evaluate it well."

    return {
        "interviewer_reply": interviewer_reply,
        "overall": overall,
        "follow_up_intent": intent,
        "star": {
            part: {"score": score, "feedback": SCORE_TEMPLATES[score]}
            for part, score in scores.items()
        },
        "strengths": list(dict.fromkeys(strengths)),
        "improvements": list(dict.fromkeys(improvements))[:4],
        "improved_answer": improved_answer,
    }


def build_family(question_entry: dict[str, Any], level: str) -> dict[str, Any]:
    scenario = build_scenario(question_entry["question"], question_entry["category"])
    family_id = f"{scenario.question_id}--{level}"
    variants = []
    for profile in TRAIN_PROFILES:
        answer = compose_profile_answer(question_entry["question"], scenario, level, profile)
        feedback = build_feedback(question_entry["question"], scenario, level, profile)
        variants.append(
            {
                "answer_profile": profile,
                "quality": profile if profile in {"strong", "weak"} else "mixed",
                "candidate_answer": answer,
                "follow_up_question": FOLLOW_UP_BY_INTENT[feedback["follow_up_intent"]],
                "feedback": feedback,
            }
        )
    return {
        "question_family_id": family_id,
        "question_id": scenario.question_id,
        "source_kind": "synthetic_template_v2",
        "group": question_entry["category"],
        "tags": list(dict.fromkeys([*GROUP_TAGS.get(question_entry["category"], []), *scenario.tags])),
        "level": level,
        "question": question_entry["question"],
        "variants": variants,
    }


def build_eval_case(
    question_entry: dict[str, Any],
    level: str,
    profile: str,
    case_index: int,
    case_label: str,
) -> dict[str, Any]:
    scenario = build_scenario(question_entry["question"], question_entry["category"])
    answer = compose_profile_answer(question_entry["question"], scenario, level, profile)
    feedback = build_feedback(question_entry["question"], scenario, level, profile)
    return {
        "eval_case_id": f"{scenario.question_id}--{level}--{profile}--{case_label}--{case_index}",
        "question_id": scenario.question_id,
        "question_family_id": f"{scenario.question_id}--{level}",
        "group": question_entry["category"],
        "tags": list(dict.fromkeys([*GROUP_TAGS.get(question_entry["category"], []), *scenario.tags])),
        "level": level,
        "answer_profile": profile,
        "question": question_entry["question"],
        "candidate_answer": answer,
        "expected_follow_up_intent": feedback["follow_up_intent"],
        "expected_scores": {part: score_payload["score"] for part, score_payload in feedback["star"].items()},
        "notes": {"source_kind": "synthetic_eval_v1", "overall": feedback["overall"]},
    }


def build_assets() -> None:
    question_bank = load_question_bank()
    question_catalog = [build_catalog_entry(item) for item in question_bank]
    generated_families = [build_family(item, level) for item in question_bank for level in LEVELS]

    eval_cases: list[dict[str, Any]] = []
    for idx, item in enumerate(question_bank):
        eval_cases.append(build_eval_case(item, "intern", "strong", idx, "baseline"))
        eval_cases.append(build_eval_case(item, "new_grad", "missing_result", idx, "missing_result"))
        eval_cases.append(
            build_eval_case(
                item,
                "intern",
                EVAL_EXTRA_PROFILES[idx % len(EVAL_EXTRA_PROFILES)],
                idx,
                "edge",
            )
        )

    with QUESTION_CATALOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(question_catalog, f, indent=2)
    with GENERATED_CORPUS_PATH.open("w", encoding="utf-8") as f:
        json.dump(generated_families, f, indent=2)
    with GOLD_EVAL_PATH.open("w", encoding="utf-8") as f:
        json.dump(eval_cases, f, indent=2)

    print(
        json.dumps(
            {
                "question_catalog": len(question_catalog),
                "question_families": len(generated_families),
                "train_profiles_per_family": len(TRAIN_PROFILES),
                "total_generated_examples": len(generated_families) * len(TRAIN_PROFILES),
                "gold_eval_cases": len(eval_cases),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    build_assets()
