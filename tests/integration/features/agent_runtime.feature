# File: agent_runtime.feature
# Purpose: Defines behavior-driven testing scenarios for the Agent Runtime App.
# Why it exists: Enforces Gherkin BDD coverage for Agent Runtime App services.
# How it works: Runs streaming queries and validates feedback records.

Feature: Agent Runtime App Functionality
  Scenario: Querying the agent app via async stream query
    Given the Agent Runtime App is active
    When the user sends a stream query "Hi!"
    Then the runtime app returns a streaming response with text

  Scenario: Registering valid and invalid customer feedback
    Given the Agent Runtime App is active
    When the user submits valid feedback score 5 and text "Great response!"
    Then the feedback is successfully registered
    And submitting feedback with invalid score "invalid" raises a value error
