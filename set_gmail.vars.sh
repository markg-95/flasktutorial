#!/bin/bash

# Setup test email server for production.



export MAIL_SERVER=smtp.gmail.com
export MAIL_PORT=587
export MAIL_USE_TLS=1
export MAIL_USERNAME="mark.getrost805@gmail.com"
export MAIL_PASSWORD="andffunky90P"

echo MAIL_SERVER: $MAIL_SERVER
echo MAIL_PORT: $MAIL_PORT
echo MAIL_USERNAME: $MAIL_USERNAME
