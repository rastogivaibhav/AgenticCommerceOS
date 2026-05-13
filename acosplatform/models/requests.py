"""Pydantic request/response models for ACOS APIs."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


# ── Valid tenant IDs ───────────────────────────────────────────────────────────
def get_valid_tenants() -> set:
    """Return current set of valid tenant IDs. Evaluated lazily at validation time."""
    try:
        from acosplatform.tenancy.manager import list_tenants
        return {t["id"] for t in list_tenants()}
    except Exception:
        return {"default", "eu-store", "jp-store", "in-store"}


class JourneyRequest(BaseModel):
    """Validated payload for POST /journey (Shopper API)."""

    message: str = Field(..., min_length=1, max_length=500,
                         description="Natural language customer message")
    customer_id: str = Field(
        default="anon",
        max_length=64,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Customer identifier — alphanumeric, hyphens, underscores only",
    )
    tenant_id: str = Field(default="default", max_length=32)
    order_id: Optional[str] = Field(default=None, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    category: Optional[str] = Field(default=None, max_length=64, pattern=r"^[a-zA-Z0-9_\- ]+$")
    points_to_redeem: int = Field(default=0, ge=0, le=10000)
    condition: Optional[Literal["opened", "unopened"]] = None

    @field_validator("tenant_id")
    @classmethod
    def tenant_must_be_valid(cls, v: str) -> str:
        valid = get_valid_tenants()
        if v not in valid:
            raise ValueError(f"tenant_id must be one of {sorted(valid)}")
        return v

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be blank or whitespace-only")
        return v
