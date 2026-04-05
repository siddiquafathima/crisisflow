from copy import deepcopy

from backend.models import (
    CrisisFlowAction,
    CrisisFlowObservation,
    CrisisFlowReward,
    CrisisFlowState,
    StepResponse,
    ActionLogEntry,
    IncidentStatus,
    TeamStatus,
    ActionType,
)
from backend.tasks import TASKS
from backend.rewards import calculate_reward


class CrisisFlowEnv:
    def __init__(self):
        self.state_data = None

    def reset(self, task_id: str) -> CrisisFlowObservation:
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id: {task_id}")

        task = TASKS[task_id]

        self.state_data = CrisisFlowState(
            task_id=task["task_id"],
            task_title=task["task_title"],
            goal=task["goal"],
            step_count=0,
            max_steps=task["max_steps"],
            incidents=deepcopy(task["incidents"]),
            teams=deepcopy(task["teams"]),
            action_log=[],
            total_reward=0.0,
            done=False,
            success=False,
            failure_reason=None,
            metadata={},
        )

        return self._build_observation()

    def state(self) -> CrisisFlowState:
        if self.state_data is None:
            raise ValueError("Environment not initialized. Call reset() first.")
        return self.state_data

    def step(self, action: CrisisFlowAction) -> StepResponse:
        if self.state_data is None:
            raise ValueError("Environment not initialized. Call reset() first.")

        if self.state_data.done:
            reward = CrisisFlowReward(
                value=0.0,
                reason="Episode already completed."
            )
            return StepResponse(
                observation=self._build_observation(),
                reward=reward,
                done=True,
                info={"message": "No further actions allowed."}
            )

        self.state_data.step_count += 1

        incident = self._find_incident(action.incident_id) if action.incident_id else None
        team = self._find_team(action.team_id) if action.team_id else None

        reward = calculate_reward(self.state_data, action)
        self.state_data.total_reward += reward.value

        log_message = self._apply_action(action, incident, team)

        self.state_data.action_log.append(
            ActionLogEntry(
                step_number=self.state_data.step_count,
                action_type=action.action_type,
                incident_id=action.incident_id,
                team_id=action.team_id,
                message=log_message,
            )
        )

        self._update_done_status()

        if self.state_data.step_count >= self.state_data.max_steps and not self.state_data.done:
            self.state_data.done = True
            self.state_data.success = False
            self.state_data.failure_reason = "Maximum steps reached before completing all incidents."

        return StepResponse(
            observation=self._build_observation(),
            reward=reward,
            done=self.state_data.done,
            info={
                "success": self.state_data.success,
                "failure_reason": self.state_data.failure_reason,
                "total_reward": round(min(self.state_data.total_reward, 1.0), 4),
            }
        )

    def _build_observation(self) -> CrisisFlowObservation:
        active_incidents = [
            incident for incident in self.state_data.incidents
            if incident.status != IncidentStatus.RESOLVED
        ]

        return CrisisFlowObservation(
            task_id=self.state_data.task_id,
            task_title=self.state_data.task_title,
            goal=self.state_data.goal,
            step_count=self.state_data.step_count,
            max_steps=self.state_data.max_steps,
            active_incidents=active_incidents,
            teams=self.state_data.teams,
            action_log=self.state_data.action_log,
            score_so_far=round(min(self.state_data.total_reward, 1.0), 4),
            completed=self.state_data.done,
        )

    def _find_incident(self, incident_id: str):
        for incident in self.state_data.incidents:
            if incident.incident_id == incident_id:
                return incident
        return None

    def _find_team(self, team_id: str):
        for team in self.state_data.teams:
            if team.team_id == team_id:
                return team
        return None

    def _apply_action(self, action: CrisisFlowAction, incident, team) -> str:
        if action.action_type == ActionType.NOOP:
            return "No operation performed."

        if action.action_type == ActionType.INSPECT_INCIDENT:
            if incident is None:
                return "Inspection failed: incident not found."
            return f"Inspected {incident.incident_id}."

        if action.action_type == ActionType.VERIFY_INCIDENT:
            if incident is None:
                return "Verification failed: incident not found."

            if incident.verified:
                return f"Incident {incident.incident_id} is already verified."

            incident.verified = True
            incident.status = IncidentStatus.VERIFIED
            return f"Verified {incident.incident_id}."

        if action.action_type == ActionType.PRIORITIZE_INCIDENT:
            if incident is None:
                return "Prioritization failed: incident not found."

            if action.priority_rank is None:
                return "Prioritization failed: missing priority rank."

            incident.priority_rank = action.priority_rank
            return f"Set priority {action.priority_rank} for {incident.incident_id}."

        if action.action_type == ActionType.ASSIGN_TEAM:
            if incident is None:
                return "Team assignment failed: incident not found."

            if team is None:
                return "Team assignment failed: team not found."

            if team.status != TeamStatus.AVAILABLE:
                return f"Team assignment failed: {team.team_id} is not available."

            if team.team_id not in incident.assigned_team_ids:
                incident.assigned_team_ids.append(team.team_id)

            team.status = TeamStatus.BUSY
            team.current_incident_id = incident.incident_id

            if incident.status in [
                IncidentStatus.REPORTED,
                IncidentStatus.VERIFIED,
                IncidentStatus.WAITING,
            ]:
                incident.status = IncidentStatus.DISPATCHED

            return f"Assigned team {team.team_id} to {incident.incident_id}."

        if action.action_type == ActionType.ESCALATE_INCIDENT:
            if incident is None:
                return "Escalation failed: incident not found."

            if not incident.escalation_required:
                return f"Escalation not required for {incident.incident_id}."

            if incident.escalation_done:
                return f"Incident {incident.incident_id} is already escalated."

            incident.escalation_done = True
            incident.status = IncidentStatus.ESCALATED
            return f"Escalated {incident.incident_id}."

        if action.action_type == ActionType.MARK_WAITING:
            if incident is None:
                return "Waiting status update failed: incident not found."

            if incident.status == IncidentStatus.RESOLVED:
                return f"Incident {incident.incident_id} is already resolved."

            incident.status = IncidentStatus.WAITING
            return f"Marked {incident.incident_id} as waiting for available team."

        if action.action_type == ActionType.MARK_RESOLVED:
            if incident is None:
                return "Resolution failed: incident not found."

            if not incident.verified:
                return f"Cannot resolve {incident.incident_id}: incident is not verified."

            required_count = len(incident.required_team_types)
            assigned_count = len(incident.assigned_team_ids)

            if assigned_count < required_count:
                return f"Cannot resolve {incident.incident_id}: not all required teams are assigned."

            if incident.escalation_required and not incident.escalation_done:
                return f"Cannot resolve {incident.incident_id}: required escalation not completed."

            incident.status = IncidentStatus.RESOLVED

            for current_team in self.state_data.teams:
                if current_team.current_incident_id == incident.incident_id:
                    current_team.status = TeamStatus.AVAILABLE
                    current_team.current_incident_id = None

            return f"Resolved {incident.incident_id}."

        return "Action had no effect."

    def _update_done_status(self):
        unresolved = [
            incident for incident in self.state_data.incidents
            if incident.status != IncidentStatus.RESOLVED
        ]

        if not unresolved:
            self.state_data.done = True
            self.state_data.success = True
            self.state_data.failure_reason = None