#!/bin/bash

echo What is the domain name \(e.g. datacommons.org\)?
read domain

echo What is the email address for Let\'s Encrypt notifications \(e.g. myemail@admin.org\)?
read email

#docker compose up