#!/usr/bin/env bash
# ==============================================================================
# create_input_sim.sh  —  Generate a solver input file
#
# Usage:
#   ./create_input_sim.sh <city> <mesh> <angle_idx> 
#
# Arguments:
#   city        City name string  (e.g. shenzhen, athens)
#   mesh        Mesh identifier   (e.g. 1, 2, coarse)
#   angle_idx   Wind angle index  (0–7):
#
# Examples:
#   ./create_input_sim.sh shenzhen 1 0
#   ./create_input_sim.sh athens   2 3 --dry-run
# ==============================================================================

# ── user configuration ─────────────────────────────────────────────────────────
TEMPLATE="CITY_MESH_cir_windANGLE.in"
OUTPUT_DIR="."
# ──────────────────────────────────────────────────────────────────────────────


# ── argument parsing ───────────────────────────────────────────────────────────
DRY_RUN=0
POSITIONAL=()
for arg in "$@"; do
    POSITIONAL+=("$arg") 
done

if [[ ${#POSITIONAL[@]} -ne 3 ]]; then
    sed -n '2,30p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'
    exit 1
fi

CITY="${POSITIONAL[0]}"
MESH="${POSITIONAL[1]}"
ANGLE_IDX="${POSITIONAL[2]}"

# ── validate inputs ────────────────────────────────────────────────────────────
if [[ ! "$ANGLE_IDX" =~ ^[0-7]$ ]]; then
    echo "[create_input_sim] ERROR: angle_idx must be an integer 0–7, got '${ANGLE_IDX}'."
    exit 1
fi

if [[ ! -f "$TEMPLATE" ]]; then
    echo "[create_input_sim] ERROR: Template not found: ${TEMPLATE}"
    exit 1
fi

OUT_FILE="${OUTPUT_DIR}/${CITY}_r1200_${MESH}_wind${ANGLE_IDX}.in"


# ── generate input file ────────────────────────────────────────────────────────
# Replace <CITY>, <MESH>, <ANGLE> in the (now-updated) template.
awk -v city="$CITY" \
    -v mesh="$MESH" \
    -v angle_idx="$ANGLE_IDX" \
'
BEGIN {
    angle_rad = angle_idx * atan2(0,-1) / 4
    # inflow: 4 segments centered upstream of wind direction
    # for angle index k: (k-2)%8, (k-1)%8, k%8, (k+1)%8
    for (i = 0; i < 4; i++)
        inflow[(angle_idx - 2 + i + 8) % 8] = 1
}
 
{
    gsub(/<CITY>/,  city)
    gsub(/<MESH>/,  mesh)
    gsub(/<ANGLE>/, angle_idx)
}
 
/^DEFINE basenm/ {
    print
    printf "DEFINE ANGLE %.10f  # %d (%d deg)\n", angle_rad, angle_idx, angle_idx * 45
    next
}
 
/^S[0-7][[:space:]]/ {
    seg = substr($1, 2, 1) + 0
    if (seg in inflow)
        printf "%-12s=CBC_PROFILE FILENAME ./wind_profile.txt RHO $(RHOINF) P $(PINF) A $(ANGLE)\n", $1
    else
        printf "%-12s=NSCBC_OUTLET_P P_REF $(PINF) L_REF 2400\n", $1
    next
}
 
{ print }
' "$TEMPLATE" > "$OUT_FILE"
 
echo "[launch_sim] Input file written  →  $(realpath "$OUT_FILE")"
