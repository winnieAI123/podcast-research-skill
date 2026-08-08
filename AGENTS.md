# Agent Installation Protocol

When a user asks you to install this repository, do not install immediately.

1. Read `README.md` and inspect the current machine with `python3 install.py --check-only` on macOS/Linux or `py -3 install.py --check-only` on Windows. Add `--agent claude`, `--agent codex`, or `--agent both` when the target is known.
2. Report the detected platform, Python version, physical RAM, free disk space, intended Agent target, local transcription backend, expected model download size, and any failed or optional conditions.
3. Explain exactly what installation will change: install Python packages and copy the Skill into the selected Agent directory.
4. Ask the user for explicit confirmation after presenting the assessment. The assessment command must not install packages or copy files.
5. Run the normal installation command only after confirmation. Preserve the same Python launcher used during assessment.
6. Show the final `SUCCESS` and `READY` results. If installation fails, retain the original error and do not claim completion.

Do not treat a request to inspect, evaluate, or review the repository as permission to install it.
