#
# Launches Machinaris as a standalone full-node with all services
# See: https://github.com/guydavis/machinaris/wiki/Docker#full-node
#
# 1) Install a recent version of Docker for your OS
# 2) Change all uppercase placeholders below to match your system paths and settings
# 3) Change TZ to local TZ_database_name from https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List
# 4) Execute script and browse to http://localhost:8926 to view Machinaris WebUI
# 5) Port-forward tcp/8444 at your router to Chia Network.  Do NOT port forward 8926 which is LAN-only!
#

docker run `
    -d -t `
    --name machinaris `
    -h (hostname) `
    -p 8926:8926 `
    -p 8927:8927 `
    -v C:\Users\USERNAME\.machinaris:/root/.chia:rw `
    -v T:\PATH\TO\TEMP:\:/plotting:rw `
    -v P:\PATH\TO\PLOTS:\:/plots:rw `
    ghcr.io/guydavis/machinaris

# If this is a controller: https://github.com/guydavis/machinaris/wiki/Workers
# Add these options above the image line at end of above run command
#   -p 8927:8927 `
#   --dns (Get-DnsClientServerAddress -AddressFamily IPv4 | Select-Object -ExpandProperty ServerAddresses) `


# If plotting only, see: https://github.com/guydavis/machinaris/wiki/Workers#plotter
# Add these options above the ghcr.io image line at end of above run command
#   -e controller_host=YOUR_CONTROLLER_HOST ` 
#   -e mode=plotter `
#   -e farmer_pk=YOUR_FARMER_PUBLIC_KEY `
#   -e pool_pk=YOUR_POOL_PUBLIC_KEY `
#   If using Plotman to rsync completed plots to final destination
#   -v C:\Users\USERNAME\.ssh\id_rsa:/id_rsa:ro `

# If harvesting only, see: https://github.com/guydavis/machinaris/wiki/Workers#harvester
# Add these options above the image line at end of above run command
#   -e controller_host=YOUR_CONTROLLER_HOST ` 
#   -e mode=harvester `
#   -e farmer_address=FARMER_HOST_NAME `
#   -e farmer_port=8447 `
# Then copy your fullnode/farmer's ca folder over and name it C:\Users\USERNAME\.machinaris\farmer_ca

# If both plotting & harvesting, see: https://github.com/guydavis/machinaris/wiki/Workers#harvesterplotter
# Combine above and add this options above the image line at end of above run command
#   -e mode=harvester+plotter `