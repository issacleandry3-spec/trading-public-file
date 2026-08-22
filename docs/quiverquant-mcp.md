# Connecting to the QuiverQuant MCP server

QuiverQuant exposes a **remote** MCP server at `https://mcp.quiverquant.com/`.
Authentication is a bearer token from your Quiver account page
(**Account → Authorization Token**).

The token is a credential equivalent to your password for the API. It must never
be written into a file that gets committed — this repository is public.

---

## Option A — Claude Code (recommended)

Claude Code speaks remote MCP natively, so no `npx mcp-remote` bridge is needed.

### One-off, user-wide (token stays in `~/.claude.json`, outside this repo)

```bash
claude mcp add --transport http quiverquant https://mcp.quiverquant.com/ \
  --scope user \
  --header "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Or via the checked-in project config

This repo ships a `.mcp.json` that reads the token from the environment instead
of hardcoding it:

```json
{
  "mcpServers": {
    "quiverquant": {
      "type": "http",
      "url": "https://mcp.quiverquant.com/",
      "headers": { "Authorization": "Bearer ${QUIVER_API_KEY}" }
    }
  }
}
```

Set the variable before launching Claude Code:

```bash
cp .env.example .env       # then paste your token into .env
export QUIVER_API_KEY="$(grep -m1 '^QUIVER_API_KEY=' .env | cut -d= -f2-)"
claude
```

Claude Code expands `${QUIVER_API_KEY}` at connection time, so the secret never
lands in git. On first use it will ask you to approve the project-scoped server.

### Verify

```bash
claude mcp list          # should show: quiverquant ... ✓ Connected
```

---

## Option B — Claude Desktop

Claude Desktop only launches stdio servers, so it needs the `mcp-remote` bridge.
Edit `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "quiverquant": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.quiverquant.com/",
        "--header",
        "Authorization:${AUTH_HEADER}"
      ],
      "env": {
        "AUTH_HEADER": "Bearer YOUR_TOKEN_HERE"
      }
    }
  }
}
```

Two details that are easy to get wrong:

1. `Authorization:${AUTH_HEADER}` has **no space** after the colon, and the value
   is passed through `env` instead of being inlined. This is deliberate —
   `mcp-remote` mis-parses `--header` values containing spaces on some
   platforms, so the space lives inside the env var (`Bearer <token>`).
2. `AUTH_HEADER` must be exactly `Bearer ` + the 40-character token, on one
   line. Nothing else — no username, no plan name, no labels copied from the
   dashboard.

Restart Claude Desktop fully (quit, don't just close the window) after editing.

---

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| `401 Unauthorized` | Token wrong, revoked, or `Bearer ` prefix missing. |
| `403 Forbidden` on CONNECT | Network/egress policy is blocking the host, not an auth problem. See below. |
| Server shows "failed" in `claude mcp list` | Run `claude --debug` and read the handshake error. |
| Works locally, fails in Claude Code on the web | Remote sandboxes have an egress allowlist — see below. |

### Running inside Claude Code on the web / a sandboxed environment

Remote sessions route all outbound traffic through an egress proxy governed by
the environment's network policy. If `mcp.quiverquant.com` is not on the
allowlist, every request fails at the tunnel stage with
`CONNECT tunnel failed, response 403` — before any auth is even attempted.

Fix it by editing the environment's network policy to allow
`mcp.quiverquant.com` (or switching that environment to unrestricted egress).
See https://code.claude.com/docs/en/claude-code-on-the-web for how network
policies and environments are configured.

---

## Rotating the token

If a token is ever pasted into a chat, a screenshot, an issue, or a commit,
treat it as compromised: go to the Quiver account page, regenerate the
Authorization Token, and update `.env` (and any `claude mcp add --scope user`
entry) with the new value.
