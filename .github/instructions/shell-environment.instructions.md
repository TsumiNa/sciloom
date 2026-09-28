---
description: "Use at the start of any new session before running terminal commands. Detect the active shell to avoid heredoc and syntax errors caused by shell incompatibility (fish, bash, zsh, sh)."
---
# Shell Environment Awareness

At the start of every new agent session, before executing any terminal command, confirm the active shell.

## How to Confirm

Identify the interpreter from the execution environment's metadata or the
command runner's configured shell before relying on shell-specific syntax. Do
not make the initial probe depend on `$$`, `$0`, `$fish_pid`, command
substitution or conditional syntax: those expressions must be parsed before the
interpreter is known and are not portable across the supported shells.

If the environment does not expose the interpreter, use an explicitly selected
shell through the command runner when available; otherwise keep commands to
literal, shell-neutral program invocations until the interpreter is known.
Treat `$SHELL` only as information about the user's login shell; it may not be
the interpreter executing the current command. Record the running interpreter
for the rest of the session and do not assume Bash.

## Shell-Specific Rules

**fish shell** — does NOT support POSIX heredocs. Avoid all of these patterns:

```bash
# WRONG in fish
cat << 'EOF' >> file.txt
...content...
EOF
```

Use `printf` or `echo` with explicit newlines instead, or write the file directly with an editor tool:

```fish
printf '%s\n' 'line1' 'line2' >> file.txt
```

Or prefer the `create_file` / `replace_string_in_file` agent tools whenever available — they bypass shell syntax entirely.

**bash / zsh / sh** — POSIX heredocs are safe. Use them normally.

## General Rules

- Never assume `bash` without confirming — the user's default interactive shell may differ.
- Do not use `bash -c "..."` sub-shells to work around fish syntax unless explicitly asked.
- When in doubt, prefer agent file-editing tools over shell redirection for writing file content.
- If a command fails with a shell syntax error, check the active shell before retrying.
- Prefer `rg` and `rg --files` for searching, and patch or editor tools over shell redirection for changing files.
- Never print secrets, tokens, environment files or credential-bearing command output.
- Do not delete or overwrite files, caches, branches or user changes whose exact target has not been verified, and never discard or reformat unrelated user changes.
