## 2024-05-18 - Missing Environment Sanitization in Subprocesses
**Vulnerability:** Found `subprocess.run` calls without the `env` argument (e.g., in `agent/skill_preprocessing.py`), meaning they inherited the full environment containing sensitive credentials (`ANTHROPIC_API_KEY`, etc.).
**Learning:** In Python, if `env` is not explicitly provided to `subprocess.run` or `Popen`, it defaults to inheriting all of `os.environ`. This is a risk when executing arbitrary or user-defined commands.
**Prevention:** Always pass an explicit, sanitized environment using `env=build_subprocess_env()` from `tools.environments.local` for any `subprocess` calls executing arbitrary commands.
