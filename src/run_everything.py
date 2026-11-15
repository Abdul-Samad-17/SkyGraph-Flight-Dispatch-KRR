"""Rebuilds every artefact from the CSVs:  python src/run_everything.py   (then python src/tests.py)"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ["make_dataset.py", "build_kg.py", "reasoner.py", "expected_results.py", "generate_reports.py", "make_visuals.py",
         "embeddings.py", "evaluate.py", "demo_transcripts.py", "build_report.py"]
for s in STEPS:
    path = os.path.join(HERE, s)
    if not os.path.exists(path):
        print("skip (missing):", s); continue
    print("==> " + s)
    subprocess.run([sys.executable, path], check=True, cwd=HERE, stdout=subprocess.DEVNULL if s in ("embeddings.py",) else None)
print("all steps finished")
