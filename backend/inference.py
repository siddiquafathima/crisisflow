from backend.env import CrisisFlowEnv
from backend.models import CrisisFlowAction, ActionType


SEVERITY_PRIORITY = {
    "critical": 3,
    "high": 2,
    "medium": 1,
    "low": 0,
}


def get_action_name(value):
    return getattr(value, "value", value)


def was_action_done(action_log, incident_id, action_name):
    return any(
        get_action_name(log["action_type"]) == action_name
        and log["incident_id"] == incident_id
        for log in action_log
    )


def sort_incidents_by_priority(incidents):
    return sorted(
        incidents,
        key=lambda incident: SEVERITY_PRIORITY.get(incident["severity"], 0),
        reverse=True,
    )


def assigned_team_types_for_incident(incident, teams):
    assigned_ids = set(incident["assigned_team_ids"])
    assigned_types = set()

    for team in teams:
        if team["team_id"] in assigned_ids:
            assigned_types.add(team["team_type"])

    return assigned_types


def find_available_team(teams, required_team_type):
    for team in teams:
        if team["team_type"] == required_team_type and team["status"] == "available":
            return team
    return None


def normalize_required_types(values):
    seen = set()
    ordered = []
    for item in values:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def get_dynamic_required_team_types(incident):
    required = list(incident["required_team_types"])
    incident_type = incident["incident_type"]
    severity = incident["severity"]
    affected_people = incident["affected_people"]

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

    return normalize_required_types(required)


def incident_has_available_required_team(incident, teams):
    assigned_types = assigned_team_types_for_incident(incident, teams)
    required_team_types = get_dynamic_required_team_types(incident)

    for required_team_type in required_team_types:
        if required_team_type in assigned_types:
            continue
        team = find_available_team(teams, required_team_type)
        if team is not None:
            return True
    return False


def can_progress_incident(incident, teams):
    if not incident["verified"]:
        return True

    if incident_has_available_required_team(incident, teams):
        return True

    dynamic_required = get_dynamic_required_team_types(incident)
    assigned_types = assigned_team_types_for_incident(incident, teams)

    if incident["escalation_required"] and not incident["escalation_done"]:
        if len(assigned_types) >= len(set(dynamic_required)):
            return True

    if len(assigned_types) >= len(set(dynamic_required)):
        return True

    return False


def all_active_incidents_waiting(observation):
    active_incidents = observation["active_incidents"]
    if not active_incidents:
        return False
    return all(incident["status"] == "waiting" for incident in active_incidents)


def choose_incident(observation):
    active_incidents = observation["active_incidents"]
    teams = observation["teams"]

    if not active_incidents:
        return None

    sorted_incidents = sort_incidents_by_priority(active_incidents)

    for incident in sorted_incidents:
        if can_progress_incident(incident, teams):
            return incident

    for incident in sorted_incidents:
        if incident["status"] != "waiting":
            return incident

    return None


def choose_next_action(observation):
    teams = observation["teams"]
    action_log = observation.get("action_log", [])

    if all_active_incidents_waiting(observation):
        return None

    incident = choose_incident(observation)
    if incident is None:
        return None

    incident_id = incident["incident_id"]

    if not was_action_done(action_log, incident_id, "inspect_incident"):
        return CrisisFlowAction(
            action_type=ActionType.INSPECT_INCIDENT,
            incident_id=incident_id
        )

    if not incident["verified"]:
        return CrisisFlowAction(
            action_type=ActionType.VERIFY_INCIDENT,
            incident_id=incident_id
        )

    required_team_types = get_dynamic_required_team_types(incident)
    already_assigned_types = assigned_team_types_for_incident(incident, teams)

    for required_team_type in required_team_types:
        if required_team_type in already_assigned_types:
            continue

        matching_team = find_available_team(teams, required_team_type)
        if matching_team:
            return CrisisFlowAction(
                action_type=ActionType.ASSIGN_TEAM,
                incident_id=incident_id,
                team_id=matching_team["team_id"]
            )
        else:
            if incident["status"] != "waiting":
                return CrisisFlowAction(
                    action_type=ActionType.MARK_WAITING,
                    incident_id=incident_id
                )
            break

    if incident["escalation_required"] and not incident["escalation_done"]:
        if len(already_assigned_types) >= len(set(required_team_types)):
            return CrisisFlowAction(
                action_type=ActionType.ESCALATE_INCIDENT,
                incident_id=incident_id,
                escalation_type="required_escalation"
            )

    if len(already_assigned_types) >= len(set(required_team_types)):
        return CrisisFlowAction(
            action_type=ActionType.MARK_RESOLVED,
            incident_id=incident_id
        )

    sorted_incidents = sort_incidents_by_priority(observation["active_incidents"])

    for other_incident in sorted_incidents:
        if other_incident["incident_id"] == incident_id:
            continue

        other_incident_id = other_incident["incident_id"]

        if not was_action_done(action_log, other_incident_id, "inspect_incident"):
            return CrisisFlowAction(
                action_type=ActionType.INSPECT_INCIDENT,
                incident_id=other_incident_id
            )

        if not other_incident["verified"]:
            return CrisisFlowAction(
                action_type=ActionType.VERIFY_INCIDENT,
                incident_id=other_incident_id
            )

        other_required_types = get_dynamic_required_team_types(other_incident)
        other_assigned_types = assigned_team_types_for_incident(other_incident, teams)

        moved = False
        for required_team_type in other_required_types:
            if required_team_type in other_assigned_types:
                continue

            matching_team = find_available_team(teams, required_team_type)
            if matching_team:
                return CrisisFlowAction(
                    action_type=ActionType.ASSIGN_TEAM,
                    incident_id=other_incident_id,
                    team_id=matching_team["team_id"]
                )
            else:
                if other_incident["status"] != "waiting":
                    return CrisisFlowAction(
                        action_type=ActionType.MARK_WAITING,
                        incident_id=other_incident_id
                    )
                moved = True
                break

        if moved:
            continue

        if other_incident["escalation_required"] and not other_incident["escalation_done"]:
            if len(other_assigned_types) >= len(set(other_required_types)):
                return CrisisFlowAction(
                    action_type=ActionType.ESCALATE_INCIDENT,
                    incident_id=other_incident_id,
                    escalation_type="required_escalation"
                )

        if len(other_assigned_types) >= len(set(other_required_types)):
            return CrisisFlowAction(
                action_type=ActionType.MARK_RESOLVED,
                incident_id=other_incident_id
            )

    return None


def simulate_task(task_id: str):
    env = CrisisFlowEnv()
    observation = env.reset(task_id).model_dump()

    step_results = []

    while True:
        action = choose_next_action(observation)
        if action is None:
            break

        response = env.step(action)
        data = response.model_dump()

        step_results.append(
            {
                "step_number": len(step_results) + 1,
                "action": action.model_dump(),
                "reward": data["reward"],
                "done": data["done"],
                "info": data["info"],
            }
        )

        observation = data["observation"]

        if data["done"]:
            break

    final_state = env.state().model_dump()

    if (
        not final_state["success"]
        and final_state["failure_reason"] is None
        and len(final_state["incidents"]) > 0
    ):
        unresolved = [i for i in final_state["incidents"] if i["status"] != "resolved"]
        if unresolved and all(i["status"] == "waiting" for i in unresolved):
            final_state["failure_reason"] = "All active incidents are waiting for team availability."

    return {
        "task_id": task_id,
        "steps": step_results,
        "final_state": final_state,
        "success": final_state["success"],
        "final_score": min(final_state["total_reward"], 1.0),
    }


def run_task(task_id):
    result = simulate_task(task_id)

    print("\n===== START TASK =====")
    print(f"Task: {task_id}")

    for step in result["steps"]:
        print(f"\n--- STEP {step['step_number']} ---")
        print("Action:", step["action"])
        print("Reward:", step["reward"])

    print("\n===== FINAL RESULT =====")
    print("Success:", result["success"])
    print("Final Score:", result["final_score"])
    if result["final_state"].get("failure_reason"):
        print("Reason:", result["final_state"]["failure_reason"])


if __name__ == "__main__":
    run_task("task_easy_apartment_fire")
    run_task("task_medium_multi_incident_dispatch")
    run_task("task_hard_cascading_gas_leak")
    run_task("task_busy_city_overload")