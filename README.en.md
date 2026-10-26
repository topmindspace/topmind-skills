# topmind Skills

Bring the topmind personal-knowledge workflow to your AI assistant (Claude Code, Codex, Cursor, OpenCode, Hermes and others). Say "save this", "organize this week" or "turn it into a draft", and the assistant stores everything in your own `topmind-workspace` folder under one shared set of conventions. Skill text is written in Chinese.

[简体中文](README.md) · [English](README.en.md) · [Install guide](./INSTALL.md) · [Changelog](./CHANGELOG.md) · [Product](https://github.com/topmindspace/topmind) · [npm](https://www.npmjs.com/package/@topmindspace/topmind-skills)

## Install

```bash
npx @topmindspace/topmind-skills add topmindspace/topmind-skills -g
```

Then say "topmind" or just ask for what you need. To upgrade:

```bash
npx @topmindspace/topmind-skills update -g
```

- A newer packaged skill overwrites the installed copy and prints `Upgraded <skill> <old> -> <new>`; the same version prints `Already up to date`; a newer installed version is kept unless you pass `--force`.
- To install for some assistants only, add `-a claude-code -a codex` to `add`.
- The community CLI `npx skills add topmindspace/topmind-skills -g -y` also works, but it leaves out the `shared/` folder, so some rules cannot be read. See [INSTALL.md](./INSTALL.md#社区-cli-npx-skills) for the extra step.
- Pinned or offline installs, project scope and per-assistant folders are covered in [INSTALL.md](./INSTALL.md).

## Usage

Expose only `topmind` as the daily entry. It decides which skill handles your request, so you never need to remember sub-skill names.

| You say | Handled by | Result |
|---|---|---|
| "Save this link" | `topmind-capture` | Stored in the weekly stream, a topic or the Inbox; the receipt says where |
| "Remind me to do X" | `topmind-capture` | Material saved, to-do written to `memory/todo.md` |
| "What's on my list?" | `topmind` | Open items from `memory/todo.md` |
| "Organize this week", "summarize this topic" | `topmind-organize` | Tidies the week's stream or organizes, compares and distills a topic |
| "Write it up", "polish this" | `topmind-write` | Drafts or revises into the delivery folder or the topic |
| "Remember that I…", "update my profile" | `topmind-memory` | Updates `memory/profile.md` or a periodic reflection |
| "Run a health check", "doctor" | `topmind-maintain` | Checks folder structure and config, with reversible cleanup |
| "Run the loop" | `topmind-loop` | Walks every topic and can resume after an interruption |
| "Sync WeRead" | `topmind-weread` | Optional: syncs WeRead highlights and notes into topics |
| "Post to X", "archive my posts" | `topmind-x` | Optional: X archive, search and posting |
| "Log 35 for lunch" | `topmind-ledger` | Optional: bookkeeping in `memory/ledgers/` |

The pack has 10 skills: the `topmind` entry, 6 actions, 2 optional connectors and 1 optional ledger. See [skills.md](./skills.md).

### Companion skills (installed separately)

These are not part of this pack. When installed, `topmind` hands matching requests to them; otherwise it falls back to `topmind-write` or explains in the receipt.

| Need | Skill | Repository |
|---|---|---|
| WeChat articles, X articles, short posts, covers, long images | `topmind-wechat-post` and 7 other writing skills | [topmind-writing-skills](https://github.com/topmindspace/topmind-writing-skills) |
| AI industry news, papers, number checks | `topmind-research` | [topmind-research](https://github.com/topmindspace/topmind-research) |
| Turn material into paged HTML and PPTX | `topmind-presentation` | [topmind-presentation](https://github.com/topmindspace/topmind-presentation) |
| Hand memory over between tools | `topmind-handoff` | [topmind-handoff](https://github.com/topmindspace/topmind-handoff) |

Routing between them is defined in [`shared/trigger-disambiguation.md`](./shared/trigger-disambiguation.md).

## Where content lives

Everything is plain Markdown in your local `topmind-workspace`, readable in Obsidian or any editor.

```text
topmind-workspace/
├── topmind.yaml          # workspace config
├── memory/               # profile, reflections, to-dos, ledgers
├── 00-Inbox/             # anything not yet classified
├── 10-动态/              # weekly stream notebooks
├── …                     # other categories from your template; rename, hide or add
├── 88-交付/              # finished drafts
└── 99-归档/
```

- When enough notes share a theme, they gather into a topic folder `{category}/{YYYY-theme}/`; until then notes sit at the category root.
- Categories do not overlap, topics emerge, the stream stays flat, the Inbox is cleared about every 30 days, references live apart, and category names stay stable. Full rules: [`shared/project-model-brief.md`](./shared/project-model-brief.md).

## Conventions

- **Save first**: unclear items go to the Inbox; imperfect classification never blocks a save.
- **Every write has a receipt**: which file, why there, and what you can do next.
- **Save settings**: `writeback_mode: auto | confirm`. auto writes and returns a receipt; confirm also saves content edits directly and queues deletion/archive for review. Explicitly requested topic or memory changes reuse your authorization; inferred suggestions need acceptance; see [`shared/auto-suggest.md`](./shared/auto-suggest.md).
- **Files are the only source of truth**: assistant session state must not become topmind content truth.
- **Desktop is not required, UTR is optional**: without topmind Desktop or the UTR CLI, the assistant uses its own file tools under the same conventions.
- **Nothing is posted for you**: skills only draft; you publish.

## For maintainers

- Version and skill list come from [`topmind-pack.json`](./topmind-pack.json) (`npm run versions`); every `SKILL.md` `metadata.version` must match.
- `SKILL.md` frontmatter uses only Agent Skills spec fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`); custom fields go under `metadata` as strings. CI checks each skill with `agentskills validate`.
- Run tests with `npm test`. Release steps are in [INSTALL.md](./INSTALL.md#发布维护者).

```text
topmind-skills/
├── topmind/              # daily entry (router)
├── topmind-capture/ … topmind-loop/   # 6 action skills
├── topmind-weread/  topmind-x/        # optional connectors
├── topmind-ledger/       # optional ledger
├── shared/               # rules shared by all skills
├── install-targets/      # install shapes per assistant
├── integrations/         # Codex, Hermes, OpenCode notes
├── evals/                # routing evals
├── bin/install-skills.mjs
└── topmind-pack.json
```

## License

MIT
