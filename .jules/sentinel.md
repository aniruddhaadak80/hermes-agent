## 2024-08-30 - Subprocess Environment Sanitization
**Vulnerability:** Found `subprocess.run` calls without `env` specified in processes that hold API keys in `os.environ` (like the TUI server process executing `shell.exec`).
**Learning:** The default behavior of `subprocess.run` (and similar functions) is to inherit `os.environ` of the parent process. If a process holds API keys in its environment and runs user-provided or plugin commands without sanitizing the environment, those keys are leaked to the child processes.
**Prevention:** Always pass `env=build_subprocess_env()` (imported from `tools.environments.local`) when spawning subprocesses from sensitive components (like `tui_gateway/methods_tools.py`) to prevent environment variable leakage.
