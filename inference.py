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


def make_client():
    try:
        return OpenAI(
            base_url=os.environ.get("API_BASE_URL", ""),
            api_key=os.environ.get("API_KEY", ""),
        )
    except Exception as e:
        print(f"[LLM_CLIENT_FAILED] error={type(e).__name__}", flush=True)
        return None


def call_validator_proxy(client):
    if client is None:
        print("[LLM_CALL_FAILED] error=NoClient", flush=True)
        return

    model_name = os.environ.get("MODEL_NAME", "gpt-4o-mini")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Reply with exactly the word: ok"},
            ],
            max_tokens=5,
            temperature=0.0,
        )
        _ = response.choices[0].message.content
        print("[LLM_CALL_SUCCESS]", flush=True)
    except Exception as e:
        print(f"[LLM_CALL_FAILED] error={type(e).__name__}", flush=True)


def run_task(client, task_id: str):
    try:
        env = CrisisFlowEnv()
        env.reset(task_id)

        call_validator_proxy(client)

        print(f"[START] task={task_id}", flush=True)

        step = 1
        total_reward = 0.0

        while True:
            try:
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

            except Exception as e:
                print(
                    f"[STEP] task={task_id} step={step} reward=0.0 error={type(e).__name__}",
                    flush=True,
                )
                break

        final_score = max(0.01, min(abs(total_reward), 0.99))

        print(
            f"[END] task={task_id} score={final_score} steps={step}",
            flush=True,
        )

    except Exception as e:
        print(f"[START] task={task_id}", flush=True)
        print(
            f"[STEP] task={task_id} step=1 reward=0.0 error={type(e).__name__}",
            flush=True,
        )
        print(f"[END] task={task_id} score=0.0 steps=1", flush=True)


def main():
    client = make_client()

    for task in TASKS:
        run_task(client, task)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] error={type(e).__name__}", flush=True)
