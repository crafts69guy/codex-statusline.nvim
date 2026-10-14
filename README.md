# codex-statusline.nvim

A tiny Fish launcher that enables Codex's native colored footer in this order:
project name, Git branch, model with reasoning effort, context remaining.
The footer lives inside Codex's terminal UI; it creates no separate pane.

Illustrative text preview (colors are rendered by Codex):

```text
my-project · main · gpt-6.1-sol medium · 92% left
```

Runtime dependencies: Fish and Codex. Verified with Codex 0.162.1.

Install all three bundled Hue custom themes once from the repository root,
including when upgrading an existing launcher installation:

```fish
set -l codex_theme_home ~/.codex
if set -q CODEX_HOME
    set codex_theme_home $CODEX_HOME
end
mkdir -p "$codex_theme_home/themes"
cp -n themes/hue-*.tmTheme "$codex_theme_home/themes/"
```

This uses your custom `CODEX_HOME` when set and preserves any existing
`hue-*.tmTheme` files. To refresh installed copies after an update, review or back
up those files and deliberately replace them with the bundled versions. The launcher
never installs or updates theme files; without the custom theme, Codex falls
back to its native default.

Install the repository anywhere and put its executable launcher on PATH:

```fish
mkdir -p ~/.local/bin
ln -s /path/to/codex-statusline.nvim/bin/codex-statusline ~/.local/bin/codex-statusline
codex-statusline
codex-statusline --mood huong -- resume SESSION_ID
codex-statusline --mood=cung -- 'prompt with spaces'
codex-statusline --cd ~/project resume SESSION_ID
codex-statusline fork SESSION_ID
```

The symlink works from any directory. The optional leading `--mood` accepts
`mua` (default), `huong`, or `cung`; `--mood=<id>` is also supported. An optional
leading `--` separates wrapper flags. Invalid or missing moods fail before
Codex starts. Remaining arguments pass unchanged to Codex,
including noninteractive commands, help, and version. `exec` keeps Codex's PID,
terminal, signal handling, and exit status. Fish runs without startup config.

The launcher supplies `tui.status_line`, `tui.status_line_use_colors=true`, and
`tui.theme=hue-<mood>` before your arguments. The selected Hue theme supplies syntax
colors, the `codex.accent` foreground, and inserted/deleted diff foregrounds and
backgrounds, and overrides your global theme for launcher sessions. Native footer
foregrounds derive from these theme colors, with Codex applying its own contrast
and saturation adjustments. The terminal background and native footer's per-field
styles remain controlled by Codex and your terminal. CLI custom themes use
TextMate `.tmTheme` files, as documented in
[CLI customization](https://learn.chatgpt.com/docs/cli-customization).
Later explicit overrides take precedence:

```fish
codex-statusline -c 'tui.status_line=["model-with-reasoning","context-used"]'
codex-statusline -c tui.status_line_use_colors=false
codex-statusline -c tui.theme=catppuccin-latte
```

Use `/statusline` to customize the native fields and `/theme` to choose a theme.
These commands are documented in
[Codex developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli),
and the settings in the [config schema](https://learn.chatgpt.com/docs/config-schema.json).
The launcher reapplies its footer and theme preset each launch; choose explicit
overrides or edit the preset for a lasting change to launcher sessions.

Native fields do not include the previous custom context graphics, Git diff
counts, or active agent list. The former Herdr/Lua observer has been removed.
The launcher does not read session history, query Herdr, or write global config.
Plain `codex` and `orch codex` use your global Codex footer settings instead.

To make plain `codex` (and wrappers such as `orch codex`) use Hue, declare the
same preset in `$CODEX_HOME/config.toml` (default `~/.codex/config.toml`):

```toml
[tui]
theme = "hue-mua"
status_line = ["project-name", "git-branch", "model-with-reasoning", "context-remaining"]
status_line_use_colors = true
```

Symlinking the themes instead of copying them keeps installed copies current, so
regenerated files apply on the next session. Point the links at this repository's
`themes/` or at a hue-theme checkout's `packages/codex-cli-themes/themes/`:

```fish
for mood in mua huong cung
    ln -sf /path/to/codex-statusline.nvim/themes/hue-$mood.tmTheme "$codex_theme_home/themes/"
end
```

The launcher's `--mood` still overrides the global theme for a single session.

Development checks need Python 3 in addition to Fish:

```fish
make check
```

Tests validate the bundled theme's plist, palette, and essential scopes, and
use fake Codex/Herdr executables to check the preset, argument forwarding,
symlink invocation, exit status, PID, terminal inheritance, and native signals.
They never invoke real Codex or control a Herdr session.

Uninstall the launcher by removing its symlink:

```fish
rm ~/.local/bin/codex-statusline
```

The terminal Hue mood is selected separately; the wrapper chooses a Codex theme
at startup. Changing `/theme` mid-session does not change the terminal mood.
To remove installed themes too, explicitly remove `hue-mua.tmTheme`,
`hue-huong.tmTheme`, and `hue-cung.tmTheme` from your `$CODEX_HOME/themes` (or
`~/.codex/themes`) after backing up any local changes.

MIT licensed. The three bundled Hue themes are copied verbatim from
[hue-theme](https://github.com/crafts69guy/hue-theme) and retain its upstream
license in [themes/LICENSE](themes/LICENSE).
