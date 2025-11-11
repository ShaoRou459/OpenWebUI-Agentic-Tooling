"""
Simple validation script for OpenWebUI tools.
This validates syntax, structure, and basic requirements without running the tools.
"""

import os
import sys
import ast
import re


def validate_python_syntax(filepath):
    """Check if Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, "Syntax valid"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"


def validate_tool_structure(filepath):
    """Check if file has required OpenWebUI tool structure."""
    try:
        with open(filepath, 'r') as f:
            code = f.read()

        # Parse the AST
        tree = ast.parse(code)

        # Check for Tools class
        has_tools_class = False
        has_valves_class = False
        has_init = False
        tool_methods = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name == "Tools":
                    has_tools_class = True
                    # Check for nested Valves class and __init__
                    for item in node.body:
                        if isinstance(item, ast.ClassDef) and item.name == "Valves":
                            has_valves_class = True
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if item.name == "__init__":
                                has_init = True
                            elif not item.name.startswith("_"):
                                # Public method (tool method)
                                tool_methods.append(item.name)

        issues = []
        if not has_tools_class:
            issues.append("Missing 'Tools' class")
        if not has_valves_class:
            issues.append("Missing 'Valves' class")
        if not has_init:
            issues.append("Missing '__init__' method")
        if not tool_methods:
            issues.append("No public tool methods found")

        if issues:
            return False, "; ".join(issues)
        else:
            return True, f"Valid structure (methods: {', '.join(tool_methods)})"

    except Exception as e:
        return False, f"Validation error: {e}"


def validate_docstring(filepath):
    """Check if file has proper OpenWebUI docstring."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Check for title, description, author
        required_fields = ['Title:', 'Description:', 'author:', 'Version:']
        missing = []

        for field in required_fields:
            if field not in content[:500]:  # Check in first 500 chars
                missing.append(field)

        if missing:
            return False, f"Missing docstring fields: {', '.join(missing)}"
        else:
            return True, "Complete docstring"

    except Exception as e:
        return False, f"Error reading file: {e}"


def validate_async_methods(filepath):
    """Check that tool methods are async."""
    try:
        with open(filepath, 'r') as f:
            code = f.read()

        tree = ast.parse(code)

        public_methods = []
        async_methods = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "Tools":
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith("_"):
                        public_methods.append(item.name)
                        if isinstance(item, ast.AsyncFunctionDef):
                            async_methods.append(item.name)

        non_async = set(public_methods) - set(async_methods)
        if non_async:
            return False, f"Non-async tool methods: {', '.join(non_async)}"
        else:
            return True, f"All {len(async_methods)} tool methods are async"

    except Exception as e:
        return False, f"Error: {e}"


def validate_tool_file(filepath):
    """Run all validations on a tool file."""
    filename = os.path.basename(filepath)
    print(f"\n{'=' * 80}")
    print(f"Validating: {filename}")
    print(f"{'=' * 80}")

    validations = [
        ("Syntax Check", validate_python_syntax),
        ("Tool Structure", validate_tool_structure),
        ("Docstring", validate_docstring),
        ("Async Methods", validate_async_methods),
    ]

    all_passed = True
    results = []

    for name, validator in validations:
        passed, message = validator(filepath)
        status = "✓" if passed else "✗"
        print(f"{status} {name}: {message}")

        if not passed:
            all_passed = False

        results.append((name, passed, message))

    return all_passed, results


def main():
    """Main validation script."""
    print("=" * 80)
    print("OpenWebUI Tools Validation")
    print("=" * 80)

    # Get all Python files in the directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tool_files = [
        os.path.join(script_dir, f)
        for f in os.listdir(script_dir)
        if f.endswith('.py') and f not in ['test_tools.py', 'validate_tools.py', '__init__.py']
    ]

    if not tool_files:
        print("✗ No tool files found!")
        return False

    print(f"\nFound {len(tool_files)} tool file(s) to validate\n")

    all_tools_passed = True
    results_summary = []

    for tool_file in sorted(tool_files):
        passed, results = validate_tool_file(tool_file)
        results_summary.append((os.path.basename(tool_file), passed))

        if not passed:
            all_tools_passed = False

    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    for filename, passed in results_summary:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {filename}")

    print("=" * 80)

    if all_tools_passed:
        print("✓ All tools passed validation!")
        print("\nAll tools are ready to use in OpenWebUI.")
        print("\nTo use these tools:")
        print("  1. Copy the tool files to your OpenWebUI tools directory")
        print("  2. Configure the API keys in the Valves settings")
        print("  3. Enable the tools in your OpenWebUI instance")
    else:
        print("✗ Some tools failed validation. Please review the issues above.")

    print("=" * 80)

    return all_tools_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
