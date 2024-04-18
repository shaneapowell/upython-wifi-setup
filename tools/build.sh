

# Compile templates
cd src/www/
python ../../lib/utemplate/utemplate_util.py compile _uwifisetup/welcome.html
python ../../lib/utemplate/utemplate_util.py compile _uwifisetup/list_networks.html
python ../../lib/utemplate/utemplate_util.py compile _uwifisetup/try_connect.html
python ../../lib/utemplate/utemplate_util.py compile _uwifisetup/complete.html
cd ../../

# pre-mpy compile the lib
wget -nc -q -O tools/mpy_cross_all.py https://raw.githubusercontent.com/micropython/micropython/master/tools/mpy_cross_all.py
python tools/mpy_cross_all.py -o dist src

# Clean up compiled templates
rm src/www/_uwifisetup/*.py

# Copy all asset files to dist
rsync -av src/www/_uwifisetup/assets dist/www/_uwifisetup



