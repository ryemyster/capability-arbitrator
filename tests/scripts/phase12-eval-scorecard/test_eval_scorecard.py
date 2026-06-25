# Created: 2026-06-24T18:28:00-06:00
"""
File: test_eval_scorecard.py
Purpose: Executable test script for validating Phase 12 Scorecard Metrics configuration.
Why it exists: Part of the Phase Completion Verification Workflow for Phase 12.
How it works: Parses tests/eval/eval_config.yaml and tests/eval/datasets/routing-eval.json to verify config integration.
"""
import os
import sys
import yaml
import json

def run_scorecard_test() -> None:
    print("============================================================")
    print("PHASE 12: EVALUATION SCORECARD METRICS VALIDATION")
    print("============================================================")
    
    config_path = "tests/eval/eval_config.yaml"
    dataset_path = "tests/eval/datasets/routing-eval.json"
    
    try:
        # Check 1: Config file exists
        assert os.path.exists(config_path), f"Config file not found at {config_path}"
        print("Sub-test 1 (Config File Existence) [PASS]")
        
        # Check 2: Load and parse eval_config.yaml
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            
        metrics_to_run = config.get("metrics_to_run", [])
        custom_metrics = config.get("custom_metrics", [])
        
        # Check 3: Check registered metrics in metrics_to_run
        required_metrics = [
            "latency_seconds",
            "token_efficiency",
            "pii_redaction_accuracy",
            "scout_confidence_gate",
            "deterministic_offload_accuracy",
        ]
        for m in required_metrics:
            assert m in metrics_to_run, f"Metric '{m}' not registered under metrics_to_run"
        print("Sub-test 2 (metrics_to_run verification) [PASS]")
        
        # Check 4: Check custom_metrics contains implementations
        custom_metric_names = [cm.get("name") for cm in custom_metrics]
        for m in required_metrics:
            assert m in custom_metric_names, f"Metric '{m}' implementation not found in custom_metrics"
        print("Sub-test 3 (custom_metrics implementation verification) [PASS]")
        
        # Check 5: Verify dataset updates
        assert os.path.exists(dataset_path), f"Dataset file not found at {dataset_path}"
        with open(dataset_path, "r") as f:
            dataset = json.load(f)
            
        eval_cases = dataset.get("eval_cases", [])
        case_ids = [ec.get("eval_case_id") for ec in eval_cases]
        
        required_cases = [
            "math_routing",
            "pii_ssn_routing",
            "pii_email_routing",
            "pii_cc_routing",
            "latency_limit_routing",
        ]
        for c in required_cases:
            assert c in case_ids, f"Required test case '{c}' not found in routing-eval.json"
        print("Sub-test 4 (Dataset case additions verification) [PASS]")
        
        print("[PASS] Scorecard Metrics and configuration validated successfully.")
        
    except Exception as e:
        print(f"[FAIL] Scorecard Metrics validation failed. Error: {e}")
        sys.exit(1)
        
    print("============================================================")

if __name__ == "__main__":
    run_scorecard_test()
