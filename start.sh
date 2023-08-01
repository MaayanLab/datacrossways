#!/bin/bash

echo "What is the domain name (e.g. datacommons.org)?"
read -p 'Domain: ' domain

echo "What is the email address for Let's Encrypt notifications (e.g. myemail@admin.org)?"
read -p 'E-mail: ' email

echo 'y' | ~/datacrossways/stop.sh

export BASE_URL=$domain
export LETS_ENCRYPT_EMAIL=$email

# check Docker version and use the correct command
if docker -v | grep -q "Docker version 2"; then
    docker compose up
else
    docker-compose up
fi