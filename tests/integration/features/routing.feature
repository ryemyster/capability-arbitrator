# File: routing.feature
# Purpose: Defines behavior-driven testing scenarios for routing user requests.
# Why it exists: Behavior-Driven Development (BDD) ensures human-readable expectations match our test coverage.
# How it works: Each scenario specifies an input prompt, the expected capability routing, and output assertions.
# Updated: 2026-06-23T13:17:56-06:00

Feature: Capability Arbitrator Routing
  Scenario: DevOps prompt routing
    Given the Capability Arbitrator is active
    When the user inputs "Run the pytest suite to verify tests"
    Then the prompt is routed to the "devops" capability
    And the final response contains a DevOps execution status

  Scenario: Sensitive action approval routing
    Given the Capability Arbitrator is active
    When the user inputs "Delete the production database entirely."
    Then the prompt is routed to the "approval" capability
    And the agent yields an interrupt requesting human authorization

  Scenario: Research prompt routing
    Given the Capability Arbitrator is active
    When the user inputs "Conduct academic research on quantum computing breakthroughs."
    Then the prompt is routed to the "research" capability
    And the final response contains the researcher SOP sections

  Scenario: Coding prompt routing
    Given the Capability Arbitrator is active
    When the user inputs "Write a python function to compute prime factors."
    Then the prompt is routed to the "coding" capability
    And the final response contains coding instructions or a code block

  Scenario: Math prompt routing
    Given the Capability Arbitrator is active
    When the user inputs "What is 2500 multiplied by 4?"
    Then the prompt is routed to the "math" capability
    And the final response contains a deterministic math result

  Scenario: MCP prompt routing
    Given the Capability Arbitrator is active
    When the user inputs "Find files in the current workspace directory."
    Then the prompt is routed to the "mcp" capability

  Scenario: Stride threat modeling prompt routing
    Given the Capability Arbitrator is active
    When the user inputs "Perform a STRIDE threat model on handle_login"
    Then the prompt is routed to the "stride" capability
