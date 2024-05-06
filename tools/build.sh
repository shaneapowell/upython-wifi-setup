

# Compile templates
cd src/www/
python ../../lib/utemplate/utemplate_util.py compile _uwifisetup/welcome.html
echo  -e "\033[0;32m *** IGNORE ***:  ModuleNotFoundError: No module named _uwifisetup/welcome_html *** \033[0m"

python ../../lib/utemplate/utemplate_util.py compile _uwifisetup/list_networks.html
echo  -e "\033[0;32m *** IGNORE ***:  ModuleNotFoundError: No module named _uwifisetup/list_networks_html *** \033[0m"

python ../../lib/utemplate/utemplate_util.py compile _uwifisetup/try_connect.html
echo  -e "\033[0;32m *** IGNORE ***:  ModuleNotFoundError: No module named _uwifisetup/try_connect_html *** \033[0m"

python ../../lib/utemplate/utemplate_util.py compile _uwifisetup/complete.html
echo  -e "\033[0;32m *** IGNORE ***:  ModuleNotFoundError: No module named _uwifisetup/complete_html *** \033[0m"
cd ../../

# pre-mpy compile the lib and templates
wget -nc -q -O tools/mpy_cross_all.py https://raw.githubusercontent.com/micropython/micropython/master/tools/mpy_cross_all.py
python tools/mpy_cross_all.py -o dist src

# Clean up compiled templates
rm src/www/_uwifisetup/*.py




