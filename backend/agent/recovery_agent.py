import os

from .prompts import SYSTEM_PROMPT
from ..models.schemas import Action, AgentDecision, RecoveryCase


class RecoveryAgent:
    """
    Recovery reasoning layer.

    If OPENAI_API_KEY is configured and USE_LLM=true, the agent uses the
    OpenAI Responses API with strict structured output. Otherwise it uses
    the deterministic fallback, which keeps local development reproducible.

    The agent only proposes an action. PolicyEngine remains authoritative.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

        # LLM provenance / observability
        self.last_source = "unknown"
        self.last_model = None
        self.last_error = None

        if self.llm_client is None and os.getenv("USE_LLM", "false").lower() == "true":
            try:
                from .gemini_client import GeminiRecoveryClient

                self.llm_client = GeminiRecoveryClient()
                self.last_model = self.llm_client.model

                print("====================================")
                print("GEMINI LLM INITIALIZED")
                print(f"MODEL = {self.last_model}")
                print("====================================")

            except Exception as exc:
                self.last_error = str(exc)

                print("GEMINI LLM INITIALIZATION FAILED")
                print(f"ERROR TYPE = {type(exc).__name__}")
                print(f"ERROR = {exc}")

                self.llm_client = None

    def decide(self, case):
        self.last_error = None

        print("\n========== RECOVERY AGENT ==========")
        print(f"USE_LLM = {os.getenv('USE_LLM')}")
        print(
            f"LLM CLIENT = "
            f"{type(self.llm_client).__name__ if self.llm_client else 'NONE'}"
        )

        if self.llm_client is not None:
            try:
                self.last_source = "llm"
                self.last_model = getattr(self.llm_client, "model", None)

                print("SOURCE = LLM")

                decision = self._llm_decide(case)
                decision = self._validate_decision(decision)

                print("LLM DECISION:")
                print(f"  action     = {decision.action}")
                print(f"  confidence = {decision.confidence}")
                print(f"  reason     = {decision.reason}")
                print("LLM VALIDATION = PASSED")
                print("====================================\n")

                return decision

            except Exception as exc:
                self.last_source = "deterministic_fallback"
                self.last_error = str(exc)

                print("LLM CALL FAILED!")
                print(f"ERROR = {type(exc).__name__}: {exc}")
                print("SOURCE = DETERMINISTIC FALLBACK")

                decision = self._deterministic_proposal(case)

                print("FALLBACK DECISION:")
                print(f"  action     = {decision.action}")
                print(f"  confidence = {decision.confidence}")
                print("====================================\n")

                return decision

        self.last_source = "deterministic_fallback"
        self.last_model = None

        print("SOURCE = DETERMINISTIC FALLBACK")

        decision = self._deterministic_proposal(case)

        print("FALLBACK DECISION:")
        print(f"  action     = {decision.action}")
        print(f"  confidence = {decision.confidence}")
        print("====================================\n")

        return decision

    def _llm_decide(self, case: RecoveryCase) -> AgentDecision:
        result = self.llm_client.generate_structured(
            system=SYSTEM_PROMPT,
            input=case.model_dump(),
            schema=AgentDecision,
        )
        return AgentDecision.model_validate(result)

    @staticmethod
    def _validate_decision(decision: AgentDecision) -> AgentDecision:
        if decision.confidence < 0 or decision.confidence > 1:
            raise ValueError("Invalid confidence")

        if decision.action == Action.SCHEDULE_RETRY:
            if decision.delay_hours is None:
                decision.delay_hours = 24
            if decision.delay_hours < 1 or decision.delay_hours > 168:
                raise ValueError("Invalid retry delay")

        return decision

    @staticmethod
    def _deterministic_proposal(case: RecoveryCase) -> AgentDecision:
        p = case.recovery_probability

        if case.attempt_number >= 3:
            return AgentDecision(
                action=Action.STOP,
                reason="Recovery attempt budget has been exhausted.",
                confidence=0.99,
            )

        if case.failure_reason in {"expired_card", "payment_method_invalid"}:
            if p >= 0.45:
                return AgentDecision(
                    action=Action.SEND_PAYMENT_LINK,
                    reason="The payment method appears invalid or expired; updating the payment method is more appropriate than blindly retrying.",
                    confidence=min(0.95, p + 0.10),
                )
            return AgentDecision(
                action=Action.STOP,
                reason="Low recovery probability for a payment-method failure.",
                confidence=0.90,
            )

        if case.failure_reason in {"network_error", "insufficient_funds"}:
            if p >= 0.70:
                return AgentDecision(
                    action=Action.SCHEDULE_RETRY,
                    delay_hours=24,
                    reason="Temporary failure pattern combined with strong historical recovery signals.",
                    confidence=min(0.95, p + 0.08),
                )
            if p >= 0.50:
                return AgentDecision(
                    action=Action.RETRY,
                    reason="Moderate recovery probability supports a limited retry.",
                    confidence=min(0.90, p + 0.05),
                )
            return AgentDecision(
                action=Action.SEND_PAYMENT_LINK,
                reason="Recovery probability is not strong enough for an automatic retry.",
                confidence=0.75,
            )

        if p >= 0.70:
            return AgentDecision(
                action=Action.RETRY,
                reason="High recovery probability supports a limited retry.",
                confidence=min(0.95, p + 0.05),
            )
        if p >= 0.50:
            return AgentDecision(
                action=Action.SEND_PAYMENT_LINK,
                reason="Moderate recovery probability; request a fresh payment attempt.",
                confidence=min(0.90, p + 0.05),
            )

        return AgentDecision(
            action=Action.ESCALATE,
            reason="Uncertain recovery outcome requires human review.",
            confidence=0.80,
        )
