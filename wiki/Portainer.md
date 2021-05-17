# TODO

Here's a sample Docker run command from Unraid.  Need to map this to Portainer and provide a good write-up here.

```
docker run -d --name='machinaris' --net='host' -e TZ="America/Denver" -e HOST_OS="Unraid" -e 'TCP_PORT_8555'='8555' -e 'TCP_PORT_8444'='8444' -e 'TCP_PORT_8926'='8926' -e 'keys'='/root/.chia/mnemonic.txt' -v '/mnt/user/appdata/machinaris':'/root/.chia':'rw' -v '/mnt/user/data/crypto/chia/plots':'/plots':'rw' -v '/mnt/temp':'/plotting':'rw' -t 'ghcr.io/guydavis/machinaris'
```

Change the following host paths in above:
* /mnt/user/appdata/machinaris: Will hold the application data, config, and logs for Chia, Plotman, and Machinaris.
* /mnt/user/data/crypto/chia/plots: Will hold the finished plot files after plotting and when farming.
* /mnt/temp: Should be your fast temporary plotting space.