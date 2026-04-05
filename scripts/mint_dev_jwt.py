#!/usr/bin/env python3
"""Mint local dev JWT tokens for Ops API role testing."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone


ROLES = ("admin", "ops", "analyst")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate dev JWTs for ACOS Ops API.")
    parser.add_argument(
        "--role",
        choices=ROLES,
        help="Role claim to mint. Omit with --all to mint all standard roles.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate tokens for admin, ops, and analyst.",
    )
    parser.add_argument(
        "--subject",
        default="dev-user",
        help="JWT subject claim. Default: dev-user",
    )
    parser.add_argument(
        "--ttl-hours",
        type=int,
        default=24,
        help="Token TTL in hours. Default: 24",
    )
    parser.add_argument(
        "--secret",
        default=os.environ.get("OPS_JWT_SECRET", ""),
        help="JWT secret. Defaults to OPS_JWT_SECRET env var.",
    )
    parser.add_argument(
        "--issuer",
        default="acos-local-dev",
        help="Issuer claim. Default: acos-local-dev",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output tokens as JSON.",
    )
    return parser


def _mint_token(secret: str, role: str, subject: str, issuer: str, ttl_hours: int) -> str:
    try:
        import jwt  # PyJWT
    except ImportError as exc:  # pragma: no cover - utility script
        raise RuntimeError("PyJWT is required. Install with: pip install pyjwt") from exc

    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "roles": [role],
        "iss": issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=ttl_hours)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.secret:
        print("Missing JWT secret. Set OPS_JWT_SECRET or pass --secret.", file=sys.stderr)
        return 2

    if args.ttl_hours <= 0:
        print("--ttl-hours must be > 0", file=sys.stderr)
        return 2

    if not args.all and not args.role:
        parser.error("Provide --role <admin|ops|analyst> or use --all")

    roles = list(ROLES) if args.all else [args.role]
    tokens = {}
    for role in roles:
        subject = args.subject if not args.all else f"{args.subject}-{role}"
        tokens[role] = _mint_token(
            secret=args.secret,
            role=role,
            subject=subject,
            issuer=args.issuer,
            ttl_hours=args.ttl_hours,
        )

    if args.json:
        print(json.dumps(tokens, indent=2))
        return 0

    for role in roles:
        print(f"{role.upper()}_TOKEN={tokens[role]}")
    return 0


if __name__ == "__main__":  # pragma: no cover - utility entrypoint
    raise SystemExit(main())
