# trading-public-file

## Camoufox MCP server

Browser automation via [Camoufox](https://github.com/whit3rabbit/camoufox-mcp), a
privacy-focused Firefox fork with anti-detection features.

The server is configured at project scope in [`.mcp.json`](.mcp.json), so anyone
who clones this repo gets it. Claude Code prompts once to approve a
project-scoped server; approve it and the tools load on the next session start.

Tools are exposed as `mcp__camoufox__<name>`.

### Stateless — navigate once, return data

| Tool | Returns |
| --- | --- |
| `camoufox_status` | Server, browser, queue, session, and policy status without launching a page |
| `browse` | Bounded page content |
| `browse_snapshot` | Visible text, ARIA snapshot, and interactive metadata |
| `browse_sequence` | Runs bounded selector actions, then returns final state |
| `browse_links` | Visible navigable links only |
| `browse_forms` | Form fields and submit controls |
| `browse_outline` | Page headings and landmarks |
| `browse_find` | Visible-text search with bounded context matches |
| `browse_screenshot` | Bounded screenshot |
| `browse_console` | Bounded console diagnostics |
| `browse_network_summary` | Bounded network diagnostic summary |

### Stateful — isolated short-lived sessions

| Tool | Purpose |
| --- | --- |
| `browse_session_start` | Start an isolated short-lived browser session |
| `browse_session_navigate` | Navigate an existing session |
| `browse_session_action` | Run one bounded action in a session |
| `browse_session_snapshot` | Read current session state |
| `browse_session_resume` | Resume a paused session after human action |
| `browse_session_close` | Close a session |

### Notes

- The server package is fetched by `npx` on first run. The Camoufox browser build
  it drives downloads separately on first actual browse, which needs outbound
  network access.
- Verified against `camoufox-mcp-server@2.5.0`; `@latest` in `.mcp.json` tracks
  new releases. Pin the version there if you need reproducibility.
