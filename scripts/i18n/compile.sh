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
    /chia-blockchain/venv/bin/pybabel compile -d ./translations
    chmod -R 777 $PWD/translations
    popd >/dev/null
done
