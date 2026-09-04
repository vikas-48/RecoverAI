from ..agent.recovery_agent import RecoveryAgent
from ..agent.input_validator import validate_untrusted_text
from ..models.recovery_model import RecoveryModel
from ..models.schemas import RecoveryCase
from .data_service import DataService
from .recovery_service import RecoveryService


class RecoveryOrchestrator:
    def __init__(
        self,
        data_service: DataService,
        model: RecoveryModel,
        recovery_service: RecoveryService,
    ):
        self.data = data_service
        self.model = model
        self.recovery_service = recovery_service

    def run(self, payment_id: str):
        context = self.data.get_case(payment_id)

        # Current dataset fields are controlled enums. Keep this boundary in
        # place before future free-text customer/merchant fields reach the LLM.
        for field in ("failure_reason", "payment_method"):
            if not validate_untrusted_text(str(context[field])):
                raise ValueError(f"Suspicious input rejected: {field}")

        probability = self.model.predict_probability(context)
        context["recovery_probability"] = probability

        case = RecoveryCase(**context)
        return self.recovery_service.recover(case)
