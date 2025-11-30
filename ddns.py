#!/usr/bin/env python3
import requests
import sys
import logging
import json
import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
LINODE_TOKEN = os.getenv("TOKEN")
DOMAIN_NAME = os.getenv("DOMAIN")
RECORD_NAME = os.getenv("HOST")
API_URL = "https://api.linode.com/v4"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def get_headers():
    return {
        "Authorization": f"Bearer {LINODE_TOKEN}",
        "Content-Type": "application/json",
    }


def get_public_ip():
    """Gets the current public IP address of this machine."""
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=10)
        response.raise_for_status()
        return response.json()["ip"]
    except Exception as e:
        logging.error(f"Failed to get public IP: {e}")
        sys.exit(1)


def get_domain_id():
    """Finds the internal Linode ID for the domain name."""
    url = f"{API_URL}/domains"
    headers = get_headers()

    # Use json.dumps to safely format the filter
    filters = {"domain": DOMAIN_NAME}
    headers["X-Filter"] = json.dumps(filters)

    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json()

        if data["results"] == 0:
            logging.error(f"Domain {DOMAIN_NAME} not found in Linode account.")
            sys.exit(1)

        return data["data"][0]["id"]
    except Exception as e:
        logging.error(f"Error fetching domain ID: {e}")
        sys.exit(1)


def get_record_details(domain_id):
    """Finds the specific A record ID and current target IP."""
    url = f"{API_URL}/domains/{domain_id}/records"
    headers = get_headers()

    filters = {"type": "A", "name": RECORD_NAME}
    headers["X-Filter"] = json.dumps(filters)

    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json()

        if data["results"] == 0:
            logging.error(f"Record '{RECORD_NAME}' not found in {DOMAIN_NAME}.")
            sys.exit(1)

        # Return the whole record object so we have ID and current Target
        return data["data"][0]
    except Exception as e:
        logging.error(f"Error fetching record ID: {e}")
        sys.exit(1)


def update_dns(domain_id, record_id, new_ip):
    """Updates the Linode DNS record."""
    url = f"{API_URL}/domains/{domain_id}/records/{record_id}"
    payload = {"target": new_ip}

    try:
        res = requests.put(url, headers=get_headers(), json=payload)
        res.raise_for_status()
        logging.info(f"SUCCESS: DNS updated to {new_ip}")
    except Exception as e:
        logging.error(f"FAILED: Linode API update failed - {e}")


def main():
    # 1. Get current external IP
    current_ip = get_public_ip()

    # 2. Get Linode Data
    domain_id = get_domain_id()
    record_data = get_record_details(domain_id)

    linode_ip = record_data["target"]
    record_id = record_data["id"]

    # 3. Compare and Update if necessary
    if current_ip == linode_ip:
        logging.info(f"No change needed. IP is still {current_ip}")
    else:
        logging.info(
            f"IP Change Detected! Linode has {linode_ip}, current is {current_ip}"
        )
        update_dns(domain_id, record_id, current_ip)


if __name__ == "__main__":
    main()
