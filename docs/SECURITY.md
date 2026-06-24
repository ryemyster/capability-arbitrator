# Security & Privacy Blueprint
### GDPR PII Screening and STRIDE Threat Modeling

The Capability Arbitrator is designed for secure enterprise deployment. This document outlines our data privacy screening (PII redaction) and structured security auditing (STRIDE threat modeling) architectures.

---

## 🔒 1. Pre-LLM PII & Data Privacy Guardrail

### Why
AI models must never ingest sensitive user secrets, credentials, or personally identifiable information (PII). Allowing this data to enter the model context window risks leaking user information into public training caches or external logs.

### What
The **Security Screen** is a high-speed, pre-LLM regex scanning layer. It intercepts every inbound user prompt *before* it is parsed by the intent classifier (Scout node), screening for five core GDPR-scoped categories:
1. **Social Security Numbers (SSNs):** Standard `XXX-XX-XXXX` formats.
2. **Email Addresses:** Standard SMTP email address strings.
3. **Phone Numbers:** Global and local phone layouts.
4. **Credit Card Numbers:** Standard 16-digit credit card spacing.
5. **IP Addresses:** IPv4 address notations.

### How it Works
Implemented as a deterministic Function Node in [app/agent.py:L185-204](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/agent.py#L185-204):
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
If a PII pattern is matched, the system blocks direct execution and routes the event to the **HITL Approval** node, requiring human permission to proceed.

### When
Runs automatically at the `START` of every single execution graph, guaranteeing that no LLM receives un-screened user data.

---

## 🛡️ 2. STRIDE Threat Modeling Workflow

### Why
Developers need structured security auditing to identify architectural and code-level vulnerabilities early in the software development lifecycle.

### What
The **STRIDE Node** is a specialized `LlmAgent` loaded with custom security intelligence ([app/skills/stride/SKILL.md](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/skills/stride/SKILL.md)). It dynamically decomposes system architectures and assesses vulnerabilities across six vectors:

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
Triggered dynamically when a user requests a threat modeling audit, ensuring heavy threat-analysis rules are only loaded when explicitly needed.
