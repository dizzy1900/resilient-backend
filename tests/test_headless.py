import json
import subprocess
import sys
from pathlib import Path


def test_headless_runner_outputs_valid_json_with_expected_keys():
    repo_root = Path(__file__).resolve().parents[1]

    cmd = [
        sys.executable,
        str(repo_root / "headless_runner.py"),
        "--lat",
        "5.6",
        "--lon",
        "-0.2",
        "--scenario_year",
        "2030",
        "--project_type",
        "agriculture",
        "--use-mock-data",
    ]

    proc = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, (
        "headless_runner.py exited non-zero. "
        f"returncode={proc.returncode}\n"
        f"stdout=\n{proc.stdout}\n"
        f"stderr=\n{proc.stderr}\n"
    )

    # Ensure stdout is valid JSON
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(
            "headless_runner.py did not output valid JSON to stdout. "
            f"error={e}\nstdout=\n{proc.stdout}\nstderr=\n{proc.stderr}\n"
        )

    assert "financial_analysis" in data
    assert "crop_analysis" in data
