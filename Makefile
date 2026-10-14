.PHONY: test check
test:
	python3 tests/launcher.py
check: test
	fish -n bin/codex-statusline
