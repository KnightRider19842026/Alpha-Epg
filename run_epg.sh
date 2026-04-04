#!/bin/bash

# -------------------------------
# Script για EPG κάθε 2 μέρες
# -------------------------------

echo "=== EPG Update Ξεκίνησε: $(date) ==="

# Βάλε εδώ την εντολή που τρέχει το πρόγραμμα σου
# Παράδειγμα 1: Αν είναι Python script
/usr/bin/python3 /home/USER/alpha_epg.py >> /home/USER/epg_log.txt 2>&1

# Παράδειγμα 2: Αν είναι executable
#/home/USER/alpha_epg >> /home/USER/epg_log.txt 2>&1

echo "=== EPG Update Τέλειωσε: $(date) ===" 
echo "----------------------------------------"
