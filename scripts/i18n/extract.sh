#
# Generate messages for internationalization.
#

for d in 'web' 'api'; 
do
    pushd $d >/dev/null
    LANGS=$(grep -oP "LANGUAGES = \[\K(.*)\]" ./default_settings.py | cut -d ']' -f 1 | tr -d \'\" | tr -d ' ')
    IFS=',';
    for lang in $LANGS; 
    do 
        /chia-blockchain/venv/bin/pybabel extract -F babel.cfg -k _l -o messages.pot .
        /chia-blockchain/venv/bin/pybabel update -i messages.pot -d ./translations
        chmod 777 ./translations/$lang/LC_MESSAGES/*
    done
    popd >/dev/null
done
