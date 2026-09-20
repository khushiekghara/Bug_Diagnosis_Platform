"""
Milestone 2 -- Task 3: Multi-Agent Orchestration
Runs the Triage Agent and Log Analysis Agent on a submitted bug report,
collects their outputs, and assembles a single shared context object that
downstream agents (Root Cause, Duplicate Detection, Remediation) will
consume in a later milestone.

Design notes:
- Agents are registered in a list, so adding a new agent later is a
  one-line change rather than a rewrite.
- Each agent is run defensively: if one agent raises, the orchestrator
  records the error and continues instead of failing the whole pipeline.
- The output is a structured "diagnosis context" -- a single dict holding
  the original report, every agent's findings, and a combined summary.
"""
from datetime import datetime, timezone
from typing import Dict, List

from agents.triage_agent import TriageAgent
from agents.log_analysis_agent import LogAnalysisAgent


class AgentOrchestrator:
    """
    Coordinates the agent pipeline for a single bug report.
    """

    def __init__(self):
        # Stage 1 agents: these run first and produce context for later stages.
        self.stage1_agents = [
            TriageAgent(),
            LogAnalysisAgent(),
        ]
        # Stage 2 agents (Root Cause, Duplicate Detection, Remediation)
        # will be added here in Milestone 3.
        self.stage2_agents: List = []

    def _run_agent_safely(self, agent, bug_report: Dict) -> Dict:
        """Runs one agent; on failure returns a structured error instead of
        crashing the whole pipeline."""
        agent_name = agent.__class__.__name__
        try:
            return agent.run(bug_report)
        except Exception as exc:
            return {
                "agent": agent_name,
                "error": str(exc),
                "status": "failed",
            }

    def build_summary(self, agent_outputs: Dict) -> str:
        """Human-readable one-paragraph summary combining both agents."""
        triage = agent_outputs.get("TriageAgent", {})
        log = agent_outputs.get("LogAnalysisAgent", {})

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
            if log.get("affected_code_path"):
                parts.append(
                    f"Affected files: {', '.join(log['affected_code_path'][:3])}."
                )
        elif log:
            parts.append("Log analysis found no parseable exception or stack trace.")

        return " ".join(parts) if parts else "No agent findings available."

    def run(self, bug_report: Dict) -> Dict:
        """
        bug_report: dict with keys 'id', 'title', 'description',
        'stack_trace', 'error_log' (any text field may be empty).

        Returns the full diagnosis context.
        """
        agent_outputs = {}

        # --- Stage 1: run Triage and Log Analysis ---
        for agent in self.stage1_agents:
            result = self._run_agent_safely(agent, bug_report)
            agent_outputs[agent.__class__.__name__] = result

        # --- Build the shared context object ---
        # This is what downstream agents will receive in Milestone 3:
        # the original report PLUS everything stage 1 learned about it.
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

        # --- Stage 2: downstream agents (empty for now, wired for M3) ---
        for agent in self.stage2_agents:
            result = self._run_agent_safely(agent, shared_context)
            agent_outputs[agent.__class__.__name__] = result

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

    # Allow running this file directly from the backend/ folder
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    sample_bug = {
        "id": 1,
        "title": "Application crashes on login with null pointer",
        "description": "The app crashes whenever a user tries to log in after a password reset.",
        "stack_trace": (
            'Traceback (most recent call last):\n'
            '  File "app/auth.py", line 88, in login\n'
            '    user.session.refresh()\n'
            'AttributeError: NoneType object has no attribute refresh'
        ),
        "error_log": "",
    }

    orchestrator = AgentOrchestrator()
    result = orchestrator.run(sample_bug)
    print(json.dumps(result, indent=2))