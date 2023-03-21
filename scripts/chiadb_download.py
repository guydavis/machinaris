#
# Via libtorrent, downloads the recent database checkpoint from https://www.chia.net/downloads/
#

import sys
import time
import traceback

import libtorrent as lt

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

        alerts = ses.pop_alerts()
        for a in alerts:
            if a.category() & lt.alert.category_t.error_notification:
                print(a)

        sys.stdout.flush()

        time.sleep(30)

    print(h.status().name, 'Database download complete.')
except:
    print(h.status().name, 'Database download failed.')
    traceback.print_exc()
