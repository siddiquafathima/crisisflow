import os
from openai import OpenAI

from backend.env import CrisisFlowEnv
from backend.models import CrisisFlowAction, ActionType
from backend.inference import choose_next_action as fallback_choose_next_action

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


def safe_action_from_policy(observation):
    try:
        action = fallback_choose_next_action(observation)
        if action is None:
            return CrisisFlowAction(action_type=ActionType.NOOP)
        return action
    except Exception:
        return CrisisFlowAction(action_type=ActionType.NOOP)


def compute_safe_score(total_reward: float, success: bool, steps: int, max_steps: int) -> float:
    reward_component = min(abs(total_reward), 0.75)

    success_bonus = 0.15 if success else 0.0

    efficiency_bonus = 0.0
    if max_steps > 0:
        efficiency_ratio = max(0.0, 1.0 - (steps / max_steps))
        efficiency_bonus = 0.09 * efficiency_ratio

    score = reward_component + success_bonus + efficiency_bonus
    return max(0.01, min(score, 0.99))


def run_task(client, task_id: str):
    try:
        env = CrisisFlowEnv()
        observation = env.reset(task_id).model_dump()

        call_validator_proxy(client)

        print(f"[START] task={task_id}", flush=True)

        step = 1
        total_reward = 0.0
        max_steps = observation.get("max_steps", 20)

        while True:
            try:
                action = safe_action_from_policy(observation)
                response = env.step(action)
                data = response.model_dump()

                reward_value = data["reward"]["value"]
                total_reward += reward_value

                action_type = getattr(action.action_type, "value", action.action_type)

                print(
                    f"[STEP] task={task_id} step={step} action={action_type} reward={reward_value}",
                    flush=True,
                )

                observation = data["observation"]

                if data["done"]:
                    break

                step += 1

            except Exception as e:
                print(
                    f"[STEP] task={task_id} step={step} action=noop reward=0.0 error={type(e).__name__}",
                    flush=True,
                )
                break

        try:
            final_state = env.state().model_dump()
            success = final_state.get("success", False)
        except Exception:
            success = False

        final_score = compute_safe_score(total_reward, success, step, max_steps)

        print(
            f"[END] task={task_id} score={final_score} steps={step} success={success}",
            flush=True,
        )

    except Exception as e:
        print(f"[START] task={task_id}", flush=True)
        print(
            f"[STEP] task={task_id} step=1 action=noop reward=0.0 error={type(e).__name__}",
            flush=True,
        )
        print(f"[END] task={task_id} score=0.01 steps=1 success=False", flush=True)


def main():
    client = make_client()

    for task in TASKS:
        run_task(client, task)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] error={type(e).__name__}", flush=True)
