#
# Initialize translation files for each supported language.
#

for d in 'web' 'api'; 
do
    pushd $d >/dev/null
    LANGS=$(grep -oP "LANGUAGES = \[\K(.*)\]" ./default_settings.py | cut -d ']' -f 1 | tr -d \'\" | tr -d ' ')
    IFS=',';
    for lang in $LANGS; 
    do 
        if [[ "$lang" == 'en' ]]; then
            continue  # No separate translation files for default locale
        fi
        if [ -d ./translations/$lang ]; then
            echo "Skipping initialization of $d/$lang as translations folder already exists."
        else
            /chia-blockchain/venv/bin/pybabel init -i messages.pot -d ./translations -l $lang
            chmod 777 ./translations/$lang/LC_MESSAGES/*
        fi
    done
    popd >/dev/null
done
