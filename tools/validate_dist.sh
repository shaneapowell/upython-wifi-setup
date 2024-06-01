set -eu -o pipefail

# Before
HASH1=$(find dist -type f | sort | xargs sha256sum)

pipenv run clean
pipenv run compile

# After
HASH2=$(find dist -type f | sort | xargs sha256sum)


echo -e "HASH1\n$HASH1"
echo -e "HASH2\n$HASH2"

if [ "$HASH1" != "$HASH2" ]; then
echo "Re-Build of dist folder produced different hash. Did you forget to pre-build?"
exit 1
fi


echo "Hash Values match.  dist looks good"
