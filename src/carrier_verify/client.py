"""Minimal client for the FMCSA QCMobile API.

Get a free web key at https://mobile.fmcsa.dot.gov/QCDevsite/ and set it via
the FMCSA_WEBKEY environment variable or pass it to the client.

All data returned is public U.S. government data.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests

from .models import AuthorityRecord, CarrierSnapshot

BASE_URL = "https://mobile.fmcsa.dot.gov/qc/services"


class QCMobileError(RuntimeError):
    """Raised on API errors after retries are exhausted."""


class QCMobileClient:
    def __init__(
        self,
        webkey: Optional[str] = None,
        base_url: str = BASE_URL,
        timeout: float = 15.0,
        max_retries: int = 2,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.webkey = webkey or os.environ.get("FMCSA_WEBKEY")
        if not self.webkey:
            raise QCMobileError(
                "No FMCSA web key. Set FMCSA_WEBKEY or pass webkey=. "
                "Register free at https://mobile.fmcsa.dot.gov/QCDevsite/"
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = session or requests.Session()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        q = dict(params or {})
        q["webKey"] = self.webkey
        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.get(url, params=q, timeout=self.timeout)
                if resp.status_code == 404:
                    raise QCMobileError(f"Not found: {path}")
                if resp.status_code == 401:
                    raise QCMobileError("Unauthorized: check your FMCSA web key")
                resp.raise_for_status()
                return resp.json()
            except QCMobileError:
                raise
            except (requests.RequestException, ValueError) as err:  # network / bad JSON
                last_err = err
                if attempt < self.max_retries:
                    time.sleep(1.5 * (attempt + 1))
        raise QCMobileError(f"Request failed for {path}: {last_err}")

    # ----- carrier lookups -------------------------------------------------

    def get_carrier(self, dot_number: str) -> CarrierSnapshot:
        return CarrierSnapshot.from_api(self._get(f"carriers/{dot_number}"))

    def get_carrier_raw(self, dot_number: str) -> Dict[str, Any]:
        return self._get(f"carriers/{dot_number}")

    def get_authority(self, dot_number: str) -> AuthorityRecord:
        return AuthorityRecord.from_api(self._get(f"carriers/{dot_number}/authority"))

    def get_oos(self, dot_number: str) -> Dict[str, Any]:
        return self._get(f"carriers/{dot_number}/oos")

    def get_basics(self, dot_number: str) -> Dict[str, Any]:
        return self._get(f"carriers/{dot_number}/basics")

    def get_by_docket(self, docket: str) -> Dict[str, Any]:
        return self._get(f"carriers/docket-number/{docket}")

    def search_by_name(self, name: str, start: int = 0, size: int = 20) -> List[Dict[str, Any]]:
        payload = self._get(f"carriers/name/{name}", params={"start": start, "size": size})
        content = payload.get("content", [])
        return content if isinstance(content, list) else [content]
