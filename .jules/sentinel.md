## 2024-05-18 - Prevent Secret Leakage in `shell.exec`
**Vulnerability:** The `shell.exec` method in `tui_gateway/methods_tools.py` executed arbitrary shell commands (`subprocess.run(..., shell=True)`) without sanitizing the environment variables. Because the TUI server process holds API keys and secrets in `os.environ`, these secrets could be leaked to the shell environment of the child process.
**Learning:** Even though `shell.exec` passes through an approval gate, any command that gets approved could inadvertently access or leak secrets if the environment isn't sanitized.
**Prevention:** Always use `build_subprocess_env()` from `tools.environments.local` to sanitize the environment before executing shell commands that shouldn't inherit the parent process's credentials.

## 2026-09-05 - Prevent Secret Leakage in MCP Catalog Bootstrap
**Vulnerability:** The `_run_bootstrap` method in `hermes_cli/mcp_catalog.py` executed arbitrary bootstrap shell commands (`subprocess.run(..., shell=True)`) during MCP installation without sanitizing environment variables.
**Learning:** Any component that shells out, especially during untrusted third-party component installation like MCP catalog bootstrapping, is vulnerable to secret leakage if `os.environ` containing the CLI's loaded API keys is passed directly to the child process.
**Prevention:** Always use `build_subprocess_env()` from `tools.environments.local` to sanitize the environment before executing third-party shell commands to ensure credentials aren't inherited by untrusted child processes.
