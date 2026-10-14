"""Exercise the actual launcher with fake commands, including a real PTY."""
import json
import os
from pathlib import Path
import plistlib
import pty
import signal
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
PRESET = [
    "-c",
    'tui.status_line=["project-name","git-branch","model-with-reasoning","context-remaining"]',
    "-c",
    "tui.status_line_use_colors=true",
    "-c",
    "tui.theme=hue-mua",
]

with (ROOT / "themes/hue-mua.tmTheme").open("rb") as source:
    theme = plistlib.load(source)
assert theme["name"] == "hue-mua"
assert theme["settings"][0]["settings"]["background"] == "#001F3E"
assert theme["settings"][0]["settings"]["foreground"] == "#E5F4FF"
scopes = {
    scope.strip(): entry["settings"]
    for entry in theme["settings"] if "scope" in entry
    for scope in entry["scope"].split(",")
}
for scope, color in {
    "comment": "#6B819A",
    "string": "#00CF6A",
    "constant.numeric": "#FF8D00",
    "keyword": "#8A7BFF",
    "entity.name.function": "#10B6F8",
    "markup.deleted": "#FF5A63",
}.items():
    assert scopes[scope]["foreground"] == color, scope

for mood in ('mua', 'huong', 'cung'):
    with (ROOT / f'themes/hue-{mood}.tmTheme').open('rb') as source:
        themed = plistlib.load(source)
    assert themed['name'] == f'hue-{mood}'
    mood_scopes = {entry.get('scope'): entry['settings'] for entry in themed['settings']}
    assert 'codex.accent' in mood_scopes
    assert 'background' in mood_scopes['markup.inserted']
    assert 'background' in mood_scopes['markup.deleted']

with tempfile.TemporaryDirectory(prefix="codex-statusline-tests-") as directory:
    temp = Path(directory)
    record = temp / "record.json"
    herdr_calls = temp / "herdr-calls"
    codex = temp / "codex"
    codex.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, signal, sys\n"
        "with open(os.environ['RECORD'], 'w') as output:\n"
        "    json.dump({'argv': sys.argv[1:], 'pid': os.getpid(),\n"
        "               'tty': [os.isatty(fd) for fd in (0, 1, 2)]}, output)\n"
        "if os.environ.get('WAIT_FOR_SIGNAL'):\n"
        "    while True: signal.pause()\n"
        "sys.exit(37)\n"
    )
    herdr = temp / "herdr"
    herdr.write_text('#!/bin/sh\necho invoked >> "$HERDR_CALLS"\nexit 99\n')
    codex.chmod(0o755)
    herdr.chmod(0o755)
    launcher = temp / "launcher"
    launcher.symlink_to(ROOT / "bin/codex-statusline")
    env = dict(os.environ, PATH=f"{temp}:{os.environ['PATH']}",
               RECORD=str(record), HERDR_CALLS=str(herdr_calls),
               HERDR_ENV="1", HERDR_PANE_ID="origin")
    for arguments in (
        ["--cd", "directory with spaces", "a 'quoted' prompt", "", "line\nbreak"],
        ["-c", 'tui.status_line=["context-used"]', "-c", "tui.status_line_use_colors=false"],
        ["-c", "tui.theme=catppuccin-latte", "--cd", "directory with spaces", "resume", "session"],
        ["--cd", "directory with spaces", "resume", "session"],
        ["fork", "session"],
        ["exec", "prompt with spaces"],
        ["--help"],
        ["--version"],
    ):
        child = subprocess.run([str(launcher), *arguments], cwd=temp, env=env,
                               capture_output=True, timeout=5)
        assert child.returncode == 37, child.stderr
        assert json.loads(record.read_text())["argv"] == PRESET + arguments

    for flags, mood in ((['--mood', 'huong'], 'huong'), (['--mood=cung'], 'cung'),
                        (['--mood', 'mua', '--'], 'mua'), (['--'], 'mua')):
        arguments = ['resume', "quote ' space", '', 'line\nbreak', '-c', 'tui.theme=override']
        child = subprocess.run([str(launcher), *flags, *arguments], cwd=temp, env=env,
                               capture_output=True, timeout=5)
        assert child.returncode == 37, child.stderr
        preset = PRESET[:-1] + [f'tui.theme=hue-{mood}']
        assert json.loads(record.read_text())['argv'] == preset + arguments
    for arguments in (['--mood'], ['--mood='], ['--mood', 'unknown']):
        record.unlink(missing_ok=True)
        child = subprocess.run([str(launcher), *arguments], env=env,
                               capture_output=True, timeout=5)
        assert child.returncode != 0 and child.stderr and not record.exists()

    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        record.unlink(missing_ok=True)
        master, slave = pty.openpty()
        child = subprocess.Popen([str(launcher), "resume", "session"], cwd=temp,
                                 env=dict(env, WAIT_FOR_SIGNAL="1"),
                                 stdin=slave, stdout=slave, stderr=slave)
        try:
            deadline = time.monotonic() + 5
            while True:
                try:
                    data = json.loads(record.read_text())
                    break
                except (FileNotFoundError, json.JSONDecodeError):
                    assert time.monotonic() < deadline, "fake Codex did not start"
                    time.sleep(0.01)
            assert data["pid"] == child.pid, "launcher must exec Codex"
            assert data["tty"] == [True, True, True], "terminal must pass through"
            assert data["argv"] == PRESET + ["resume", "session"]
            child.send_signal(signum)
            assert child.wait(timeout=5) == -signum, "native signal exit must pass through"
        finally:
            if child.poll() is None:
                child.kill()
                child.wait()
            os.close(slave)
            os.close(master)

    assert not herdr_calls.exists(), "launcher must never invoke Herdr"

print("Native footer launcher assertions passed")
