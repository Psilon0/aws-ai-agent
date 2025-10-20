.PHONY: test lint smoke clean ci
test:
\tpytest -q -x
lint:
\tpython -m pyflakes src || true
smoke:
\tbash scripts/smoke.sh
clean:
\tbash scripts/cleanup.sh
ci: clean test
