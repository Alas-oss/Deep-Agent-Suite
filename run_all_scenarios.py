import subprocess
import sys 
from pathlib import Path
import time

REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"
OUTPUT_DIR = REPO_ROOT / "outputs"
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from scenarios import SCENARIOS

def cleanup_outputs(scenario):
    for f in scenario["expected_outputs"]:
        p = OUTPUT_DIR / f
        if p.exists():
            p.unlink()

results = []
for idx, scenario in enumerate(SCENARIOS):
    print(f"\n Running scenario {idx}: {scenario['name']} ")
    cleanup_outputs(scenario)

    proc = subprocess.run([sys.executable, "main.py", str(idx)], capture_output=True, text=True, cwd=REPO_ROOT)

    missing = [f for f in scenario["expected_outputs"] if not (OUTPUT_DIR / f).exists()]
    passed = len(missing) == 0

    results.append({"scenario": scenario["name"], "passed": passed, "missing": missing})
    if not passed:
        print(f"STDOUT: \n{proc.stdout[-2000:]}")
        print(f"STDERR: \n{proc.stderr[-2000:]}")

    if idx < len(SCENARIOS) - 1:
        print("Pausing 20s between scenarios to respect rate limits...")
        time.sleep(20)

print("\n Summary ")
for r in results:
    status = "PASS" if r["passed"] else f"FAIL (missing: {r['missing']})"
    print(f"{r['scenario']}: {status}")