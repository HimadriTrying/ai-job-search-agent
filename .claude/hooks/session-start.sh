#!/bin/bash
# SessionStart hook — installs rtk (https://github.com/rtk-ai/rtk) in Claude Code
# on the web sessions. rtk is a CLI proxy that compresses command output (git,
# tests, etc.) before it reaches the model's context window, protecting the
# rate-limit quota. The PreToolUse hook (rtk-rewrite.sh) degrades to a no-op when
# rtk is absent, so nothing here is allowed to fail the session.
set -uo pipefail

# Web/remote sessions only. On a local machine, install rtk once yourself
# (`brew install rtk`) and it's picked up as-is.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# Remote environments route HTTPS through an inspecting proxy with its own CA;
# point curl (including the curls inside rtk's install.sh) at that bundle.
if [ -f /root/.ccr/ca-bundle.crt ]; then
  export CURL_CA_BUNDLE=/root/.ccr/ca-bundle.crt
fi

# Idempotent: the container cache keeps the binary between sessions.
if ! command -v rtk >/dev/null 2>&1; then
  # Fast path: prebuilt release binary → ~/.local/bin. Needs github.com to be
  # reachable, which depends on the environment's network policy.
  curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh | sh \
    || true

  # Fallback: build from source via git, which the proxy allows even when plain
  # HTTPS to github.com is blocked. ~3 min once, then cached with the container.
  if ! command -v rtk >/dev/null 2>&1 && command -v cargo >/dev/null 2>&1; then
    echo "[session-start] release download unavailable; building rtk with cargo (~3 min, first session only)" >&2
    CARGO_NET_GIT_FETCH_WITH_CLI=true cargo install --quiet --git https://github.com/rtk-ai/rtk rtk \
      || echo "[session-start] rtk build failed — session continues without compression" >&2
  fi
fi

# Make rtk visible to the Bash tool for the rest of the session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi

rtk --version 2>/dev/null || true
exit 0
