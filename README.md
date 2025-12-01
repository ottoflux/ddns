# ddns
A simple dynamic DNS service for use with Linode API for domain management.

## manual runs
Use .env or sent env vars for manual runs:

TOKEN=[your Linode API token - NOTE, create an extra user with limited access]

DOMAIN=[domain name, e.g. foo.com]

HOST=[ddns hostname / subdomain]

## OR for a service
Use /etc/ddns/secrets.env (as root, restrict permissions to go-rwx / 600) for TOKEN env var.

Use something like this for your /etc/systemd/system/ddns-updater.service file:
```
[Unit]
Description=Linode DDNS Updater
Wants=network-online.target
After=network-online.target

[Service]
# Set the working directory
WorkingDirectory=/opt/ddns

# Specify the user to run the script as (best practice)
User=ddns-user

# Load the secret variables from the protected file - root 0600
EnvironmentFile=/etc/ddns/secrets.env

# Define environment variables (for configuration)
Environment=DOMAIN=example.com
Environment=HOST=home

# NOTE: Use the full path to the Venv interpreter to make sure you're runing with your venv.
ExecStart=/opt/ddns/venv/bin/python /opt/ddns/ddns.py 

# Restart the service if it exits with an error
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

and then you'll want to run (after setting up your venv):
```
sudo systemctl daemon-reload
sudo systemctl enable --now ddns-updater.timer
```
