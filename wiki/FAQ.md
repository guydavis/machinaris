# Frequently Asked Questions

## Plotting

## Farming

### How come Machinaris shows zero plots farming right after restart?

Some users, particularly those with lots of plots, have reported that the main Machinaris status (and `chia farm summary` behind the scenes) report zero plots on initial start up, even when plots exist in the `/plots` directory.  This generally resolves itself as Chia catches up on syncing/startup so just wait a while and check later.  One user reported 30 minutes for them once.

## Security

### Why doesn't Machinaris offer an authentication mechanism to allow logins?

Machinaris is a simple web app for access to your blockchain and plotting.  It is intended for use on your local area network only, but you may choose to [proxy access](./wiki/Nginx) to it via other web servers.  If you do this, then your web server should have many means of securing/authenticating access to proxy targets such as Machinaris.  The onus is on you to configure this correctly for you particular setting. 