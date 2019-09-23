#     imap-alerter - Monitors IMAP mailboxes and sends alerts on new mails through SMTP
#     Copyright (C) 2019  Jens Willemsens
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Simple polling monitor for IMAP mailboxes.
In case of new mails, it sends a mail alert through SMTP.

@author: Jens Willemsens <jens@jensw.be> May 2019
"""

from email.message import EmailMessage
from pathlib import Path
import imaplib
import logging as log
import pickle
import smtplib
import sys
import time
import yaml

# GLOBAL VARS
config = {}


def load_config(path, glob):
    global config
    for filename in Path(path).glob(glob):
        with filename.open(mode='r') as file_config:
            config = yaml.safe_load(file_config)

    if config == {}:
        log.error('No config file found')
        exit(1)


def load_alerted():
    try:
        with open('data/alerted.pickle', 'rb') as file_alerted:
            return pickle.load(file_alerted)
    except FileNotFoundError:
        return dict()


def dump_alerted(uid_alerted):
    with open('data/alerted.pickle', 'wb') as file_alerted:
        pickle.dump(uid_alerted, file_alerted)


def poll_unseen(monitor):
    log.debug('Polling for unseen messages ...')
    account = imaplib.IMAP4_SSL(monitor['imap_host'], monitor['imap_port'])
    account.login(monitor['username'], monitor['password'])
    account.select(config.get('default_folder', 'INBOX'))
    _, data = account.uid('search', None, 'UNSEEN')
    uid_unseen = set(data[0].split())
    account.close()
    account.logout()
    log.debug('{} unseen messages found'.format(len(uid_unseen)))
    return uid_unseen


def send_alert(alert, count):
    log.debug('Send alerts')
    
    # Basic message
    msg = EmailMessage()
    msg.set_content("FYI, {} new message(s) received.".format(count))
    
    # Set subject
    monitor = config['accounts'][alert['monitor']]
    msg['Subject'] = alert.get('subject', 'New mail received at {}'.format(monitor['username']))
    
    # Set sender
    sender = config['accounts'][alert['sender']]
    msg['From'] = sender.get('smtp_from', sender['username'])
    if msg['From'] == '':
        msg['From'] = sender['username']

        # Connect to sender
    with smtplib.SMTP(sender['smtp_host'], sender['smtp_port']) as server:
        server.starttls()
        server.login(sender['username'], sender['password'])
        
        # Send alerts
        for receiver in alert['alert']:
            del msg['To']
            msg['To'] = receiver
            server.send_message(msg)
    
        # Close server connection
        server.quit()


def run():
    # Get alerted UID's
    uid_alerted = load_alerted()

    # Infinite polling
    while 1:
        for alert in config['alerts']:
            monitor = config['accounts'][alert['monitor']]
            uid_unseen = poll_unseen(monitor)

            if len(uid_unseen):
                uid_alerted_mon = uid_alerted.get(alert['monitor'], set())
                uid_new = uid_unseen.difference(uid_alerted_mon)
                if len(uid_new):
                    # Sending alert
                    log.info("Sending alert for {} messages with UID's: {}".format(len(uid_new), b", ".join(uid_new)))
                    send_alert(alert, len(uid_new))

                    # Update and save alerted UID's
                    uid_alerted_mon.update(uid_new)
                    uid_alerted[alert['monitor']] = uid_alerted_mon
                    dump_alerted(uid_alerted)
                else:
                    log.info('No new messages found')

        # Timeout
        sleep_mins = config.get('polling_time', 15)
        log.debug('Sleeping for {} minute(s)'.format(sleep_mins))
        time.sleep(sleep_mins * 60)


def main():
    # Setup logging
    log.basicConfig(stream=sys.stderr, level=log.DEBUG)

    # Load config
    load_config('config', 'config.y*ml')  # Sets global "config" variable

    # Start polling
    run()
    

if __name__ == '__main__':
    main()
