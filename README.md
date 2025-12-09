# Nion Orchestration Engine

## Project Overview: Three-Tier AI Orchestration System

This project is a simplified, standalone implementation of Nion's three-tier AI orchestration system designed for **project management**. Its core function is to analyze incoming communication (like emails or meeting transcripts), extract critical information (action items, risks, issues, decisions), and coordinate an appropriate, context-aware response using a hierarchical structure of AI agents.

The system's architecture is a key feature, ensuring a clear **separation of concerns** and efficient delegation of tasks.



---

## Architecture Overview

The system implements a rigid three-tier hierarchy for task delegation and execution:

### L1 Orchestrator (The Planner)
* **Role:** Analyzes message intent, identifies informational gaps, and creates a complete **execution plan** (a sequence of tasks).
* **Visibility:** Can see **all L2 domains** and **Cross-cutting agents** (`knowledge_retrieval`, `evaluation`).
* **Constraint:** **Cannot** directly access L3 agents. All L3 execution must be delegated through an L2 Coordinator.

### L2 Coordinators (The Managers)
* **Role:** Receives a domain-specific task from L1, breaks it down into specific L3 agent calls, coordinates their execution, and aggregates the results.
* **Visibility:** Can see **its own L3 agents** and **Cross-cutting agents**.

### L3 Agents (The Workers)
* **Role:** Executes a single, specific task (e.g., extraction, validation, tracking, Q&A).
* **Execution:** Performs the core work and returns structured output.

### L2 Domains & Responsibilities

| Domain | Coordinator | L3 Agents | Purpose |
| :--- | :--- | :--- | :--- |
| **TRACKING\_EXECUTION** | L2 | Extraction, Validation, Tracking | Handling Action Items, Risks, Issues, and Decisions. |
| **COMMUNICATION\_COLLABORATION** | L2 | Q&A, Reporting, Delivery | Generating context-aware, gap-aware responses and reports. |
| **LEARNING\_IMPROVEMENT** | L2 | Instruction\_Parsing | Adapting system behavior based on explicit user instructions. |

---

## Features

* ✅ **Intent Analysis** and **Automatic Task Planning**.
* ✅ Structured **Extraction** of Action Items, Risks, Issues, and Decisions.
* ✅ **Context-Aware Response Generation** with explicit gap awareness ("What we know vs. What we need").
* ✅ Processing of **Meeting Transcripts** to extract multiple entities.
* ✅ **Escalation** and **Ambiguous Request** handling.
* ✅ Full **Orchestration Map Visualization** in the output for transparency.

---

## Setup Instructions

### Prerequisites

* **Python 3.11**.
* **No external dependencies** required (uses only the Python standard library).

### Installation

1.  Clone or download the repository:
    ```bash
    git clone <repository-url>
    cd aiNions_test
    ```
2.  No additional packages are needed.

### Running the Application

Run the main script to process a default test case:

```bash
python main.py
```

## Included Test Cases

The implementation supports 6 distinct scenarios to demonstrate the system's flexibility:

| Test Case | Scenario | Key Intent |
| :--- | :--- | :--- |
| **Test Case 1** | Simple Status Question | Information Retrieval |
| **Test Case 2** | Feasibility Question | Decision / Planning |
| **Test Case 3** | Decision/Recommendation Request | Conflict Resolution |
| **Test Case 4** | Meeting Transcript | **Multi-entity Extraction** (AI, Risk, Issue, Decision) |
| **Test Case 5** | Urgent Escalation | Priority Handling / **Escalation** |
| **Test Case 6** | Ambiguous Request | **Gap Detection** / Clarification |
