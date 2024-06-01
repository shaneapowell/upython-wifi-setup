HASH1=$(find dist -type f | sort | sha1sum)
pipenv run compile
HASH2=$(find dist -type f | sort | sha1sum)
if [[ "$HASH1" != "$HASH2" ]]; then
echo "Re-Build of dist folder produced different hash. Did you forget to pre-build?"
exit 1
fi