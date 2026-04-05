from backend.models import CrisisFlowState, SeverityLevel, TeamType


def grade_task(state: CrisisFlowState) -> float:
    if not state.incidents:
        return 0.0

    total_score = 0.0
    per_incident_weight = 1.0 / len(state.incidents)

    for incident in state.incidents:
        incident_score = 0.0

        if incident.verified:
            incident_score += 0.2

        if incident.priority_rank is not None:
            if incident.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL] and incident.priority_rank == 1:
                incident_score += 0.2
            elif incident.severity == SeverityLevel.MEDIUM and incident.priority_rank in [2, 3]:
                incident_score += 0.15
            else:
                incident_score += 0.05

        required_types = set(incident.required_team_types)
        assigned_team_types = set()

        for team in state.teams:
            if team.team_id in incident.assigned_team_ids:
                assigned_team_types.add(team.team_type)

        if required_types:
            coverage_ratio = len(required_types.intersection(assigned_team_types)) / len(required_types)
            incident_score += 0.3 * coverage_ratio

        if incident.escalation_required:
            if incident.escalation_done:
                incident_score += 0.15

        if incident.status.value == "resolved":
            safe_to_resolve = incident.verified and len(incident.assigned_team_ids) >= len(incident.required_team_types)
            if incident.escalation_required:
                safe_to_resolve = safe_to_resolve and incident.escalation_done

            if safe_to_resolve:
                incident_score += 0.15

        if state.step_count <= state.max_steps:
            incident_score += 0.05

        total_score += min(incident_score, 1.0) * per_incident_weight

    return round(min(total_score, 1.0), 4)