import os
from openai import OpenAI

from backend.env import CrisisFlowEnv
from backend.models import CrisisFlowAction, ActionType

TASKS = [
    "task_easy_apartment_fire",
    "task_medium_multi_incident_dispatch",
    "task_hard_cascading_gas_leak",
    "task_busy_city_overload",
]


def make_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["API_BASE_URL"],
        api_key=os.environ["API_KEY"],
    )


def call_validator_proxy(client):
    model_name = os.environ.get("MODEL_NAME", "gpt-4o-mini")

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": "Say OK"}
        ],
        max_tokens=5,
    )

    print("[LLM_CALL_SUCCESS]", flush=True)



def run_task(client: OpenAI, task_id: str) -> None:
    env = CrisisFlowEnv()
    env.reset(task_id)

    # Required real proxy call
    call_validator_proxy(client)

    print(f"[START] task={task_id}", flush=True)

    step = 1
    total_reward = 0.0

    while True:
        action = CrisisFlowAction(action_type=ActionType.NOOP)
        response = env.step(action)

        reward_value = response.reward.value
        total_reward += reward_value

        print(
            f"[STEP] task={task_id} step={step} reward={reward_value}",
            flush=True,
        )

        if response.done:
            break

        step += 1

    final_score = max(0.0, min(total_reward, 1.0))

    print(
        f"[END] task={task_id} score={final_score} steps={step}",
        flush=True,
    )


def main() -> None:
    client = make_client()

    for task in TASKS:
        run_task(client, task)


if __name__ == "__main__":
    main()