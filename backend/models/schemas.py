from enum import Enum
from pydantic import BaseModel, Field


class Action(str, Enum):
    RETRY = "retry"
    SCHEDULE_RETRY = "schedule_retry"
    SEND_PAYMENT_LINK = "send_payment_link"
    ESCALATE = "escalate"
    STOP = "stop"


class RecoveryCase(BaseModel):
    payment_id: str
    customer_id: str
    amount: float = Field(gt=0)
    failure_reason: str
    attempt_number: int = Field(ge=1)
    payment_method: str
    customer_lifetime_value: float = Field(ge=0)
    customer_total_payments: int = Field(ge=0)
    customer_success_rate: float = Field(ge=0, le=1)
    customer_failure_rate: float = Field(ge=0, le=1)
    average_payment: float = Field(ge=0)
    days_since_last_success: int = Field(ge=0)
    recovery_probability: float = Field(ge=0, le=1)


class AgentDecision(BaseModel):
    action: Action
    delay_hours: int | None = Field(default=None, ge=0, le=168)
    reason: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(ge=0, le=1)


class PolicyDecision(BaseModel):
    approved: bool
    final_action: Action
    reason: str
    requires_human: bool = False


class RecoveryResult(BaseModel):
    payment_id: str
    proposed_action: Action
    final_action: Action
    policy_approved: bool
    requires_human: bool
    success: bool
    outcome_status: str
    amount_recovered: float
    reason: str
    audit_id: str
    external_payment_link_id: str | None = None
    external_payment_link_url: str | None = None
