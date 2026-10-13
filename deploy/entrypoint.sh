#!/bin/bash
# Start Odoo for the DMAG OKR suite.
# First start: create the database, install every OKR module with the DMAG demo data.
set -e

DB="${OKR_DB:-dmag_okr}"
MODULES="${OKR_MODULES:-okr_scale_demo}"
CONF="${OKR_CONF:-/etc/odoo/odoo.conf}"
export PGHOST="${PGHOST:-db}" PGUSER="${PGUSER:-odoo}" PGPASSWORD="${PGPASSWORD:-odoo}"

echo "[okr] waiting for PostgreSQL..."
until pg_isready -q; do sleep 1; done

if ! psql -lqt | cut -d'|' -f1 | grep -qw "$DB"; then
    echo "[okr] first start: creating database '$DB' with $MODULES (2-4 minutes)..."
    odoo -c "$CONF" -d "$DB" -i "$MODULES" --load-language=vi_VN --without-demo=all --stop-after-init
    echo "[okr] database ready."
elif [ "${OKR_UPDATE:-0}" = "1" ]; then
    echo "[okr] updating all modules of '$DB'..."
    odoo -c "$CONF" -d "$DB" -u all --stop-after-init
fi

echo "[okr] Odoo is starting on http://localhost:8069 (login admin / admin)"
exec odoo -c "$CONF" -d "$DB" "$@"
