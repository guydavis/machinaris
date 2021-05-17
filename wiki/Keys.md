Key management can be accomplished using the CLI tools within the container.  For example, if your Machinaris container was named 'machinaris': 

```
docker exec -it machinaris bash
$ chia wallet show
```

The Docker container places your private key mnemonic in a text file named: 

`/root/.chia/mnemonic.txt`

The container will create a new one if not found.  You can replace that with your existing key mnemonic if you chose.

NOTE: **For security, Machinaris will NEVER read from this file or display it in any way through the WebUI.**  You must view/edit it via your filesystem mounts or through a `docker exec -it` into the container.
