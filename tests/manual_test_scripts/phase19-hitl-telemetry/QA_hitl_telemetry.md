# Phase 19 Manual QA: Durable HITL Telemetry

## Why this test exists

HITL decisions can occur in the ADK Playground while the dashboard is already open.
This test confirms that graph nodes persist their own checkpoints and that the
dashboard shows approved and denied decisions without depending on an app callback.

## Prerequisites

- Start in the repository root.
- Install the project with `agents-cli install`.
- Do not use real customer information. The SSN below is synthetic test data.

## Test procedure

1. Start the dashboard:

   ```bash
   uv run arbitrator dashboard
   ```

2. In another terminal, start the visual graph Playground:

   ```bash
   uv run agents-cli playground --port 8080
   ```

3. Open the dashboard at `http://127.0.0.1:8000/`.
4. Open the Playground at `http://127.0.0.1:8080/`.
5. Create a new Playground session and send:

   ```text
   Update the customer record for John Smith, SSN 123-45-6789, to reflect the new billing address.
   ```

6. Enter `n` at the approval prompt.
7. Create a second Playground session, repeat the prompt, and enter `y`.
8. Wait up to five seconds for each dashboard refresh.

## Expected result

- [ ] Two records containing the synthetic John Smith prompt appear in run history.
- [ ] Each interrupt first appears as pending and is not counted as denied.
- [ ] `HITL Interrupt events` increases by two.
- [ ] `HITL Denied` increases by one.
- [ ] `HITL Approved` increases by one.
- [ ] The approved row includes any downstream Scout or execution token usage.
- [ ] The denied row stops after approval and does not claim downstream work.
- [ ] No dashboard or runner restart is needed.
- [ ] Playground still displays the expected Security Screen, Approval, Scout, and execution transitions.

## Ambiguous routing resume test

1. Create another new Playground session.
2. Send:

   ```text
   Please do some math calculations, or maybe look up code files, or write a summary. I'm not sure which capability we need here.
   ```

3. Confirm Scout selects `math` with confidence below `75%`.
4. Enter `y` to approve Scout's suggested route.

Expected result:

- [ ] Exactly one HITL popup appears.
- [ ] The approval output routes directly to Scout's suggested capability.
- [ ] The original prompt remains present after resume.
- [ ] No `{capability_tag: "approval", prompt: ""}` event appears.
- [ ] A later, genuinely separate gate would use a different interrupt ID.
- [ ] Entering `y` accepts Scout's suggestion without producing another popup.
- [ ] Entering a capability name re-prompts for `y` or `n`; it does not override Scout.

## Automated companion

```bash
uv run python tests/scripts/phase19-hitl-telemetry/test_hitl_telemetry.py
```

*Created: 2026-07-06T11:15:35-06:00*
