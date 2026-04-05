from backend.models import (
    Incident,
    Team,
    IncidentType,
    SeverityLevel,
    TeamType,
    TeamStatus,
)


TASKS = {
    "task_easy_apartment_fire": {
        "task_id": "task_easy_apartment_fire",
        "task_title": "Apartment Fire Response",
        "goal": "Safely handle the apartment fire by verifying it, assigning the correct teams, and resolving it in the proper order.",
        "max_steps": 8,
        "incidents": [
            Incident(
                incident_id="INC001",
                title="Apartment Fire",
                incident_type=IncidentType.FIRE,
                zone="Zone B",
                severity=SeverityLevel.HIGH,
                affected_people=3,
                required_team_types=[TeamType.FIRE_UNIT, TeamType.AMBULANCE],
                escalation_required=False,
                notes="Residential kitchen fire reported on the second floor."
            )
        ],
        "teams": [
            Team(team_id="FIRE_A", team_type=TeamType.FIRE_UNIT, status=TeamStatus.AVAILABLE),
            Team(team_id="AMB_1", team_type=TeamType.AMBULANCE, status=TeamStatus.AVAILABLE),
            Team(team_id="POL_1", team_type=TeamType.POLICE_UNIT, status=TeamStatus.AVAILABLE),
            Team(team_id="HAZ_1", team_type=TeamType.HAZMAT_UNIT, status=TeamStatus.AVAILABLE),
        ],
    },

    "task_medium_multi_incident_dispatch": {
        "task_id": "task_medium_multi_incident_dispatch",
        "task_title": "Multi-Incident City Dispatch",
        "goal": "Prioritize multiple incidents correctly and assign limited resources to the right emergencies.",
        "max_steps": 14,
        "incidents": [
            Incident(
                incident_id="INC101",
                title="Traffic Accident at Junction",
                incident_type=IncidentType.TRAFFIC_ACCIDENT,
                zone="Zone A",
                severity=SeverityLevel.MEDIUM,
                affected_people=2,
                required_team_types=[TeamType.POLICE_UNIT, TeamType.AMBULANCE],
                escalation_required=False,
                notes="Two vehicles collided at a busy signal junction."
            ),
            Incident(
                incident_id="INC102",
                title="Medical Collapse in Public Park",
                incident_type=IncidentType.MEDICAL,
                zone="Zone C",
                severity=SeverityLevel.HIGH,
                affected_people=1,
                required_team_types=[TeamType.AMBULANCE],
                escalation_required=False,
                notes="Adult male reported unconscious near park entrance."
            ),
            Incident(
                incident_id="INC103",
                title="Minor Shop Fire",
                incident_type=IncidentType.FIRE,
                zone="Zone B",
                severity=SeverityLevel.MEDIUM,
                affected_people=0,
                required_team_types=[TeamType.FIRE_UNIT, TeamType.AMBULANCE],
                escalation_required=False,
                notes="Small electrical fire reported in a retail shop."
            ),
        ],
        "teams": [
            Team(team_id="FIRE_B", team_type=TeamType.FIRE_UNIT, status=TeamStatus.AVAILABLE),
            Team(team_id="AMB_2", team_type=TeamType.AMBULANCE, status=TeamStatus.AVAILABLE),
            Team(team_id="POL_2", team_type=TeamType.POLICE_UNIT, status=TeamStatus.AVAILABLE),
            Team(team_id="AMB_2B", team_type=TeamType.AMBULANCE, status=TeamStatus.AVAILABLE),
            Team(team_id="POL_2B", team_type=TeamType.POLICE_UNIT, status=TeamStatus.AVAILABLE),
        ],
    },

    "task_hard_cascading_gas_leak": {
        "task_id": "task_hard_cascading_gas_leak",
        "task_title": "Cascading Gas Leak Emergency",
        "goal": "Contain the gas leak, coordinate perimeter control, support nearby casualties, and prevent escalation into a larger disaster.",
        "max_steps": 18,
        "incidents": [
            Incident(
                incident_id="INC201",
                title="Gas Leak Near Market Street",
                incident_type=IncidentType.GAS_LEAK,
                zone="Zone A",
                severity=SeverityLevel.HIGH,
                affected_people=5,
                required_team_types=[TeamType.HAZMAT_UNIT, TeamType.POLICE_UNIT],
                escalation_required=True,
                notes="Possible underground pipeline leak with strong odor spreading."
            ),
            Incident(
                incident_id="INC202",
                title="Traffic Accident Near Leak Area",
                incident_type=IncidentType.TRAFFIC_ACCIDENT,
                zone="Zone A",
                severity=SeverityLevel.MEDIUM,
                affected_people=2,
                required_team_types=[TeamType.AMBULANCE, TeamType.POLICE_UNIT],
                escalation_required=False,
                notes="Minor collision reported close to the leak zone."
            ),
            Incident(
                incident_id="INC203",
                title="Rising Fire Risk",
                incident_type=IncidentType.FIRE,
                zone="Zone A",
                severity=SeverityLevel.CRITICAL,
                affected_people=0,
                required_team_types=[TeamType.FIRE_UNIT, TeamType.AMBULANCE],
                escalation_required=False,
                notes="High ignition risk due to gas concentration and nearby electrical sparks."
            ),
        ],
        "teams": [
            Team(team_id="HAZ_2", team_type=TeamType.HAZMAT_UNIT, status=TeamStatus.AVAILABLE),
            Team(team_id="AMB_3", team_type=TeamType.AMBULANCE, status=TeamStatus.AVAILABLE),
            Team(team_id="POL_3", team_type=TeamType.POLICE_UNIT, status=TeamStatus.AVAILABLE),
            Team(team_id="FIRE_C", team_type=TeamType.FIRE_UNIT, status=TeamStatus.AVAILABLE),
            Team(team_id="AMB_3B", team_type=TeamType.AMBULANCE, status=TeamStatus.AVAILABLE),
            Team(team_id="POL_3B", team_type=TeamType.POLICE_UNIT, status=TeamStatus.AVAILABLE),
            Team(team_id="FIRE_CB", team_type=TeamType.FIRE_UNIT, status=TeamStatus.AVAILABLE),
        ],
    },

    "task_busy_city_overload": {
        "task_id": "task_busy_city_overload",
        "task_title": "City Overload - No Team Available",
        "goal": "Demonstrate waiting-state behavior when all required teams are already occupied and a new critical incident appears.",
        "max_steps": 8,
        "incidents": [
            Incident(
                incident_id="INC301",
                title="High-Rise Fire Alert",
                incident_type=IncidentType.FIRE,
                zone="Zone D",
                severity=SeverityLevel.CRITICAL,
                affected_people=8,
                required_team_types=[TeamType.FIRE_UNIT, TeamType.AMBULANCE],
                escalation_required=False,
                notes="Residents trapped in a high-rise building; all local response units are currently busy."
            ),
            Incident(
                incident_id="INC302",
                title="Roadside Trauma Case",
                incident_type=IncidentType.MEDICAL,
                zone="Zone E",
                severity=SeverityLevel.HIGH,
                affected_people=1,
                required_team_types=[TeamType.AMBULANCE],
                escalation_required=False,
                notes="Medical emergency reported while ambulance capacity is exhausted."
            ),
        ],
        "teams": [
            Team(
                team_id="FIRE_D",
                team_type=TeamType.FIRE_UNIT,
                status=TeamStatus.BUSY,
                current_incident_id="PRE_BUSY_1",
            ),
            Team(
                team_id="AMB_4",
                team_type=TeamType.AMBULANCE,
                status=TeamStatus.BUSY,
                current_incident_id="PRE_BUSY_2",
            ),
            Team(
                team_id="POL_4",
                team_type=TeamType.POLICE_UNIT,
                status=TeamStatus.BUSY,
                current_incident_id="PRE_BUSY_3",
            ),
            Team(
                team_id="HAZ_4",
                team_type=TeamType.HAZMAT_UNIT,
                status=TeamStatus.AVAILABLE,
            ),
        ],
    },
}