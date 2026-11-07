UV ?= uv
RUN = $(UV) run --locked --offline --no-sync

.PHONY: help sync sync-store check check-store schema env verify
help:
	@echo "sync | sync-store | check | check-store | schema | env | lab-NN | verify-NN | verify"
	@echo "Native Windows: uv run --locked --offline --no-sync python -m common.cli ..."
sync:
	$(UV) sync --locked
sync-store:
	$(UV) sync --locked --group mooncake
check:
	$(RUN) python -m common.cli check
check-store:
	$(RUN) python -m pytest -m integration
schema:
	$(RUN) python -m common.cli schema
env:
	$(RUN) python env/check_env.py
lab-%:
	UV="$(UV)" sh labs/$*-*/run.sh
verify-%:
	$(RUN) python -m common.cli verify $*
verify:
	$(RUN) python -m common.cli verify all
