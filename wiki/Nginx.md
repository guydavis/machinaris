Machinaris supports proxying via Nginx and other web servers.  I use [SWAG](https://docs.linuxserver.io/general/swag) (Nginx + Let's Encrypt) on Unraid.  

NOTE: Machinaris does not provide it's own authentication so you must wrap it with .htaccess, Authelia, LDAP, etc to ensure it is not exposed incorrectly.

## Proxy Root Path

If you just want your external DNS name to serve up Machinaris (with authentication - see above!), then just use something like this:

```
    client_max_body_size 0;

    # enable for ldap auth, fill in ldap details in ldap.conf
    #include /config/nginx/ldap.conf;

    # enable for Authelia
    #include /config/nginx/authelia-server.conf;

    location / {
        # enable the next two lines for http auth
        #auth_basic "Restricted";
        #auth_basic_user_file /config/nginx/.htpasswd;

        # enable the next two lines for ldap auth
        #auth_request /auth;
        #error_page 401 =200 /ldaplogin;

        # enable for Authelia
        #include /config/nginx/authelia-location.conf;

        include /config/nginx/proxy.conf;
        resolver 127.0.0.11 valid=30s;
        set $upstream_app lidarr;
        set $upstream_port 8686;
        set $upstream_proto http;
        proxy_pass $upstream_proto://$upstream_app:$upstream_port;

    }
```

## Proxy Subfolder Path

If you want Machinaris to respond to `http://MYSERVER.net/machinaris` (notice the subfolder in path), then your web server should set the `SCRIPT_NAME` header.  Here is a sample config for use with the SWAG container, widely used on Unraid:

```
location ^~ /machinaris {
    # enable the next two lines for http auth
    #auth_basic "Restricted";
    #auth_basic_user_file /config/nginx/.htpasswd;

    # enable the next two lines for ldap auth, also customize and enable ldap.conf in the default conf
    #auth_request /auth;
    #error_page 401 =200 /ldaplogin;

    # enable for Authelia, also enable authelia-server.conf in the default site config
    #include /config/nginx/authelia-location.conf;

    include /config/nginx/proxy.conf;
    resolver 127.0.0.11 valid=30s;
    set $upstream_app $upstream_app;
    set $upstream_port $upstream_port;
    set $upstream_proto http;
    proxy_set_header SCRIPT_NAME /machinaris;
    proxy_pass $upstream_proto://$upstream_app:$upstream_port;

}
```

Big thanks to @Allram on Discord for suggesting that Machinaris build in proxy support from day one!