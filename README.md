# IMAP-Alerter
Monitors mailboxes over IMAP and sends an email alert over SMTP.
Checks the mailbox for unread messages. In case there are any and no alert was sent for them, a new alert is sent. An unique ID for each message is saved in `data/alerted.pickle`. This way the app only notifies you once.

## How to use
1. Clone the repo
2. Copy `config/config.template.yaml` to `config/config.yaml`
3. Complete the config file
4. Start `main.py`

## Using Docker
1. Pull or build the docker container
2. Copy `config/config.template.yaml` to your pc
3. Complete the config file
4. Mount this file as volume in the docker container to `/app/config/config.yaml`
5. (Optionally) Mount a folder to `/app/data`. This folder stores the alerts which have been sent in the past.
6. Start the image