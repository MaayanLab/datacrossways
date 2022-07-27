#!/bin/bash

echo What is the domain name \(e.g. datacommons.org\)?
read -p 'Domain: ' domain

echo What is the email address for Let\'s Encrypt notifications \(e.g. myemail@admin.org\)?
read -p 'E-mail: ' email

export BASE_URL=$domain
export LETS_ENCRYPT_EMAIL=$email

docker compose up