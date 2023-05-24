#!/usr/bin/env python3

import argparse
import os
import smtplib
from collections import defaultdict
from email.message import EmailMessage


def main(sample_file, email):
    """Parse a textfile with run info and report on any origins failing >10% of samples via email."""

    # Quick sanity checks
    sanity_checks(sample_file, email)

    # Read sample_file into list containing quota of failed qc_status per origin
    status_list = parse_samples(sample_file)

    # Send an email to the address specified if any origin failed too much
    if len(status_list) > 0:
        send_mail(status_list, email, sample_file)


def parseArgs():
    parser = argparse.ArgumentParser(
        description='Parse a textfile with run info and report on any origins failing >10% of samples via email.')
    parser.add_argument('--sample_file', help='Path to txt-file with sample info (required)', required=True)
    parser.add_argument('--email', help='email to send result (required)', required=True)
    arguments = parser.parse_args()
    return arguments


def sanity_checks(sample_file, email):
    """Checks that the sample-file and the email looks alright."""

    # Does the input-file exist?
    if not os.path.exists(sample_file) or not os.path.isfile(sample_file):
        print(f"File {sample_file} does not appear to exist...")
        print(f"Exiting...")
        exit(1)

    # Check that the email looks decent
    if not "@" in email:
        print(f"You gave {email} as email. Is this a real address? It doesn't contain an @...")
        print(f"Exiting...")
        exit(1)

    # Check that the header of the input looks decent
    with open(sample_file, 'r') as sf:
        header = sf.readline().rstrip().split(",")
        if not len(header) == 6 or header[5] != "qc_pass":
            print(f"Header on {sample_file} looks odd. Expected 6 headers, and qc_pass.")
            print(f"Exiting...")
            exit(1)


def parse_samples(sample_file):
    """Parse the samplefile into a dict with origin and qc_status"""

    # Read samples into a dict
    sample_dict = defaultdict(list)
    with open(sample_file, 'r') as sf:
        next(sf)
        for line in sf:
            sample_id = line.split(',')[0]
            origin = sample_id.split('-')[0]
            qc_status = line.split(',')[5].rstrip()
            sample_dict[origin].append(qc_status)

    # Count quota of samples that failed
    status_list = []
    for ori in sample_dict.keys():
        passed = sample_dict[ori].count("TRUE")
        total = len(sample_dict[ori])
        quota = 1 - (passed / total)
        if quota >= 0.1:
            status_list.append(f"{ori}, {quota}")

    return status_list  # Return list of origins with failed quota >10%


def send_mail(status_list, email, sample_file):
    """Send a mail if status on sample qc if any origin failed."""

    body = '\n'.join([f'During parsing of {sample_file} there were origins that failed >10% of samples:',
                      'origin, quota_failed',
                      '\n'.join(status_list)])
    subject = f'Sample parse status'

    msg = EmailMessage()
    msg.set_content(body)

    msg['Subject'] = subject
    msg['From'] = "emilio.rudbeck@gu.se"
    msg['To'] = email

    # Send the message
    try:
        s = smtplib.SMTP('smtp.gu.se')
        s.send_message(msg)
        s.quit()
    except Exception:
        raise


if __name__ == '__main__':
    arguments = parseArgs()
    main(arguments.sample_file, arguments.email)
