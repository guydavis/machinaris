#
# Generate messages for internationalization.
#

for d in 'web' 'api'; 
do
    pushd $d >/dev/null
    /chia-blockchain/venv/bin/pybabel extract -F babel.cfg -k _l -o messages.pot .
    /chia-blockchain/venv/bin/pybabel update -i messages.pot -d ./translations
    chmod -R 777 $PWD/translations
    popd >/dev/null
done
