from ..agent.recovery_agent import RecoveryAgent
from ..models.schemas import Action, RecoveryCase, RecoveryResult
from ..policies.policy_engine import PolicyEngine
from ..tools.payment_tools import PaymentTools
from ..tools.customer_tools import CustomerTools
from ..tools.ops_tools import OpsTools
from .audit_service import AuditService
from .outcome_service import OutcomeService


class RecoveryService:
    def __init__(self, agent=None):
        self.agent = agent or RecoveryAgent()
        self.policy = PolicyEngine()
        self.payment_tools = PaymentTools()
        self.customer_tools = CustomerTools()
        self.ops_tools = OpsTools()
        self.audit = AuditService()
        self.outcomes = OutcomeService()
        self.external_recoveries = {}

    def reconcile_external_payment(
        self,
        payment_id: str,
        razorpay_payment_id: str,
        amount_rupees: float,
        payment_link_id: str | None = None,
    ) -> dict:
        """Reconcile a real Razorpay Test/Live webhook into the audit trail.

        This is deliberately separate from the synthetic OutcomeService: an
        external captured/payment-link-paid event is authoritative for the
        actual payment amount received.
        """
        payload = {
            "razorpay_payment_id": razorpay_payment_id,
            "amount_recovered": round(amount_rupees, 2),
            "payment_link_id": payment_link_id,
            "source": "razorpay_webhook",
        }
        self.audit.record("RAZORPAY_PAYMENT_CONFIRMED", payment_id, payload)
        self.external_recoveries[payment_id] = {
            "payment_id": payment_id,
            "status": "recovered",
            "amount_recovered": round(amount_rupees, 2),
            "razorpay_payment_id": razorpay_payment_id,
            "payment_link_id": payment_link_id,
            "source": "razorpay_webhook",
        }
        event_id = self.audit.record(
            "OUTCOME_VERIFIED",
            payment_id,
            {
                "status": "recovered",
                "amount_recovered": round(amount_rupees, 2),
                "message": "Recovery verified from Razorpay webhook.",
                "source": "razorpay_webhook",
                "razorpay_payment_id": razorpay_payment_id,
            },
        )
        return {
            "status": "reconciled",
            "payment_id": payment_id,
            "razorpay_payment_id": razorpay_payment_id,
            "amount_recovered": round(amount_rupees, 2),
            "audit_id": event_id,
        }

    def recover(self, case: RecoveryCase) -> RecoveryResult:
        self.audit.record(
            "CASE_DETECTED",
            case.payment_id,
            case.model_dump(),
        )

        # ---------------------------------------------------------
        # 1. AI AGENT: Generate recovery proposal
        # ---------------------------------------------------------
        proposal = self.agent.decide(case)

        # Record whether the proposal came from Gemini or fallback.
        if self.agent.last_source == "llm":
            self.audit.record(
                "AGENT_LLM_CALL",
                case.payment_id,
                {
                    "provider": "gemini",
                    "model": self.agent.last_model,
                    "status": "success",
                },
            )

        elif self.agent.last_source == "deterministic_fallback":
            self.audit.record(
                "AGENT_LLM_CALL",
                case.payment_id,
                {
                    "provider": "gemini",
                    "model": self.agent.last_model,
                    "status": "fallback",
                    "error": self.agent.last_error,
                },
            )

        # Record the actual proposal made by the agent.
        self.audit.record(
            "AGENT_PROPOSAL",
            case.payment_id,
            {
                "action": proposal.action.value,
                "confidence": proposal.confidence,
                "reason": proposal.reason,
                "agent_source": self.agent.last_source,
                "provider": (
                    "gemini"
                    if self.agent.last_source == "llm"
                    else None
                ),
                "model": self.agent.last_model,
            },
        )

        # ---------------------------------------------------------
        # 2. POLICY ENGINE: Validate / override agent proposal
        # ---------------------------------------------------------
        policy = self.policy.evaluate(case, proposal)

        self.audit.record(
            "POLICY_DECISION",
            case.payment_id,
            policy.model_dump(),
        )

        action = policy.final_action

        # ---------------------------------------------------------
        # 3. TOOL EXECUTION
        # ---------------------------------------------------------
        if action == Action.RETRY:
            tool = self.payment_tools.retry_payment(
                case.payment_id,
                case.amount,
            )

        elif action == Action.SCHEDULE_RETRY:
            delay = proposal.delay_hours or 24

            tool = self.payment_tools.schedule_retry(
                case.payment_id,
                delay,
            )

        elif action == Action.SEND_PAYMENT_LINK:
            tool = self.payment_tools.create_payment_link(
                case.payment_id,
                case.amount,
            )

        elif action == Action.ESCALATE:
            tool = self.ops_tools.escalate_to_human(
                case.payment_id,
                policy.reason,
            )

        else:
            tool = self.ops_tools.stop_recovery(
                case.payment_id,
                policy.reason,
            )

        self.audit.record(
            "TOOL_EXECUTION",
            case.payment_id,
            {
                "action": action.value,
                "success": tool.success,
                "message": tool.message,
                "tool_call_id": tool.tool_call_id,
            },
        )

        # ---------------------------------------------------------
        # 4. OUTCOME HANDLING
        # ---------------------------------------------------------

        # Safely handle tools that may or may not return
        # external Razorpay payment-link fields.
        external_url = getattr(tool, "external_url", None)
        external_id = getattr(tool, "external_id", None)

        external_link = bool(
            tool.success
            and external_url
        )

        # ---------------------------------------------------------
        # 4A. Razorpay Payment Link
        # ---------------------------------------------------------
        if external_link:
            outcome_status = "pending"
            amount_recovered = 0.0

            outcome_message = (
                "Razorpay Payment Link created; "
                "awaiting customer payment webhook."
            )

            self.audit.record(
                "OUTCOME_PENDING",
                case.payment_id,
                {
                    "status": outcome_status,
                    "amount_recovered": amount_recovered,
                    "message": outcome_message,
                    "source": "razorpay_payment_link",
                    "payment_link_id": external_id,
                    "payment_link_url": external_url,
                },
            )

        # ---------------------------------------------------------
        # 4B. Successful internal recovery action
        # ---------------------------------------------------------
        elif action in {
            Action.RETRY,
            Action.SCHEDULE_RETRY,
            Action.SEND_PAYMENT_LINK,
        } and tool.success:

            outcome = self.outcomes.verify(
                payment_id=case.payment_id,
                amount=case.amount,
                action=action.value,
                recovery_probability=case.recovery_probability,
            )

            outcome_status = outcome.status
            amount_recovered = outcome.amount_recovered
            outcome_message = outcome.message

            self.audit.record(
                "OUTCOME_VERIFIED",
                case.payment_id,
                {
                    "status": outcome.status,
                    "amount_recovered": outcome.amount_recovered,
                    "message": outcome.message,
                },
            )

        # ---------------------------------------------------------
        # 4C. Failed / blocked / stopped action
        # ---------------------------------------------------------
        else:
            outcome = self.outcomes.verify(
                payment_id=case.payment_id,
                amount=case.amount,
                action=action.value,
                recovery_probability=0.0,
            )

            outcome_status = outcome.status
            amount_recovered = outcome.amount_recovered
            outcome_message = outcome.message

            self.audit.record(
                "OUTCOME_VERIFIED",
                case.payment_id,
                {
                    "status": outcome.status,
                    "amount_recovered": outcome.amount_recovered,
                    "message": outcome.message,
                },
            )

        # ---------------------------------------------------------
        # 5. FINAL RESULT
        # ---------------------------------------------------------
        return RecoveryResult(
            payment_id=case.payment_id,
            proposed_action=proposal.action,
            final_action=action,
            policy_approved=policy.approved,
            requires_human=policy.requires_human,

            # Revenue recovery succeeded only when the outcome
            # itself is recovered.
            success=outcome_status == "recovered",

            outcome_status=outcome_status,
            amount_recovered=amount_recovered,

            reason=(
                outcome_message
                if outcome_status in {"recovered", "pending"}
                else policy.reason + " " + outcome_message
            ),

            audit_id=self.audit.events[-1]["event_id"],

            external_payment_link_id=external_id,
            external_payment_link_url=external_url,
        )