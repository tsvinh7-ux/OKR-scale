#!/bin/bash
# Run the automated tests of every OKR module on a throw-away database.
set -e
export PGHOST="${PGHOST:-db}" PGUSER="${PGUSER:-odoo}" PGPASSWORD="${PGPASSWORD:-odoo}"
DB="okr_test_$(date +%s)"
TAGS=/okr_scale,/okr_scale_project,/okr_scale_cfr,/okr_scale_reward,/okr_scale_reward_stock,/okr_scale_portal,/okr_scale_template,/okr_scale_review
MODULES=okr_scale,okr_scale_project,okr_scale_cfr,okr_scale_reward,okr_scale_reward_stock,okr_scale_portal,okr_scale_template,okr_scale_review

until pg_isready -q; do sleep 1; done
LOG=/tmp/okr_tests.log
CONF="${OKR_CONF:-/etc/odoo/odoo.conf}"
odoo -c "$CONF" -d "$DB" -i "$MODULES" --without-demo=all --load-language=vi_VN \
     --test-tags "$TAGS" --stop-after-init --http-port 8070 --log-level=test > "$LOG" 2>&1 || true
grep -E "tests\.(stats|result)|(ERROR|FAIL):" "$LOG" || true
dropdb --if-exists "$DB" || true
if grep -q "tests.result: 0 failed, 0 error(s)" "$LOG" && ! grep -qE " CRITICAL |Failed to load registry" "$LOG"; then
    echo "[okr] ALL TESTS PASSED"
else
    echo "[okr] TESTS FAILED - last lines of $LOG:"; tail -n 60 "$LOG"; exit 1
fi
