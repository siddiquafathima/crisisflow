from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# -----------------------------
# ENUMS
# -----------------------------

class IncidentType(str, Enum):
    FIRE = "fire"
    MEDICAL = "medical"
    TRAFFIC_ACCIDENT = "traffic_accident"
    GAS_LEAK = "gas_leak"


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    REPORTED = "reported"
    VERIFIED = "verified"
    DISPATCHED = "dispatched"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    WAITING = "waiting"


class TeamType(str, Enum):
    FIRE_UNIT = "fire_unit"
    AMBULANCE = "ambulance"
    POLICE_UNIT = "police_unit"
    HAZMAT_UNIT = "hazmat_unit"


class TeamStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"


class ActionType(str, Enum):
    INSPECT_INCIDENT = "inspect_incident"
    VERIFY_INCIDENT = "verify_incident"
    PRIORITIZE_INCIDENT = "prioritize_incident"
    ASSIGN_TEAM = "assign_team"
    ESCALATE_INCIDENT = "escalate_incident"
    MARK_RESOLVED = "mark_resolved"
    NOOP = "noop"
    MARK_WAITING = "mark_waiting"


# -----------------------------
# CORE MODELS
# -----------------------------

class Incident(BaseModel):
    incident_id: str
    title: str
    incident_type: IncidentType
    zone: str
    severity: SeverityLevel
    status: IncidentStatus = IncidentStatus.REPORTED
    affected_people: int = 0
    verified: bool = False
    priority_rank: Optional[int] = None
    required_team_types: List[TeamType] = []
    assigned_team_ids: List[str] = []
    escalation_required: bool = False
    escalation_done: bool = False
    notes: Optional[str] = None


class Team(BaseModel):
    team_id: str
    team_type: TeamType
    status: TeamStatus = TeamStatus.AVAILABLE
    current_incident_id: Optional[str] = None


class ActionLogEntry(BaseModel):
    step_number: int
    action_type: ActionType
    incident_id: Optional[str] = None
    team_id: Optional[str] = None
    message: str


# -----------------------------
# OPENENV-STYLE MODELS
# -----------------------------

class CrisisFlowAction(BaseModel):
    action_type: ActionType
    incident_id: Optional[str] = None
    team_id: Optional[str] = None
    priority_rank: Optional[int] = None
    escalation_type: Optional[str] = None


class CrisisFlowReward(BaseModel):
    value: float
    reason: str


class CrisisFlowObservation(BaseModel):
    task_id: str
    task_title: str
    goal: str
    step_count: int
    max_steps: int
    active_incidents: List[Incident]
    teams: List[Team]
    action_log: List[ActionLogEntry]
    score_so_far: float = 0.0
    completed: bool = False


class CrisisFlowState(BaseModel):
    task_id: str
    task_title: str
    goal: str
    step_count: int
    max_steps: int
    incidents: List[Incident]
    teams: List[Team]
    action_log: List[ActionLogEntry]
    total_reward: float = 0.0
    done: bool = False
    success: bool = False
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = {}


class StepResponse(BaseModel):
    observation: CrisisFlowObservation
    reward: CrisisFlowReward
    done: bool
    info: Dict[str, Any] = {}