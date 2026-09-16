"""Pairing helper - prints a QR code encoding the daemon WS URL + auth token."""

from __future__ import annotations

import argparse
import logging
import sys

import psutil
import qrcode

from kaow.config import Settings, load_settings

TAILSCALE_NETWORK = (100, 64)  # 100.64.0.0/10 CGNAT range used by Tailscale


def build_pairing_url(settings: Settings, address: str) -> str:
    """Build the ws:// URL a phone needs to connect, token embedded as query."""
    return f"ws://{address}:{settings.port}/ws?token={settings.auth_token}"


def detect_tailscale_ip() -> str | None:
    """Return the first IPv4 bound to Tailscale's CGNAT range, if any."""
    addrs = psutil.net_if_addrs()
    for iface, entries in addrs.items():
        if "tailscale" not in iface.lower():
            continue
        for entry in entries:
            ip = entry.address
            if entry.family.name == "AF_INET" and ip and _is_tailscale(ip):
                return ip
    return None


def _is_tailscale(ip: str) -> bool:
    try:
        parts = [int(p) for p in ip.split(".")]
    except ValueError:
        return False
    if len(parts) != 4:
        return False
    return parts[0] == TAILSCALE_NETWORK[0] and 64 <= parts[1] <= 127


def print_qr(url: str) -> None:
    """Render the URL as an ASCII QR code."""
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)
    print()


def main() -> None:
    """Entry point for `kaow-pair`."""
    parser = argparse.ArgumentParser(description="Print a KAOW pairing QR code")
    parser.add_argument(
        "--address",
        help="Tailnet address (IP or magic DNS name) for the phone to reach",
    )
    args = parser.parse_args()

    settings = load_settings()
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger("kaow.pair")

    address = args.address or detect_tailscale_ip()
    if address is None:
        logger.error("No Tailscale interface found. Pass --address <tailnet-ip-or-name>.")
        sys.exit(1)

    url = build_pairing_url(settings, address)
    print(f"KAOW pairing code - scan with the mobile app (address: {address})\n")
    print_qr(url)
    print(f"Manual entry:\n  URL: {url.split('?')[0]}\n  Token: {settings.auth_token}")


if __name__ == "__main__":
    main()
