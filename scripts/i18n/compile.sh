#
# Compile current messages.po into messages.mo for use at runtime.
#

# If building on Github servers, change to deployment root
if [ "$PWD" != '/code/machinaris' ]; then  # else stay in code root
    cd /machinaris
fi

for d in 'web' 'api'; 
do
    pushd $d >/dev/null
    LANGS=$(grep -oP "LANGUAGES = \[\K(.*)\]" ./default_settings.py | cut -d ']' -f 1 | tr -d \'\" | tr -d ' ')
    IFS=',';
    for lang in $LANGS; 
    do 
        pybabel compile -d ./translations
        chmod 777 ./translations/$lang/LC_MESSAGES/*
    done
    popd >/dev/null
done
