from backend.env import CrisisFlowEnv
from backend.models import CrisisFlowAction, ActionType


def main():
    env = CrisisFlowEnv()

    observation = env.reset("task_easy_apartment_fire")
    print("\n--- RESET ---")
    print(observation.model_dump())

    actions = [
        CrisisFlowAction(action_type=ActionType.INSPECT_INCIDENT, incident_id="INC001"),
        CrisisFlowAction(action_type=ActionType.VERIFY_INCIDENT, incident_id="INC001"),
        CrisisFlowAction(action_type=ActionType.ASSIGN_TEAM, incident_id="INC001", team_id="FIRE_A"),
        CrisisFlowAction(action_type=ActionType.ASSIGN_TEAM, incident_id="INC001", team_id="AMB_1"),
        CrisisFlowAction(action_type=ActionType.MARK_RESOLVED, incident_id="INC001"),
    ]

    for i, action in enumerate(actions, start=1):
        response = env.step(action)
        print(f"\n--- STEP {i} ---")
        print(response.model_dump())

    print("\n--- FINAL STATE ---")
    print(env.state().model_dump())


if __name__ == "__main__":
    main()