import json
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from backend.env import CrisisFlowEnv
from backend.models import CrisisFlowAction, ActionType
from backend.inference import choose_next_action as fallback_choose_next_action


# =========================
# LOAD .env AUTOMATICALLY
# =========================
load_dotenv()

# =========================
# REQUIRED ENV VARIABLES
# =========================
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

TASKS = [
    "task_easy_apartment_fire",
    "task_medium_multi_incident_dispatch",
    "task_hard_cascading_gas_leak",
    "task_busy_city_overload",
]

TEMPERATURE = 0.0
MAX_TOKENS = 220
DEBUG = True

VALID_ACTIONS = {
    "inspect_incident",
    "verify_incident",
    "assign_team",
    "escalate_incident",
    "mark_waiting",
    "mark_resolved",
    "noop",
}


# =========================
# OPENAI CLIENT
# =========================
def make_client():
    return OpenAI(
        base_url=API_BASE_URL,
        api_key=HF_TOKEN,
    )


# =========================
# HELPERS
# =========================
def strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_json_block(text: str) -> str:
    text = strip_code_fences(text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def action_needs_incident(action_type: str) -> bool:
    return action_type in {
        "inspect_incident",
        "verify_incident",
        "assign_team",
        "escalate_incident",
        "mark_waiting",
        "mark_resolved",
    }


def is_valid_llm_action(action: CrisisFlowAction) -> bool:
    action_type = getattr(action.action_type, "value", action.action_type)

    if action_type not in VALID_ACTIONS:
        return False

    if action_needs_incident(action_type) and not action.incident_id:
        return False

    if action_type == "assign_team" and not action.team_id:
        return False

    if action_type == "escalate_incident" and not action.escalation_type:
        return False

    return True


def all_active_incidents_waiting(observation: Dict[str, Any]) -> bool:
    active_incidents = observation.get("active_incidents", [])
    if not active_incidents:
        return False
    return all(incident.get("status") == "waiting" for incident in active_incidents)


# =========================
# PROMPT
# =========================
def build_prompt(observation: Dict[str, Any]) -> List[Dict[str, str]]:
    system_prompt = """
You are an emergency dispatch decision agent for CrisisFlow.

Choose exactly ONE next action.
Reply with ONLY valid JSON.

Allowed action_type values:
- inspect_incident
- verify_incident
- assign_team
- escalate_incident
- mark_waiting
- mark_resolved
- noop

JSON schema:
{
  "action_type": "inspect_incident|verify_incident|assign_team|escalate_incident|mark_waiting|mark_resolved|noop",
  "incident_id": "INC123" or null,
  "team_id": "TEAM_ID" or null,
  "priority_rank": null,
  "escalation_type": "required_escalation" or null
}

Rules:
- Prefer higher severity first: critical > high > medium > low.
- Inspect before verify.
- Verify before assign/resolve.
- Assign only suitable available teams.
- Do not assign the same required team type twice to one incident.
- If no required team is available, use mark_waiting.
- Escalate only when required.
- Resolve only after all needed teams are assigned and required escalation is done.
- If no meaningful move exists, respond with noop.
""".strip()

    compact_observation = {
        "task_id": observation.get("task_id"),
        "task_title": observation.get("task_title"),
        "goal": observation.get("goal"),
        "step_count": observation.get("step_count"),
        "max_steps": observation.get("max_steps"),
        "active_incidents": observation.get("active_incidents", []),
        "teams": observation.get("teams", []),
        "recent_action_log": observation.get("action_log", [])[-6:],
        "score_so_far": observation.get("score_so_far"),
        "completed": observation.get("completed"),
    }

    user_prompt = (
        "Choose the single best next action for this observation.\n\n"
        + json.dumps(compact_observation, indent=2)
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


# =========================
# LLM ACTION PARSING
# =========================
def parse_action(raw_text: str) -> Dict[str, Any]:
    json_text = extract_json_block(raw_text)
    data = json.loads(json_text)

    action_type = data.get("action_type")
    if action_type not in VALID_ACTIONS:
        raise ValueError(f"Invalid action_type: {action_type}")

    return {
        "action_type": action_type,
        "incident_id": data.get("incident_id"),
        "team_id": data.get("team_id"),
        "priority_rank": data.get("priority_rank"),
        "escalation_type": data.get("escalation_type"),
    }


def to_action_model(action_data: Dict[str, Any]) -> CrisisFlowAction:
    return CrisisFlowAction(
        action_type=ActionType(action_data["action_type"]),
        incident_id=action_data.get("incident_id"),
        team_id=action_data.get("team_id"),
        priority_rank=action_data.get("priority_rank"),
        escalation_type=action_data.get("escalation_type"),
    )


def get_llm_action(client: OpenAI, observation: Dict[str, Any]) -> CrisisFlowAction:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=build_prompt(observation),
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    raw_output = response.choices[0].message.content or ""

    if DEBUG:
        print("\nLLM RAW OUTPUT:\n", raw_output)

    parsed = parse_action(raw_output)
    return to_action_model(parsed)


# =========================
# ACTION SELECTION
# =========================
def get_next_action(client: OpenAI, observation: Dict[str, Any]) -> CrisisFlowAction:
    try:
        action = get_llm_action(client, observation)
        if is_valid_llm_action(action):
            return action
        print("[WARN] Invalid LLM action -> fallback")
    except Exception as exc:
        print(f"[WARN] LLM failed -> fallback: {exc}")

    fallback_action = fallback_choose_next_action(observation)
    if fallback_action is None:
        return CrisisFlowAction(action_type=ActionType.NOOP)
    return fallback_action


# =========================
# TASK RUNNER
# =========================
def run_task(client: OpenAI, task_id: str) -> Dict[str, Any]:
    env = CrisisFlowEnv()
    observation = env.reset(task_id).model_dump()

    print("\n===== START TASK =====")
    print(f"Task: {task_id}")

    step_number = 1

    while True:
        # clean early stop for waiting-only overload cases
        if all_active_incidents_waiting(observation):
            break

        action = get_next_action(client, observation)

        # avoid useless noop loop when nothing meaningful remains
        if getattr(action.action_type, "value", action.action_type) == "noop":
            if all_active_incidents_waiting(observation):
                break

        step_response = env.step(action)
        data = step_response.model_dump()

        print(f"\n--- STEP {step_number} ---")
        print("Action:", action.model_dump())
        print("Reward:", data["reward"])

        observation = data["observation"]
        step_number += 1

        if data["done"]:
            break

    final_state = env.state().model_dump()

    # patch a cleaner final reason for waiting-only situations
    if (
        not final_state["success"]
        and not final_state.get("failure_reason")
        and all_active_incidents_waiting(observation)
    ):
        final_state["failure_reason"] = "All active incidents are waiting for team availability."

    final_score = min(final_state["total_reward"], 1.0)

    print("\n===== FINAL RESULT =====")
    print("Success:", final_state["success"])
    print("Final Score:", final_score)
    if final_state.get("failure_reason"):
        print("Reason:", final_state["failure_reason"])

    return {
        "task_id": task_id,
        "success": final_state["success"],
        "final_score": final_score,
        "failure_reason": final_state.get("failure_reason"),
    }


# =========================
# MAIN
# =========================
def main() -> None:
    client = make_client()

    results = []
    total_score = 0.0

    for task_id in TASKS:
        result = run_task(client, task_id)
        results.append(result)
        total_score += result["final_score"]

    avg_score = total_score / len(TASKS)

    print("\n===== BASELINE SUMMARY =====")
    for result in results:
        print(
            f"{result['task_id']}: success={result['success']} score={result['final_score']}"
        )
    print(f"Average Score: {avg_score:.4f}")


if __name__ == "__main__":
    main()