#
# Via libtorrent, downloads the recent database checkpoint from https://www.chia.net/downloads/
#

import os
import sys
import time
import traceback

import libtorrent as lt

DOWNLOAD_STATUS_FILE='.chiadb_download_size'

try:
    ses = lt.session({'listen_interfaces': '0.0.0.0:6881'})

    info = lt.torrent_info(sys.argv[1])
    h = ses.add_torrent({'ti': info, 'save_path': '.'})
    s = h.status()
    print('Starting torrent download of: ', s.name)

    while (not s.is_seeding):
        s = h.status()

        print('%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % (
            s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000,
            s.num_peers, s.state), end=' ')
        
        # Libtorrent allocates full file size immediately, so write actual downloaded amount to a 
        f = open(DOWNLOAD_STATUS_FILE, "w")
        f.write(str(s.total_download))
        f.close()

        alerts = ses.pop_alerts()
        for a in alerts:
            if a.category() & lt.alert.category_t.error_notification:
                print(a)

        sys.stdout.flush()

        time.sleep(10) # Setup.html refreshes every 10 seconds showing progress bar

    print(h.status().name, 'Database download complete.')
    if os.path.exists(DOWNLOAD_STATUS_FILE):
        os.remove(DOWNLOAD_STATUS_FILE)
except:
    print(h.status().name, 'Database download failed.')
    traceback.print_exc()
