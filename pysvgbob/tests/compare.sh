#!/bin/bash
# Compare the Python port against the reference svgbob binary.
# usage: tests/compare.sh file.bob... (default: the crate's test_data)
here=$(cd "$(dirname "$0")/.." && pwd)
files=("$@")
[ ${#files[@]} -eq 0 ] && files=("$here"/../svgbob/crates/svgbob/test_data/*.bob)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail=0
for f in "${files[@]}"; do
    svgbob "$f" > "$tmp/ref.svg"
    start=$(date +%s.%N)
    PYTHONPATH="$here" python3 -m svgbob "$f" > "$tmp/py.svg"
    t=$(echo "$(date +%s.%N) - $start" | bc)
    if cmp -s "$tmp/ref.svg" "$tmp/py.svg"; then
        printf "SAME %6.2fs %s\n" "$t" "$f"
    else
        n=$(diff "$tmp/ref.svg" "$tmp/py.svg" | grep -c '^[<>]')
        printf "DIFF %6.2fs %s (%d lines)\n" "$t" "$f" "$n"
        fail=1
    fi
done
exit $fail
