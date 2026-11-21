import inspect
import sys
import os
import traceback

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

import tests.unit.test_gstin as t_gstin
import tests.unit.test_normalize as t_normalize
import tests.unit.test_validation_rules as t_rules
import tests.unit.test_metrics as t_metrics
import tests.unit.test_sql_guard as t_sql_guard

modules = [t_gstin, t_normalize, t_rules, t_metrics, t_sql_guard]

passed = 0
failed = 0

print("=" * 60)
print("DocuMind Unit Test Runner")
print("=" * 60)

for mod in modules:
    print(f"\nRunning tests in {mod.__name__}:")
    for name, func in inspect.getmembers(mod, inspect.isfunction):
        if name.startswith("test_"):
            try:
                func()
                print(f"  [PASS] {name}")
                passed += 1
            except Exception as e:
                print(f"  [FAIL] {name}: {e}")
                traceback.print_exc()
                failed += 1

print("\n" + "=" * 60)
print(f"Summary: {passed} passed, {failed} failed")
print("=" * 60)

if failed > 0:
    sys.exit(1)
