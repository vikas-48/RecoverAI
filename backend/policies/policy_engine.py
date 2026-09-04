from ..models.schemas import Action, AgentDecision, PolicyDecision, RecoveryCase


class PolicyEngine:
    """
    Deterministic authorization layer.

    The LLM/agent never gets direct authority to execute a money-moving action.
    """

    MAX_AUTO_AMOUNT = 50_000
    MIN_AUTO_PROBABILITY = 0.30
    MAX_RETRY_ATTEMPTS = 3

    def evaluate(
        self,
        case: RecoveryCase,
        proposal: AgentDecision,
    ) -> PolicyDecision:

        # Hard controls are checked before the agent's requested action.
        if case.amount > self.MAX_AUTO_AMOUNT:
            return PolicyDecision(
                approved=False,
                final_action=Action.ESCALATE,
                requires_human=True,
                reason="High-value payment exceeds the automatic-action limit.",
            )

        if case.attempt_number >= self.MAX_RETRY_ATTEMPTS:
            return PolicyDecision(
                approved=False,
                final_action=Action.STOP,
                requires_human=False,
                reason="Stopping rule: maximum recovery attempts reached.",
            )

        if case.recovery_probability < self.MIN_AUTO_PROBABILITY:
            return PolicyDecision(
                approved=False,
                final_action=Action.STOP,
                requires_human=False,
                reason="Recovery probability is below the minimum action threshold.",
            )

        # Never allow blind retries for payment-method failures.
        if case.failure_reason in {"expired_card", "payment_method_invalid"}:
            if proposal.action in {Action.RETRY, Action.SCHEDULE_RETRY}:
                return PolicyDecision(
                    approved=False,
                    final_action=Action.SEND_PAYMENT_LINK,
                    requires_human=False,
                    reason="Policy blocked retry for an invalid/expired payment method.",
                )

        allowed = {
            Action.RETRY,
            Action.SCHEDULE_RETRY,
            Action.SEND_PAYMENT_LINK,
            Action.ESCALATE,
            Action.STOP,
        }

        if proposal.action not in allowed:
            return PolicyDecision(
                approved=False,
                final_action=Action.ESCALATE,
                requires_human=True,
                reason="Unknown action proposed by agent.",
            )

        if proposal.action == Action.ESCALATE:
            return PolicyDecision(
                approved=False,
                final_action=Action.ESCALATE,
                requires_human=True,
                reason="Agent requested human review.",
            )

        return PolicyDecision(
            approved=True,
            final_action=proposal.action,
            requires_human=False,
            reason="Action satisfies automated recovery policies.",
        )
