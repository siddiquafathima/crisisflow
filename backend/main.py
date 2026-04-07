from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.env import CrisisFlowEnv
from backend.models import CrisisFlowAction
from backend.tasks import TASKS
from backend.inference import simulate_task


app = FastAPI(title="CrisisFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = CrisisFlowEnv()


class ResetRequest(BaseModel):
    task_id: str | None = None


class SimulateRequest(BaseModel):
    task_id: str


@app.get("/health")
def health():
    return {"status": "ok", "message": "CrisisFlow API is running"}


@app.get("/tasks")
def get_tasks():
    return {
        "tasks": [
            {
                "task_id": task["task_id"],
                "task_title": task["task_title"],
                "goal": task["goal"],
                "max_steps": task["max_steps"],
            }
            for task in TASKS.values()
        ]
    }


@app.post("/reset")
def reset_environment(request: ResetRequest | None = None):
    try:
        default_task_id = next(iter(TASKS.keys()))

        task_id = default_task_id
        if request and request.task_id and request.task_id in TASKS:
            task_id = request.task_id

        observation = env.reset(task_id)
        return observation.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step")
def step_environment(action: CrisisFlowAction):
    try:
        response = env.step(action)
        return response.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
def get_state():
    try:
        return env.state().model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate")
def simulate_environment(request: SimulateRequest):
    try:
        return simulate_task(request.task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))