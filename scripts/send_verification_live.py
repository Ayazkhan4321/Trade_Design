"""CLI to call the send-verification endpoint for debugging.

Usage:
  python scripts/send_verification_live.py --email john@example.com
  python scripts/send_verification_live.py --phone +11234567890

This script imports the existing service function `send_verification` and
prints the raw result plus any HTTP response body logged by the service.
"""
import argparse
import os
import sys

# Ensure package imports work when running from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Create_Account.create_account_service import send_verification
import logging
logging.basicConfig(level=logging.DEBUG)


def main():
    p = argparse.ArgumentParser(description="Send verification code to an email or phone for debugging")
    p.add_argument("--email", help="Email address to send verification to")
    p.add_argument("--phone", help="Phone number to send verification to")
    args = p.parse_args()

    if not args.email and not args.phone:
        print("Provide --email or --phone")
        sys.exit(2)

    payload = {}
    if args.email:
        payload["email"] = args.email
    if args.phone:
        payload["phone"] = args.phone

    ok, msg, retry = send_verification(payload)
    print("Result:")
    print("  success:", ok)
    print("  message:", msg)
    print("  retryable:", retry)


if __name__ == '__main__':
    main()
