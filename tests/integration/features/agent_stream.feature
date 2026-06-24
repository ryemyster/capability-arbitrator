# File: agent_stream.feature
# Purpose: Defines behavior-driven testing scenarios for agent streaming.
# Why it exists: Enforces Gherkin BDD coverage for streaming interactions.
# How it works: Runs queries with SSE streaming enabled and asserts chunk responses.

Feature: Agent Stream Functionality
  Scenario: Querying agent and receiving streaming response
    Given the Capability Arbitrator is active
    When the user requests streaming for "Why is the sky blue?"
    Then the agent returns at least one streaming response chunk containing text
