"""Probe the send-verification endpoint with a few variants to find what the server accepts.

Usage: python scripts/probe_send_verification.py --email you@example.com

It will try:
 - POST JSON {email: ...}
 - POST form-urlencoded
 - GET ?email=...
 - POST JSON with 'contact' envelope

Prints status code and response body for each attempt.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.config import API_ACCOUNTS_SEND
import requests


def try_post_json(url, payload):
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)


def try_post_form(url, payload):
    try:
        r = requests.post(url, data=payload, timeout=10)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)


def try_get(url, params):
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--email', required=True)
    args = p.parse_args()

    url = API_ACCOUNTS_SEND
    print('Endpoint:', url)

    print('\n1) POST JSON {"email": ...}')
    s, b = try_post_json(url, {'email': args.email})
    print('Status:', s)
    print('Body:', b)

    print('\n2) POST form data (email=...)')
    s, b = try_post_form(url, {'email': args.email})
    print('Status:', s)
    print('Body:', b)

    print('\n3) GET ?email=...')
    s, b = try_get(url, {'email': args.email})
    print('Status:', s)
    print('Body:', b)

    print('\n4) POST JSON enveloped {"contact":{"email":...}}')
    s, b = try_post_json(url, {'contact': {'email': args.email}})
    print('Status:', s)
    print('Body:', b)

    print('\nDone')

if __name__ == '__main__':
    main()
