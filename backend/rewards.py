from backend.models import CrisisFlowReward, ActionType, TeamStatus


def _get_incident(state, incident_id):
    if not incident_id:
        return None
    for incident in state.incidents:
        if incident.incident_id == incident_id:
            return incident
    return None


def _get_team(state, team_id):
    if not team_id:
        return None
    for team in state.teams:
        if team.team_id == team_id:
            return team
    return None


def _assigned_team_types(incident, state):
    assigned_ids = set(incident.assigned_team_ids)
    assigned_types = set()

    for team in state.teams:
        if team.team_id in assigned_ids:
            assigned_types.add(team.team_type)

    return assigned_types


def _normalize_required_types(values):
    seen = set()
    ordered = []
    for item in values:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _get_dynamic_required_team_types(incident):
    """
    Must match inference.py logic so reward system and decision system agree.
    """
    required = list(incident.required_team_types)
    incident_type = getattr(incident.incident_type, "value", incident.incident_type)
    severity = getattr(incident.severity, "value", incident.severity)
    affected_people = incident.affected_people

    if incident_type == "fire":
        if "fire_unit" not in required:
            required.append("fire_unit")
        if affected_people > 0 and "ambulance" not in required:
            required.append("ambulance")

    elif incident_type == "gas_leak":
        if "hazmat_unit" not in required:
            required.append("hazmat_unit")
        if "police_unit" not in required:
            required.append("police_unit")
        if affected_people > 0 and "ambulance" not in required:
            required.append("ambulance")

    elif incident_type == "traffic_accident":
        if "police_unit" not in required:
            required.append("police_unit")
        if (affected_people > 0 or severity in ["high", "critical"]) and "ambulance" not in required:
            required.append("ambulance")

    elif incident_type == "medical":
        if "ambulance" not in required:
            required.append("ambulance")
        if severity == "critical" and "police_unit" not in required:
            required.append("police_unit")

    return _normalize_required_types(required)


def _missing_required_team_exists(incident, state):
    assigned_types = _assigned_team_types(incident, state)
    required_types = set(_get_dynamic_required_team_types(incident))
    missing_types = required_types - assigned_types
    return len(missing_types) > 0, missing_types


def _required_team_available(state, missing_types):
    for team in state.teams:
        team_type = getattr(team.team_type, "value", team.team_type)
        if team_type in missing_types and team.status == TeamStatus.AVAILABLE:
            return True
    return False


def calculate_reward(state, action):
    incident = _get_incident(state, action.incident_id)
    team = _get_team(state, action.team_id)

    if action.action_type == ActionType.NOOP:
        return CrisisFlowReward(
            value=-0.1,
            reason="No operation performed."
        )

    if action.action_type == ActionType.INSPECT_INCIDENT:
        if incident is None:
            return CrisisFlowReward(
                value=-0.1,
                reason="Inspection failed: incident not found."
            )
        return CrisisFlowReward(
            value=0.05,
            reason="Incident inspected successfully."
        )

    if action.action_type == ActionType.VERIFY_INCIDENT:
        if incident is None:
            return CrisisFlowReward(
                value=-0.1,
                reason="Verification failed: incident not found."
            )
        if incident.verified:
            return CrisisFlowReward(
                value=-0.05,
                reason="Incident already verified."
            )
        return CrisisFlowReward(
            value=0.15,
            reason="Incident verified correctly."
        )

    if action.action_type == ActionType.PRIORITIZE_INCIDENT:
        if incident is None:
            return CrisisFlowReward(
                value=-0.1,
                reason="Prioritization failed: incident not found."
            )
        return CrisisFlowReward(
            value=0.1,
            reason="Incident prioritized."
        )

    if action.action_type == ActionType.ASSIGN_TEAM:
        if incident is None:
            return CrisisFlowReward(
                value=-0.1,
                reason="Team assignment failed: incident not found."
            )

        if team is None:
            return CrisisFlowReward(
                value=-0.1,
                reason="Team assignment failed: team not found."
            )

        if team.status != TeamStatus.AVAILABLE:
            return CrisisFlowReward(
                value=-0.1,
                reason="Selected team is already busy."
            )

        dynamic_required = set(_get_dynamic_required_team_types(incident))
        team_type = getattr(team.team_type, "value", team.team_type)

        if team_type not in dynamic_required:
            return CrisisFlowReward(
                value=-0.25,
                reason="Incorrect team assigned to incident."
            )

        assigned_types = _assigned_team_types(incident, state)
        if team_type in assigned_types:
            return CrisisFlowReward(
                value=-0.1,
                reason="A team of this required type is already assigned."
            )

        return CrisisFlowReward(
            value=0.25,
            reason="Correct team assigned to incident."
        )

    if action.action_type == ActionType.ESCALATE_INCIDENT:
        if incident is None:
            return CrisisFlowReward(
                value=-0.1,
                reason="Escalation failed: incident not found."
            )

        if not incident.escalation_required:
            return CrisisFlowReward(
                value=-0.05,
                reason="Escalation not required for this incident."
            )

        if incident.escalation_done:
            return CrisisFlowReward(
                value=-0.05,
                reason="Incident already escalated."
            )

        return CrisisFlowReward(
            value=0.2,
            reason="Required escalation completed."
        )

    if action.action_type == ActionType.MARK_WAITING:
        if incident is None:
            return CrisisFlowReward(
                value=-0.1,
                reason="Waiting action failed: incident not found."
            )

        if not incident.verified:
            return CrisisFlowReward(
                value=-0.05,
                reason="Incident should be verified before being marked waiting."
            )

        missing_exists, missing_types = _missing_required_team_exists(incident, state)

        if not missing_exists:
            return CrisisFlowReward(
                value=-0.05,
                reason="All required team types are already assigned."
            )

        if _required_team_available(state, missing_types):
            return CrisisFlowReward(
                value=-0.05,
                reason="A required team is still available, so waiting is not needed."
            )

        return CrisisFlowReward(
            value=0.05,
            reason="Incident correctly marked as waiting due to no available required team."
        )

    if action.action_type == ActionType.MARK_RESOLVED:
        if incident is None:
            return CrisisFlowReward(
                value=-0.1,
                reason="Resolution failed: incident not found."
            )

        if not incident.verified:
            return CrisisFlowReward(
                value=-0.3,
                reason="Incident cannot be resolved before verification."
            )

        assigned_types = _assigned_team_types(incident, state)
        required_types = set(_get_dynamic_required_team_types(incident))

        if not required_types.issubset(assigned_types):
            return CrisisFlowReward(
                value=-0.2,
                reason="Not all required teams are assigned before resolution."
            )

        if incident.escalation_required and not incident.escalation_done:
            return CrisisFlowReward(
                value=-0.2,
                reason="Required escalation missing before resolution."
            )

        return CrisisFlowReward(
            value=0.4,
            reason="Incident resolved safely after correct workflow."
        )

    return CrisisFlowReward(
        value=-0.05,
        reason="Unknown or ineffective action."
    )