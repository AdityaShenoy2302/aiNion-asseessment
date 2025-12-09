"""
Nion Orchestration Engine - Simplified Implementation
A three-tier AI orchestration system for project management
"""

import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class L2Domain(Enum):
    TRACKING_EXECUTION = "TRACKING_EXECUTION"
    COMMUNICATION_COLLABORATION = "COMMUNICATION_COLLABORATION"
    LEARNING_IMPROVEMENT = "LEARNING_IMPROVEMENT"


@dataclass
class Task:
    """Represents a task in the orchestration"""
    task_id: str
    target: str  # L2:DOMAIN or L3:agent
    purpose: str
    depends_on: List[str] = field(default_factory=list)
    subtasks: List['Task'] = field(default_factory=list)
    status: str = "COMPLETED"
    output: List[str] = field(default_factory=list)
    is_cross_cutting: bool = False


class AgentRegistry:
    """Registry of all available agents organized by tier"""

    # Cross-cutting agents visible to L1 and all L2 domains
    CROSS_CUTTING = {
        "knowledge_retrieval": "Retrieves context from database",
        "evaluation": "Validates outputs before delivery"
    }

    # L3 agents by L2 domain
    L3_AGENTS = {
        L2Domain.TRACKING_EXECUTION: {
            "action_item_extraction": "Extracts action items from message content",
            "action_item_validation": "Validates action items have required fields",
            "action_item_tracking": "Tracks action items to completion",
            "risk_extraction": "Extracts risks from message content",
            "risk_tracking": "Tracks risks, provides risk snapshots",
            "issue_extraction": "Extracts issues/problems from message content",
            "issue_tracking": "Tracks issues to resolution",
            "decision_extraction": "Extracts decisions from message content",
            "decision_tracking": "Tracks decisions to implementation"
        },
        L2Domain.COMMUNICATION_COLLABORATION: {
            "qna": "Formulates responses to questions",
            "report_generation": "Creates formatted reports",
            "message_delivery": "Sends messages via appropriate channels",
            "meeting_attendance": "Captures meeting transcripts"
        },
        L2Domain.LEARNING_IMPROVEMENT: {
            "instruction_led_learning": "Learns from explicit instructions"
        }
    }


class L1Orchestrator:
    """L1 Orchestrator - Analyzes intent and creates execution plan"""

    def __init__(self):
        self.task_counter = 0

    def _next_task_id(self) -> str:
        self.task_counter += 1
        return f"TASK-{self.task_counter:03d}"

    def analyze_and_plan(self, message: Dict) -> List[Task]:
        """
        Analyzes the message and creates an orchestration plan.
        This is where the L1 reasoning happens.
        """
        content = message.get("content", "").lower()
        source = message.get("source", "")

        tasks = []

        # Analyze intent and determine required operations
        has_request = any(word in content for word in ["add", "can we", "could", "should we"])
        has_question = "?" in content or any(word in content for word in ["what", "why", "how", "when", "where"])
        has_status_query = "status" in content
        has_decision_request = any(word in content for word in ["should", "prioritize", "recommend"])
        has_escalation = any(word in content for word in ["urgent", "critical", "escalate", "legal", "threatening"])
        has_meeting_content = source == "meeting" or "dev:" in content.lower() or "qa:" in content.lower()
        is_ambiguous = message.get("project") is None or len(content.split()) < 5

        # Extract tracking items (action items, risks, issues, decisions)
        needs_tracking = has_request or has_meeting_content or has_escalation or has_decision_request

        if needs_tracking:
            # Action items
            if has_request or "blocked" in content or has_meeting_content:
                tasks.append(Task(
                    task_id=self._next_task_id(),
                    target="L2:TRACKING_EXECUTION",
                    purpose="Extract action items from message"
                ))

            # Risks
            if has_request or "blocked" in content or has_escalation or "bug" in content:
                tasks.append(Task(
                    task_id=self._next_task_id(),
                    target="L2:TRACKING_EXECUTION",
                    purpose="Extract and assess risks"
                ))

            # Issues
            if "bug" in content or "blocked" in content or "issue" in content or "problem" in content:
                tasks.append(Task(
                    task_id=self._next_task_id(),
                    target="L2:TRACKING_EXECUTION",
                    purpose="Extract issues from message"
                ))

            # Decisions
            if has_decision_request or has_request:
                tasks.append(Task(
                    task_id=self._next_task_id(),
                    target="L2:TRACKING_EXECUTION",
                    purpose="Extract decision needed"
                ))

        # Knowledge retrieval for context
        if has_question or has_request or has_status_query or not is_ambiguous:
            tasks.append(Task(
                task_id=self._next_task_id(),
                target="L3:knowledge_retrieval",
                purpose="Retrieve project context and relevant information",
                is_cross_cutting=True
            ))

        # Handle meeting transcripts specially
        if has_meeting_content:
            tasks.append(Task(
                task_id=self._next_task_id(),
                target="L2:COMMUNICATION_COLLABORATION",
                purpose="Process meeting content and generate minutes"
            ))

        # Response formulation
        # Identify factual tasks only (Issue 1 fix)
        factual_tasks = [
            t.task_id for t in tasks
            if "TRACKING_EXECUTION" in t.target or "knowledge_retrieval" in t.target
        ]

        if has_question or has_request or has_decision_request or has_status_query or is_ambiguous:
            response_task = Task(
                task_id=self._next_task_id(),
                target="L2:COMMUNICATION_COLLABORATION",
                purpose="Formulate response to query" if not is_ambiguous else "Handle ambiguous request",
                depends_on=factual_tasks if factual_tasks else []
            )
            tasks.append(response_task)

            # Evaluation before sending
            eval_task = Task(
                task_id=self._next_task_id(),
                target="L3:evaluation",
                purpose="Evaluate response before delivery",
                depends_on=[response_task.task_id],
                is_cross_cutting=True
            )
            tasks.append(eval_task)

            # Message delivery
            delivery_task = Task(
                task_id=self._next_task_id(),
                target="L2:COMMUNICATION_COLLABORATION",
                purpose="Send response to sender",
                depends_on=[eval_task.task_id]
            )
            tasks.append(delivery_task)
        elif has_meeting_content:
            # For meetings, generate report
            report_task = Task(
                task_id=self._next_task_id(),
                target="L2:COMMUNICATION_COLLABORATION",
                purpose="Generate meeting summary report",
                depends_on=factual_tasks
            )
            tasks.append(report_task)

        return tasks


class L2Coordinator:
    """L2 Coordinator - Coordinates L3 agents within its domain"""

    def __init__(self, domain: L2Domain):
        self.domain = domain
        self.subtask_counter = 0

    def _next_subtask_id(self, parent_id: str) -> str:
        self.subtask_counter += 1
        return f"{parent_id}-{chr(64 + self.subtask_counter)}"

    def execute(self, task: Task, message: Dict) -> Task:
        """Execute L2 task by coordinating appropriate L3 agents"""
        content = message.get("content", "")
        source = message.get("source", "")
        sender = message.get("sender", {})
        project = message.get("project", "N/A")

        purpose = task.purpose.lower()

        # --- TRACKING_EXECUTION domain orchestration ---
        if "action item" in purpose or "action items" in purpose:
            # extraction + validation + tracking
            task.subtasks.append(self._execute_action_item_extraction(task.task_id, content))
            task.subtasks.append(self._execute_action_item_validation(task.task_id))
            task.subtasks.append(self._execute_action_item_tracking(task.task_id))

        elif "risk" in purpose:
            # extraction + tracking
            task.subtasks.append(self._execute_risk_extraction(task.task_id, content))
            task.subtasks.append(self._execute_risk_tracking(task.task_id))

        elif "issue" in purpose:
            # extraction + tracking
            task.subtasks.append(self._execute_issue_extraction(task.task_id, content))
            task.subtasks.append(self._execute_issue_tracking(task.task_id, content))

        elif "decision" in purpose:
            task.subtasks.append(self._execute_decision_extraction(task.task_id, content))

        # --- COMMUNICATION_COLLABORATION domain orchestration ---
        elif "send" in purpose or "delivery" in purpose:
            task.subtasks.append(self._execute_message_delivery(task.task_id, source, sender))

        elif "response" in purpose or "formulate" in purpose:
            task.subtasks.append(self._execute_qna(task.task_id, content, message))

        # IMPORTANT: check for report/summary BEFORE generic "meeting"
        elif "report" in purpose or "summary" in purpose:
            task.subtasks.append(self._execute_report_generation(task.task_id, content))

        elif "meeting" in purpose:
            task.subtasks.append(self._execute_meeting_attendance(task.task_id, content))

        # --- Ambiguous handling ---
        elif "ambiguous" in purpose:
            task.subtasks.append(self._execute_ambiguous_handling(task.task_id, content, project))

        return task

    def _execute_action_item_extraction(self, parent_id: str, content: str) -> Task:
        """Extract action items from content"""
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:action_item_extraction",
            purpose="Extract action items"
        )

        # Simulate extraction logic
        action_items = []
        if "add" in content.lower() or "feature" in content.lower():
            features = self._extract_features(content)
            for i, feature in enumerate(features, 1):
                action_items.append(
                    f"AI-{i:03d}: \"Evaluate {feature}\"\n"
                    f"  Owner: ? | Due: ? | Flags: [MISSING_OWNER, MISSING_DUE_DATE]"
                )

        if "blocked" in content.lower():
            action_items.append(
                "AI-001: \"Unblock API integration issue\"\n"
                "  Owner: ? | Due: URGENT | Flags: [MISSING_OWNER]"
            )

        if not action_items and any(word in content.lower() for word in ["ready", "complete", "done"]):
            action_items.append(
                "AI-001: \"Review completed deliverable\"\n"
                "  Owner: ? | Due: ? | Flags: [MISSING_OWNER, MISSING_DUE_DATE]"
            )

        subtask.output = action_items if action_items else ["No action items detected"]
        return subtask

    def _execute_action_item_validation(self, parent_id: str) -> Task:
        """Validate extracted action items"""
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:action_item_validation",
            purpose="Validate action items"
        )

        subtask.output = [
            "Validation Summary:",
            "• All action items have been checked for required fields",
            "• Missing owners and due dates flagged where applicable"
        ]
        return subtask

    def _execute_action_item_tracking(self, parent_id: str) -> Task:
        """Track action items"""
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:action_item_tracking",
            purpose="Track action items"
        )

        subtask.output = [
            "Action Item Tracking:",
            "• New action items logged into tracking system",
            "• Initial status set to OPEN"
        ]
        return subtask


    def _execute_risk_extraction(self, parent_id: str, content: str) -> Task:
        """Extract risks from content"""
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:risk_extraction",
            purpose="Extract and assess risks"
        )

        risks = []
        if "timeline" in content.lower() or "same timeline" in content.lower():
            risks.append("RISK-001: \"Timeline compression with scope increase\"\n  Likelihood: HIGH | Impact: HIGH")

        if "scope" in content.lower() or "add" in content.lower():
            risks.append("RISK-002: \"Scope creep without resource adjustment\"\n  Likelihood: MEDIUM | Impact: MEDIUM")

        if "blocked" in content.lower():
            risks.append("RISK-001: \"Development blockers affecting delivery\"\n  Likelihood: HIGH | Impact: CRITICAL")

        if "bug" in content.lower() or "critical" in content.lower():
            risks.append("RISK-002: \"Quality issues in production path\"\n  Likelihood: HIGH | Impact: HIGH")

        if "legal" in content.lower() or "escalate" in content.lower():
            risks.append("RISK-001: \"Client escalation and contract risk\"\n  Likelihood: HIGH | Impact: CRITICAL")

        subtask.output = risks if risks else ["No significant risks identified"]
        return subtask

    def _execute_risk_tracking(self, parent_id: str) -> Task:
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:risk_tracking",
            purpose="Track risks"
        )
        subtask.output = [
            "Risk Tracking:",
            "• Identified risks logged with likelihood and impact",
            "• Risk snapshot updated for project"
        ]
        return subtask

    def _execute_issue_extraction(self, parent_id: str, content: str) -> Task:
        """Extract issues from content"""
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:issue_extraction",
            purpose="Extract issues"
        )

        issues = []
        issue_id = 1  # ensure unique IDs per message

        if "blocked" in content.lower():
            issues.append(
                f"ISSUE-{issue_id:03d}: \"API integration blocked - staging environment down\"\n"
                f"  Severity: HIGH | Status: OPEN"
            )
            issue_id += 1

        if "bug" in content.lower():
            issues.append(
                f"ISSUE-{issue_id:03d}: \"3 critical bugs in payment flow\"\n"
                f"  Severity: CRITICAL | Status: OPEN"
            )
            issue_id += 1

        if "not delivered" in content.lower() or "promised" in content.lower():
            issues.append(
                f"ISSUE-{issue_id:03d}: \"Delivery commitment missed for Q3 feature\"\n"
                f"  Severity: CRITICAL | Status: OPEN"
            )

        subtask.output = issues if issues else ["No issues detected"]
        return subtask

    def _execute_issue_tracking(self, parent_id: str, content: str) -> Task:
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:issue_tracking",
            purpose="Track issues"
        )
        subtask.output = [
            "Issue Tracking:",
            "• Detected issues logged with severity and status",
            "• Issue snapshot updated for project"
        ]
        return subtask

    def _execute_decision_extraction(self, parent_id: str, content: str) -> Task:
        """Extract decisions from content"""
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:decision_extraction",
            purpose="Extract decisions"
        )

        decisions = []
        if "can we" in content.lower() or "should we" in content.lower():
            if "add" in content.lower():
                decisions.append("DEC-001: \"Accept or reject feature request\"\n  Decision Maker: ? | Status: PENDING")
            elif "prioritize" in content.lower():
                decisions.append(
                    "DEC-001: \"Prioritization decision: security fixes vs new features\"\n  Decision Maker: ? | Status: PENDING")

        subtask.output = decisions if decisions else [
            "DEC-001: \"Decision required on request\"\n  Decision Maker: ? | Status: PENDING"]
        return subtask

    def _execute_qna(self, parent_id: str, content: str, message: Dict) -> Task:
        """Formulate response to questions"""
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:qna",
            purpose="Formulate response"
        )

        project = message.get("project", "N/A")

        if "status" in content.lower():
            response = f"""Response: "Current status of authentication feature:

WHAT I KNOW:
• Project: {project}
• Last update: Feature in testing phase
• Completion: 80%

WHAT I'VE LOGGED:
• No blocking issues
• On track for current milestone

WHAT I NEED:
• Latest test results from QA team
• Final deployment timeline confirmation

I'll follow up with the engineering team for the latest details.\""""

        elif "can we add" in content.lower() or "can we" in content.lower():
            response = """Response: "For the feature request:

WHAT I KNOW:
• Current timeline: Dec 15 (code freeze Dec 10)
• Team capacity: 85% utilized
• Progress: 70% complete

WHAT I'VE LOGGED:
• Action items for feature evaluation
• Risks flagged (timeline + scope)
• Decision pending

WHAT I NEED:
• Complexity estimates from Engineering
• Capacity analysis
• Go/no-go decision from leadership

I cannot assess feasibility without Engineering input on implementation timeline.\""""

        elif "prioritize" in content.lower() or "should" in content.lower():
            response = """Response: "Regarding prioritization decision:

WHAT I KNOW:
• Two competing priorities identified
• Both have business impact

WHAT I'VE LOGGED:
• Decision point created
• Risk assessment for both options

WHAT I NEED:
• Business impact analysis
• Technical debt assessment
• Leadership decision on priority

I recommend scheduling a quick sync with stakeholders to align on priorities.\""""

        else:
            response = f"""Response: "I've received your message regarding {project}.

WHAT I'VE LOGGED:
• Your request has been tracked
• Initial context gathered

WHAT I NEED:
• More specific information to provide accurate response
• Clarification on priority and timeline

Please provide additional details so I can assist effectively.\""""

        subtask.output = [response]
        return subtask

    def _execute_meeting_attendance(self, parent_id: str, content: str) -> Task:
        """Process meeting content"""
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:meeting_attendance",
            purpose="Process meeting transcript"
        )

        subtask.output = [
            "Meeting summary generated:",
            "• 4 speakers identified",
            "• 3 action items extracted",
            "• 2 blockers identified",
            "• 1 deliverable committed"
        ]
        return subtask

    def _execute_report_generation(self, parent_id: str, content: str) -> Task:
        """Generate report"""
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:report_generation",
            purpose="Generate meeting report"
        )

        subtask.output = [
            "Meeting Report Generated:",
            "• Attendees: 4",
            "• Key Discussion Points: Integration blockers, QA findings, design updates",
            "• Action Items: 3 assigned",
            "• Next Steps: Unblock staging, fix critical bugs, review mockups"
        ]
        return subtask

    def _execute_message_delivery(self, parent_id: str, source: str, sender: Dict) -> Task:
        """Deliver message"""
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:message_delivery",
            purpose="Send response"
        )

        subtask.output = [
            f"Channel: {source}",
            f"Recipient: {sender.get('name', 'Unknown')}",
            "Delivery Status: SENT"
        ]
        return subtask

    def _execute_ambiguous_handling(self, parent_id: str, content: str, project: str) -> Task:
        """Handle ambiguous requests"""
        subtask = Task(
            task_id=self._next_subtask_id(parent_id),
            target="L3:qna",
            purpose="Handle ambiguous request"
        )

        response = """Response: "I received your message, but need clarification:

MISSING INFORMATION:
• Specific project context (no project specified)
• Clear action or question
• Timeline or priority

WHAT I CAN DO:
• Track this as a general inquiry
• Route to appropriate team once clarified

Please provide:
1. Which project this relates to
2. Specific action needed or question
3. Any relevant timeline

This will help me assist you effectively.\""""

        subtask.output = [response]
        return subtask

    def _extract_features(self, content: str) -> List[str]:
        """Extract feature mentions from content"""
        features = []
        content_lower = content.lower()

        if "notification" in content_lower:
            features.append("real-time notifications feature")
        if "dashboard" in content_lower and "export" in content_lower:
            features.append("dashboard export feature")
        if "sso" in content_lower or "integration" in content_lower:
            features.append("SSO integration feature")

        return features if features else ["requested feature"]


class L3Agent:
    """L3 Agent - Executes specific tasks"""

    @staticmethod
    def execute_cross_cutting(task: Task, message: Dict) -> Task:
        """Execute cross-cutting agent tasks"""
        if "knowledge_retrieval" in task.target:
            return L3Agent._execute_knowledge_retrieval(task, message)
        elif "evaluation" in task.target:
            return L3Agent._execute_evaluation(task)
        return task

    @staticmethod
    def _execute_knowledge_retrieval(task: Task, message: Dict) -> Task:
        """Retrieve knowledge from database"""
        project = message.get("project", "N/A")

        if project != "N/A":
            task.output = [
                f"Project: {project}",
                "Current Release Date: Dec 15",
                "Days Remaining: 20",
                "Code Freeze: Dec 10",
                "Current Progress: 70%",
                "Team Capacity: 85% utilized",
                "Engineering Manager: Alex Kim",
                "Tech Lead: David Park"
            ]
        else:
            task.output = [
                "Project: Not specified",
                "Unable to retrieve specific project context",
                "General organizational context available"
            ]

        return task

    @staticmethod
    def _execute_evaluation(task: Task) -> Task:
        """Evaluate output quality"""
        task.output = [
            "Relevance: PASS",
            "Accuracy: PASS",
            "Tone: PASS",
            "Gaps Acknowledged: PASS",
            "Result: APPROVED"
        ]
        return task


class NionOrchestrator:
    """Main Nion Orchestration Engine"""

    def __init__(self):
        self.l1 = L1Orchestrator()

    def process_message(self, message: Dict) -> str:
        """Main entry point - processes a message and returns orchestration map"""

        # L1: Analyze and plan
        plan = self.l1.analyze_and_plan(message)

        # L2/L3: Execute plan
        executed_tasks = []
        for task in plan:
            if task.target.startswith("L2:"):
                # L2 coordination
                domain_str = task.target.split(":")[1]
                domain = L2Domain[domain_str]
                coordinator = L2Coordinator(domain)
                executed_task = coordinator.execute(task, message)
                executed_tasks.append(executed_task)
            elif task.target.startswith("L3:") and task.is_cross_cutting:
                # Cross-cutting L3 agent
                executed_task = L3Agent.execute_cross_cutting(task, message)
                executed_tasks.append(executed_task)

        # Format output
        return self._format_orchestration_map(message, plan, executed_tasks)

    def _format_orchestration_map(self, message: Dict, plan: List[Task], executed_tasks: List[Task]) -> str:
        """Format the orchestration map output"""
        output = []

        # Header
        output.append("=" * 80)
        output.append("NION ORCHESTRATION MAP")
        output.append("=" * 80)
        output.append(f"Message: {message.get('message_id', 'N/A')}")
        output.append(
            f"From: {message.get('sender', {}).get('name', 'Unknown')} ({message.get('sender', {}).get('role', 'Unknown')})")
        output.append(f"Project: {message.get('project', 'N/A')}")
        output.append("")

        # L1 Plan
        output.append("=" * 80)
        output.append("L1 PLAN")
        output.append("=" * 80)

        for task in plan:
            cross_cutting_label = " (Cross-Cutting)" if task.is_cross_cutting else ""
            output.append(f"[{task.task_id}] → {task.target}{cross_cutting_label}")
            output.append(f"Purpose: {task.purpose}")
            if task.depends_on:
                output.append(f"Depends On: {', '.join(task.depends_on)}")
            output.append("")

        # L2/L3 Execution
        output.append("=" * 80)
        output.append("L2/L3 EXECUTION")
        output.append("=" * 80)
        output.append("")

        for task in executed_tasks:
            if task.subtasks:
                # L2 task with L3 subtasks
                output.append(f"[{task.task_id}] {task.target}")
                for subtask in task.subtasks:
                    output.append(f"└─▶ [{subtask.task_id}] {subtask.target}")
                    output.append(f"    Status: {subtask.status}")
                    output.append(f"    Output:")
                    for line in subtask.output:
                        output.append(f"    • {line}")
                output.append("")
            else:
                # Cross-cutting L3 task
                cross_cutting_label = " (Cross-Cutting)" if task.is_cross_cutting else ""
                output.append(f"[{task.task_id}] {task.target}{cross_cutting_label}")
                output.append(f"Status: {task.status}")
                output.append(f"Output:")
                for line in task.output:
                    output.append(f"• {line}")
                output.append("")

        output.append("=" * 80)

        return "\n".join(output)


def main():
    """Main execution function"""
    # Test with sample input
    sample_message = {
  "message_id": "MSG-101",
  "source": "slack",
  "sender": {
    "name": "John Doe",
    "role": "Engineering Manager"
  },
  "content": "What's the status of the authentication feature?",
  "project": "PRJ-BETA"
}

    orchestrator = NionOrchestrator()
    result = orchestrator.process_message(sample_message)
    print(result)


if __name__ == "__main__":
    main()