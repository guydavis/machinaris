#!/bin/bash
#
# Due to complaints about JS CDNs, this pulls all JS libs into web/static/3rd_party folder
#

# Bootstrap and Icons
BSI_VERSION=1.11.3
BOOTSTRAP_VERSION=5.3.3
BASEPATH=${JS_LIBS_BASEPATH:-/machinaris/web/static/3rd_party}

# Mapping library
LEAFLET_VERSION=1.9.4

# List of other css/js links
LIST="
https://cdn.datatables.net/2.1.8/css/dataTables.bootstrap5.css
https://cdn.datatables.net/2.1.8/js/dataTables.bootstrap5.js
https://cdn.datatables.net/2.1.8/js/dataTables.min.js
https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.js.map
https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js
https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon@1.3.1/dist/chartjs-adapter-luxon.umd.min.js
https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js
https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js
https://cdn.jsdelivr.net/npm/luxon@3.5.0/build/global/luxon.min.js"

mkdir -p $BASEPATH
for url in $LIST ; do
  wget -nv -O ${BASEPATH}/$(basename $url) "$url"
done

# Bootstrap Icons
wget -nv -O ${BASEPATH}/bsi-icons.zip "https://github.com/twbs/icons/releases/download/v${BSI_VERSION}/bootstrap-icons-${BSI_VERSION}.zip"
unzip -q -o ${BASEPATH}/bsi-icons.zip -d $BASEPATH/
mv $BASEPATH/bootstrap-icons-${BSI_VERSION} $BASEPATH/icons
mv ${BASEPATH}/icons/font/* ${BASEPATH}/icons/
rmdir ${BASEPATH}/icons/font/ 
rm -f ${BASEPATH}/bsi-icons.zip

# Bootstrap
wget -O ${BASEPATH}/bs.zip -nv "https://github.com/twbs/bootstrap/releases/download/v${BOOTSTRAP_VERSION}/bootstrap-${BOOTSTRAP_VERSION}-dist.zip" && \
unzip -q -o -j ${BASEPATH}/bs.zip -d $BASEPATH/ bootstrap-${BOOTSTRAP_VERSION}*/css/bootstrap.min.css* bootstrap-${BOOTSTRAP_VERSION}*/js/bootstrap.bundle.min.js*  && \
rm -f ${BASEPATH}/bs.zip

# Leaflet and plugins
wget -O ${BASEPATH}/leaflet.zip -nv "https://leafletjs-cdn.s3.amazonaws.com/content/leaflet/v${LEAFLET_VERSION}/leaflet.zip" && \
unzip -q -o ${BASEPATH}/leaflet.zip -d $BASEPATH/ && \
rm -f ${BASEPATH}/leaflet.zip
wget -O ${BASEPATH}/leaflet-layervisibility.js -nv "https://unpkg.com/leaflet-layervisibility/dist/leaflet-layervisibility.js"
sed -i 's/\/\/# sourceMapping.*//g' ${BASEPATH}/leaflet-layervisibility.js

# Pull localization files for DataTables.js
mkdir -p $BASEPATH/i18n/
LANGS=$(grep -oP "LANGUAGES = \[\K(.*)\]" $BASEPATH/../../default_settings.py | cut -d ']' -f 1 | tr -d \'\" | tr -d ' ')
IFS=',';
for lang in $LANGS; 
do
  if [[ "$lang" == 'en' ]]; then
      continue  # No separate translation files for default locale
  fi

  lang_hyphen=${lang/_/-}
  wget -nv -O ${BASEPATH}/i18n/datatables.${lang}.json https://raw.githubusercontent.com/DataTables/Plugins/master/i18n/${lang_hyphen}.json
  if [ $? == 0 ]; then
    echo "Successfully downloaded DataTables language translations for ${lang}."
  else
    echo "ERROR: Failed to download DataTables language translations for ${lang}."
  fi
done
