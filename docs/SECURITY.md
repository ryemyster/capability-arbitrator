# Security & Privacy Blueprint
### PII Detection, Approval Routing and STRIDE Threat Modeling

The Capability Arbitrator includes prototype security controls for local and deployable agent workflows. This document outlines data privacy screening, approval routing and structured STRIDE threat modeling.

---

## 1. Pre-LLM PII and Data Privacy Guardrail

### Why
AI models should not receive sensitive user secrets, credentials, or personally identifiable information (PII) unless a human explicitly approves that flow. The Security Screen exists to catch common sensitive patterns before normal routing begins.

### What
The **Security Screen** is a high-speed, pre-LLM regex scanning layer. It intercepts every inbound user prompt *before* it is parsed by the intent classifier (Scout node), screening for five configured categories:
1. **Social Security Numbers (SSNs):** Standard `XXX-XX-XXXX` formats.
2. **Email Addresses:** Standard SMTP email address strings.
3. **Phone Numbers:** Global and local phone layouts.
4. **Credit Card Numbers:** Standard 16-digit credit card spacing.
5. **IP Addresses:** IPv4 address notations.

### How it Works
Implemented as a deterministic Function Node in [app/agent.py](../app/agent.py):
```python
@node
def security_screen(node_input: str) -> Event:
    # Regex match checks
    # If PII is found:
    return Event(
        output="[SECURITY ALERT] PII detected in input...", 
        route="approval"
    )
```
If a PII pattern is matched, the system blocks normal execution and routes the event to the **HITL Approval** node. The implementation detects and escalates; it does not rewrite or redact the original inbound prompt.

### When
Runs automatically at the `START` of the execution graph. Covered regex patterns route to approval before the Scout runs.

---

## 2. STRIDE Threat Modeling Workflow

### Why
Developers need structured security auditing to identify architectural and code-level vulnerabilities early in the software development lifecycle.

### What
The **STRIDE Node** is a specialized `LlmAgent` loaded with custom security instructions ([app/skills/stride/SKILL.md](../app/skills/stride/SKILL.md)). It reviews supplied code or architecture text across six threat categories:

* **S**poofing (Identity Impersonation)
* **T**ampering (Malicious Modifications)
* **R**epudiation (Lack of Traceability)
* **I**nformation Disclosure (Secret Leaks)
* **D**enial of Service (Resource Exhaustion)
* **E**levation of Privilege (Unauthorized Access)

### How it Works
1. The **Scout Node** detects a security query (e.g. *"Audit this API gateway structure for security threats"*).
2. The orchestrator routes the request to `stride_node` and progressively loads the STRIDE skill instructions into the active context.
3. The node generates a structured threat report containing:
   - **Executive Security Summary**
   - **Data Flow & Trust Boundaries**
   - **Threat Modeling Table** (with Severity and concrete Mitigation Recommendations).

### When
Triggered when a user requests a threat modeling audit through the live routing graph.

---

## 3. STRIDE Self-Healing CLI

### Why
Security reports are only useful if someone can turn them into verified patches. The STRIDE Self-Healing CLI connects the STRIDE review skill to a patch-generation skill, then verifies the result before it can open a PR.

### What
The self-healing pipeline is an offline CLI workflow, not a live graph node. It is disabled by default and controlled by [`config/stride_self_healing.yaml`](../config/stride_self_healing.yaml) plus `STRIDE_SELF_HEALING_*` environment overrides from `.env.example`.

### How it Works
Run:
```bash
uv run arbitrator stride-heal app/agent.py --mode audit_only
uv run arbitrator stride-heal app/agent.py --mode apply_patch
```

The implementation in [app/app_utils/patch_agent_utils.py](../app/app_utils/patch_agent_utils.py):
1. calls the STRIDE skill on the target file,
2. parses medium/high findings from the threat table,
3. asks the patch agent to generate corrected file content,
4. writes the patch only in patching modes,
5. runs configured verification commands,
6. reverts the file if verification fails,
7. opens a PR only in `open_pr` mode.

### When
Use it for controlled local security remediation experiments. Keep `STRIDE_SELF_HEALING_ENABLED=false` unless you are intentionally testing the feature.
