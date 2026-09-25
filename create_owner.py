"""
One-time CLI script to securely provision an Owner (Admin) account for Checkup Buddy.
Owners cannot self-register through the public web UI.
"""

import sys
import os
import argparse
import getpass
import hashlib
import secrets

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database

PBKDF2_ITERATIONS = 100_000


def hash_password(password: str, salt_hex: str = None) -> tuple[str, str]:
    """Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
    if salt_hex is None:
        salt_bytes = secrets.token_bytes(16)
        salt_hex = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt_hex)

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        PBKDF2_ITERATIONS
    )
    return derived.hex(), salt_hex


def main():
    parser = argparse.ArgumentParser(description="Provision an Owner account for Checkup Buddy.")
    parser.add_argument("--username", help="Owner username")
    parser.add_argument("--email", help="Owner email address")
    parser.add_argument("--mobile", help="Owner mobile number", default="")
    parser.add_argument("--password", help="Owner password (if omitted, prompts securely)")
    args = parser.parse_args()

    database.init_db()

    print("=" * 60)
    print("      CHECKUP BUDDY — OWNER ACCOUNT PROVISIONING")
    print("=" * 60)

    username = args.username or input("Enter Owner username [default: admin]: ").strip() or "admin"
    email = args.email or input("Enter Owner email: ").strip()

    if not email or "@" not in email:
        print("[ERROR] A valid email address is required.")
        sys.exit(1)

    # Check if email or username already exists
    if database.get_user_by_email(email):
        print(f"[ERROR] User with email '{email}' already exists.")
        sys.exit(1)

    if database.get_user_by_username(username):
        print(f"[ERROR] User with username '{username}' already exists.")
        sys.exit(1)

    mobile = args.mobile
    if not mobile and not args.email:
        mobile = input("Enter Owner mobile number (optional): ").strip()

    if args.password:
        password = args.password
    else:
        password = getpass.getpass("Enter Owner password: ")
        confirm = getpass.getpass("Confirm Owner password: ")
        if password != confirm:
            print("[ERROR] Passwords do not match.")
            sys.exit(1)

    if len(password) < 6:
        print("[ERROR] Password must be at least 6 characters long.")
        sys.exit(1)

    pwd_hash, salt = hash_password(password)

    user_id = database.create_user(
        role="owner",
        username=username,
        email=email,
        mobile=mobile,
        password_hash=pwd_hash,
        salt=salt,
        email_verified=1,
        mobile_verified=1
    )

    print(f"\n[SUCCESS] Owner account created successfully!")
    print(f"User ID: {user_id}")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Role: owner")
    print("=" * 60)


if __name__ == "__main__":
    main()
