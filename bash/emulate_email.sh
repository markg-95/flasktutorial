#!/bin/bash

# Setup test email server for production. 

echo "Emulating email server. Press 'control+c' to quit."

export MAIL_PORT=8025
export MAIL_SERVER=localhost
python -m smtpd -n -c DebuggingServer localhost:8025

