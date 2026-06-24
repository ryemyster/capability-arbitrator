#!/usr/bin/env python3
"""
File: agent_quality_check.py
Purpose: Validates that app code meets strict AI Agent coding quality standards before building or testing.
Why it exists: Prevents agents from generating overly complex, non-DRY, or poorly typed code.
How it works: Parses Python files under app/ using AST, checking file lengths, function/node lengths, type annotations, and module header blocks.
"""

import ast
import os
import sys

MAX_FILE_LINES = 300
MAX_FUNCTION_LINES = 50

# Files that are exempt from certain checks (like system-generated entrypoints or config stubs)
EXEMPT_FILES = ["config.py", "__init__.py"]

def check_file(filepath: str) -> list[str]:
    errors = []
    filename = os.path.basename(filepath)
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    lines = content.splitlines()
    if filename not in EXEMPT_FILES and len(lines) > MAX_FILE_LINES:
        errors.append(f"File is too long: {len(lines)} lines (max {MAX_FILE_LINES})")
        
    try:
        tree = ast.parse(content, filename=filepath)
    except SyntaxError as e:
        return [f"Syntax error: {e}"]
        
    # 1. Check for Module Header Block (Module docstring with Purpose, Why, How)
    module_doc = ast.get_docstring(tree)
    if filename not in EXEMPT_FILES:
        if not module_doc:
            errors.append("Missing module-level docstring header block.")
        else:
            doc_lower = module_doc.lower()
            missing_sections = []
            for term in ["purpose:", "why", "how"]:
                if term not in doc_lower:
                    missing_sections.append(term.capitalize())
            if missing_sections:
                errors.append(f"Module docstring header is missing sections: {', '.join(missing_sections)}")
            
    # 2. Walk AST to inspect functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Determine function line count
            fn_lines = (node.end_lineno - node.lineno) + 1
            if filename not in EXEMPT_FILES and fn_lines > MAX_FUNCTION_LINES:
                errors.append(f"Function/node '{node.name}' at line {node.lineno} is too long: {fn_lines} lines (max {MAX_FUNCTION_LINES})")
                
            # Check for type annotations on arguments and return type for helper/node functions
            # Exempt standard context, node_input, self, cls parameter checks
            for arg in node.args.args:
                if arg.arg in ["self", "cls", "ctx", "node_input"]:
                    continue
                if not arg.annotation:
                    errors.append(f"Function '{node.name}' at line {node.lineno} is missing type annotation for argument '{arg.arg}'")
            
            # Check return type (except __init__)
            if node.name != "__init__" and not node.returns:
                errors.append(f"Function '{node.name}' at line {node.lineno} is missing return type annotation")
                
    return errors

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_dir = os.path.join(base_dir, "app")
    
    failed = False
    print("Running AI Agent Code Quality Checks...")
    
    for root, _, files in os.walk(app_dir):
        if "__pycache__" in root or ".adk" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, base_dir)
                errors = check_file(filepath)
                if errors:
                    print(f"❌ {rel_path} failed quality check:")
                    for err in errors:
                        print(f"   - {err}")
                    failed = True
                else:
                    print(f"✅ {rel_path} passed.")
                    
    if failed:
        print("\nCode quality checks failed. Please refactor to comply with standards.")
        sys.exit(1)
    else:
        print("\nAll code quality checks passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
