"""
AEGIS Remediation Policy Gate
Enforces strict allowlisting, risk classification, approval gates, and state transitions.
"""

from typing import Optional, Dict, Any
from engine.models.schemas import (
    RemediationActionProposal,
    ActionRiskLevel,
    ActionState
)
from .action_catalog import ALLOWLISTED_ACTIONS

class PolicyGate:
    def validate_proposal(self, action_type: str, target_service: str, parameters: Dict[str, Any]) -> RemediationActionProposal:
        # Check allowlist
        if action_type not in ALLOWLISTED_ACTIONS:
            raise PermissionError(f"Action '{action_type}' is forbidden. Not in allowlisted remediation catalog.")

        catalog_entry = ALLOWLISTED_ACTIONS[action_type]
        risk = catalog_entry["risk_level"]
        requires_approval = catalog_entry["requires_approval"]

        # Prevent arbitrary injection
        for k, v in parameters.items():
            if any(forbidden in str(v).lower() for forbidden in [";", "rm -rf", "drop table", "exec", "curl", "bash"]):
                raise ValueError(f"Dangerous parameter value detected: {k}={v}")

        initial_state = ActionState.PENDING_APPROVAL if requires_approval else ActionState.APPROVED

        proposal = RemediationActionProposal(
            incident_id="pending",
            action_type=action_type,
            target_service=target_service,
            parameters=parameters,
            risk_level=risk,
            requires_approval=requires_approval,
            state=initial_state
        )
        return proposal

    def approve_action(self, proposal: RemediationActionProposal, approver_name: str) -> RemediationActionProposal:
        if proposal.state not in (ActionState.PROPOSED, ActionState.PENDING_APPROVAL):
            raise ValueError(f"Cannot approve action in state {proposal.state}")

        proposal.state = ActionState.APPROVED
        proposal.approved_by = approver_name
        import time
        proposal.approved_at = time.time()
        return proposal

    def reject_action(self, proposal: RemediationActionProposal, reason: str) -> RemediationActionProposal:
        proposal.state = ActionState.REJECTED
        proposal.rejection_reason = reason
        return proposal
