#!/bin/bash
#
# Due to complaints about JS CDNs, this pulls all JS libs into web/static/3rd_party folder
#

# Bootstrap Icons
BSI_VERSION=1.7.2
BOOTSTRAP_VERSION=5.1.3
BASEPATH=${JS_LIBS_BASEPATH:-/machinaris/web/static/3rd_party}

# List of other css/js links
LIST="
https://cdn.datatables.net/1.10.25/css/dataTables.bootstrap5.css
https://cdn.datatables.net/1.10.25/js/dataTables.bootstrap5.js
https://cdn.datatables.net/1.10.25/js/jquery.dataTables.js
https://cdn.jsdelivr.net/npm/chart.js@3.5.0/dist/chart.min.js
https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon@1.1.0/dist/chartjs-adapter-luxon.min.js
https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.min.js
https://moment.github.io/luxon/global/luxon.min.js"

mkdir -p $BASEPATH
for url in $LIST ; do
  wget -nv -O ${BASEPATH}/$(basename $url) "$url"
done

# Bootstrap Icons
wget -nv -O ${BASEPATH}/bsi-icons.zip "https://github.com/twbs/icons/releases/download/v${BSI_VERSION}/bootstrap-icons-${BSI_VERSION}.zip" && \
unzip -o ${BASEPATH}/bsi-icons.zip -d $BASEPATH/ && \
mv $BASEPATH/bootstrap-icons-${BSI_VERSION} $BASEPATH/icons && \
rm -f ${BASEPATH}/bsi-icons.zip

# Bootstrap
wget -O ${BASEPATH}/bs.zip -nv "https://github.com/twbs/bootstrap/releases/download/v${BOOTSTRAP_VERSION}/bootstrap-${BOOTSTRAP_VERSION}-dist.zip" && \
unzip -o -j ${BASEPATH}/bs.zip -d $BASEPATH/ bootstrap-${BOOTSTRAP_VERSION}*/css/bootstrap.min.css* bootstrap-${BOOTSTRAP_VERSION}*/js/bootstrap.bundle.min.js*  && \
rm -f ${BASEPATH}/bs.zip

# Leaflet
wget -O ${BASEPATH}/leaflet.zip -nv "https://leafletjs-cdn.s3.amazonaws.com/content/leaflet/v1.7.1/leaflet.zip" && \
unzip -o ${BASEPATH}/leaflet.zip -d $BASEPATH/ && \
rm -f ${BASEPATH}/leaflet.zip

# Pull localization files for DataTables.js
mkdir -p $BASEPATH/i18n/
LANGS=$(grep -oP "LANGUAGES = \[\K(.*)\]" $BASEPATH/../../default_settings.py | cut -d ']' -f 1 | tr -d \'\" | tr -d ' ')
IFS=',';
for lang in $LANGS; 
do
  if [[ "$lang" == 'en' ]]; then
      continue  # No separate translation files for default locale
  fi
  # First try $lang.json
  wget -nv -O ${BASEPATH}/i18n/datatables.${lang}.json https://raw.githubusercontent.com/DataTables/Plugins/master/i18n/${lang}.json
  if [ $? != 0 ]; then # Then try $lang_$lang.json  (Example French)
    echo "Going for ${lang}_${lang}.json"
    wget -nv -O ${BASEPATH}/i18n/datatables.${lang}.json https://raw.githubusercontent.com/DataTables/Plugins/master/i18n/${lang}_${lang}.json
  fi
done
