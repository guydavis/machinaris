#!/bin/bash
# Pull all 3rd party libs / icons into web/static/3rd_party folder

# Bootstrap Icons
BSI_VERSION=1.7.2
BOOTSTRAP_VERSION=5.1.3
BASEPATH=/machinaris/web/static/3rd_party

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
wget -nv -O bsi-icons.zip "https://github.com/twbs/icons/releases/download/v${BSI_VERSION}/bootstrap-icons-${BSI_VERSION}.zip" && \
unzip -o bsi-icons.zip -d $BASEPATH/ && \
mv $BASEPATH/bootstrap-icons-${BSI_VERSION} $BASEPATH/icons && \
rm -f bsi-icons.zip

# Bootstrap
wget -O bs.zip -nv "https://github.com/twbs/bootstrap/releases/download/v${BOOTSTRAP_VERSION}/bootstrap-${BOOTSTRAP_VERSION}-dist.zip" && \
unzip -o -j bs.zip -d $BASEPATH/ bootstrap-${BOOTSTRAP_VERSION}*/css/bootstrap.min.css* bootstrap-${BOOTSTRAP_VERSION}*/js/bootstrap.bundle.min.js*  && \
rm -f bs.zip
