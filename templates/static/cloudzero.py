"""
CloudZero API Client

Handles uploading CBF (Common Billing Format) data to CloudZero AnyCost Streams.
This file is copied verbatim into generated adaptors.
"""

import os
import json
import requests
from pathlib import Path


class CloudZeroClient:
    """Client for the CloudZero AnyCost Stream API."""

    def __init__(self):
        self.api_key = os.getenv("CLOUDZERO_API_KEY")
        self.connection_id = os.getenv("CLOUDZERO_CONNECTION_ID")
        self.api_url = os.getenv("CLOUDZERO_API_URL", "https://api.cloudzero.com")

        if not self.api_key:
            raise ValueError("CLOUDZERO_API_KEY environment variable is required")
        if not self.connection_id:
            raise ValueError("CLOUDZERO_CONNECTION_ID environment variable is required")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        })

    def test_connection(self) -> bool:
        """Test the CloudZero API connection."""
        try:
            url = f"{self.api_url}/v2/connections/{self.connection_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"CloudZero connection test failed: {e}")
            return False

    def upload_cbf(self, cbf_file_path: str) -> dict:
        """Upload a CBF CSV file to CloudZero.

        Args:
            cbf_file_path: Path to the CBF CSV file.

        Returns:
            API response dict.
        """
        path = Path(cbf_file_path)
        if not path.exists():
            raise FileNotFoundError(f"CBF file not found: {cbf_file_path}")

        url = f"{self.api_url}/v2/connections/{self.connection_id}/anycost"

        with open(path, "r") as f:
            cbf_content = f.read()

        payload = {
            "records": cbf_content,
        }

        response = self.session.post(url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        print(f"CloudZero upload successful: {result.get('records_accepted', 'unknown')} records accepted")
        return result

    def upload_records(self, records: list[dict]) -> dict:
        """Upload CBF records directly as a list of dicts.

        Args:
            records: List of CBF record dicts.

        Returns:
            API response dict.
        """
        url = f"{self.api_url}/v2/connections/{self.connection_id}/anycost"

        payload = {
            "records": records,
        }

        response = self.session.post(url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        print(f"CloudZero upload successful: {result.get('records_accepted', 'unknown')} records accepted")
        return result
