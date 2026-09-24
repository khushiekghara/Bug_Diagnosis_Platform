"""
Milestone 2 -- Task 3: Multi-Agent Orchestration
Milestone 3 -- adds Root Cause Agent, Duplicate Detection Agent, and
Remediation Agent as Stage 2 agents, running after Triage and Log
Analysis (Stage 1).

Runs the full agent pipeline on a submitted bug report, collects every
agent's output, and assembles a single shared context object.

Design notes:
- Agents are registered in ordered lists, so adding a new agent later is
  a one-line change rather than a rewrite.
- Each agent is run defensively: if one agent raises, the orchestrator
  records the error and continues instead of failing the whole pipeline.
- Stage 2 agents run in a specific order and each one's output is added
  back into shared_context before the next Stage 2 agent runs -- this is
  required because RemediationAgent consumes RootCauseAgent's and
  DuplicateDetectionAgent's output, so those two must run first.
"""
from datetime import datetime, timezone
from typing import Dict, List

from agents.triage_agent import TriageAgent
from agents.log_analysis_agent import LogAnalysisAgent
from agents.root_cause_agent import RootCauseAgent
from agents.duplicate_detection_agent import DuplicateDetectionAgent
from agents.remediation_agent import RemediationAgent

STAGE2_CONTEXT_KEYS = {
    "RootCauseAgent": "root_cause",
    "DuplicateDetectionAgent": "duplicate_detection",
    "RemediationAgent": "remediation",
}


class AgentOrchestrator:
    def __init__(self):
        self.stage1_agents = [
            TriageAgent(),
            LogAnalysisAgent(),
        ]
        self.stage2_agents = [
            RootCauseAgent(),
            DuplicateDetectionAgent(),
            RemediationAgent(),
        ]

    def _run_agent_safely(self, agent, context) -> Dict:
        agent_name = agent.__class__.__name__
        try:
            return agent.run(context)
        except Exception as exc:
            return {
                "agent": agent_name,
                "error": str(exc),
                "status": "failed",
            }

    def build_summary(self, agent_outputs: Dict) -> str:
        triage = agent_outputs.get("TriageAgent", {})
        log = agent_outputs.get("LogAnalysisAgent", {})
        root_cause = agent_outputs.get("RootCauseAgent", {})
        duplicates = agent_outputs.get("DuplicateDetectionAgent", {})
        remediation = agent_outputs.get("RemediationAgent", {})

        parts = []

        if triage and "severity" in triage:
            parts.append(
                f"Classified as {triage['severity']} severity "
                f"({triage['priority']}), affecting the "
                f"{triage['affected_component']} component "
                f"with {int(triage['confidence'] * 100)}% confidence."
            )

        if log and log.get("exception_type"):
            parts.append(
                f"Log analysis identified a {log['exception_type']} "
                f"originating at {log['failure_point']}."
            )
        elif log:
            parts.append("Log analysis found no parseable exception or stack trace.")

        if root_cause and root_cause.get("root_cause_hypothesis"):
            parts.append(f"Root cause hypothesis: {root_cause['root_cause_hypothesis']}")

        if duplicates and duplicates.get("duplicate_status"):
            match_count = len(duplicates.get("matches", []))
            parts.append(
                f"Duplicate check: {duplicates['duplicate_status']} "
                f"({match_count} similar historical bug(s) found)."
            )

        if remediation and remediation.get("recommendations"):
            top_rec = remediation["recommendations"][0]
            parts.append(f"Top recommendation ({top_rec['basis']}): {top_rec['recommendation']}")

        return " ".join(parts) if parts else "No agent findings available."

    def run(self, bug_report: Dict) -> Dict:
        agent_outputs = {}

        for agent in self.stage1_agents:
            result = self._run_agent_safely(agent, bug_report)
            agent_outputs[agent.__class__.__name__] = result

        shared_context = {
            "bug_report": {
                "id": bug_report.get("id"),
                "title": bug_report.get("title"),
                "description": bug_report.get("description"),
                "stack_trace": bug_report.get("stack_trace"),
                "error_log": bug_report.get("error_log"),
            },
            "triage": agent_outputs.get("TriageAgent", {}),
            "log_analysis": agent_outputs.get("LogAnalysisAgent", {}),
        }

        for agent in self.stage2_agents:
            agent_name = agent.__class__.__name__
            result = self._run_agent_safely(agent, shared_context)
            agent_outputs[agent_name] = result

            context_key = STAGE2_CONTEXT_KEYS.get(agent_name)
            if context_key:
                shared_context[context_key] = result

        return {
            "bug_id": bug_report.get("id"),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "agents_run": list(agent_outputs.keys()),
            "agent_outputs": agent_outputs,
            "shared_context": shared_context,
            "summary": self.build_summary(agent_outputs),
        }


if __name__ == "__main__":
    import json
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    sample_bug = {
        "id": 1,
        "title": "Application crashes on tab close with video playing",
        "description": "The browser crashes intermittently when closing a tab while a video plays in the background.",
        "stack_trace": (
            'nsIFrame::Destroy() at layout/base/nsFrame.cpp:512\n'
            '  called from nsCSSFrameConstructor::ContentRemoved'
        ),
        "error_log": "",
    }

    orchestrator = AgentOrchestrator()
    result = orchestrator.run(sample_bug)
    print(json.dumps(result, indent=2))