set -eu -o pipefail
HASH1=$(find dist -type f | sort | sha1sum -b)
pipenv run compile
HASH2=$(find dist -type f | sort | sha1sum -b)
echo "Hash1 [$HASH1]"
echo "Hash2 [$HASH2]"
if [ "$HASH1" != "$HASH2" ]; then
echo "Re-Build of dist folder produced different hash. Did you forget to pre-build?"
exit 1
else
echo "Hash Values match.  dist looks good"
fi