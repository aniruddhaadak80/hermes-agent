## 2024-05-18 - Prevent Secret Leakage in `shell.exec`
**Vulnerability:** The `shell.exec` method in `tui_gateway/methods_tools.py` executed arbitrary shell commands (`subprocess.run(..., shell=True)`) without sanitizing the environment variables. Because the TUI server process holds API keys and secrets in `os.environ`, these secrets could be leaked to the shell environment of the child process.
**Learning:** Even though `shell.exec` passes through an approval gate, any command that gets approved could inadvertently access or leak secrets if the environment isn't sanitized.
**Prevention:** Always use `build_subprocess_env()` from `tools.environments.local` to sanitize the environment before executing shell commands that shouldn't inherit the parent process's credentials.

## 2026-09-11 - Prevent Secret Leakage in `agent/anthropic_credentials.py` `subprocess.run` calls
**Vulnerability:** The `_read_claude_code_credentials_from_keychain` and `run_oauth_setup_token` functions in `agent/anthropic_credentials.py` executed `subprocess.run` calls without sanitizing the environment variables. The parent process may hold API keys and credentials in `os.environ`, which would be passed to the child process (like `security` and `claude setup-token`).
**Learning:** Any `subprocess.run` call, even running simple CLI tools, should sanitize its environment. Relying on default inheritance can leak secrets, especially in Python where `os.environ` contains application credentials.
**Prevention:** Always pass `env=build_subprocess_env()` (from `tools.environments.local`) to all `subprocess.run` calls to ensure that the Hermes secret-scrub policy is applied.
