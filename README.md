---
title: CrisisFlow
emoji: 🚨
colorFrom: red
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# 🚨 CrisisFlow: AI Emergency Response Simulation Environment

## 📌 Overview

CrisisFlow is a real-world emergency response simulation environment designed for training and evaluating AI agents.

It simulates how emergency systems handle incidents like:
- Fires
- Traffic accidents
- Gas leaks

using intelligent decision-making and resource allocation.

The environment follows the **OpenEnv standard** and allows agents to interact using:
- `step()`
- `reset()`
- `state()`

---

## 🎯 Motivation

In real-world emergency systems:
- Resources are limited
- Incidents happen simultaneously
- Prioritization is critical

CrisisFlow models this problem to help build **AI agents that can make smart decisions under pressure**.

---

## ⚙️ Environment Design

### 🔹 Observation Space

The agent receives:
- Active incidents (type, severity, affected people)
- Available teams (fire, police, ambulance, hazmat)
- Current state and progress

---

### 🔹 Action Space

The agent can perform:

- `inspect_incident`
- `verify_incident`
- `assign_team`
- `mark_waiting`
- `mark_resolved`
- `escalate_incident`
- `noop`

---

### 🔹 Reward System

- Inspect → `+0.05`
- Verify → `+0.15`
- Correct team assignment → `+0.25`
- Resolve → `+0.4`
- Wrong actions / useless actions → penalty

👉 This ensures learning across the full decision process.

---

## 🧠 Key Features

- Priority-based dispatch (Critical → High → Medium → Low)
- Smart team assignment based on incident type
- Duplicate team prevention
- Waiting logic when no teams available
- Overload scenario handling
- Escalation for complex incidents
- LLM + fallback hybrid decision system

---

## 🧪 Tasks

### 🟢 Easy: Apartment Fire
- Single incident
- Assign fire + ambulance
- Resolve

---

### 🟡 Medium: Multi-Incident Dispatch
- Multiple incidents
- Requires prioritization
- Different team types

---

### 🔴 Hard: Cascading Gas Leak
- Multi-stage incidents
- Hazmat + police + ambulance
- Escalation required

---

### ⚫ Overload Scenario
- All teams busy
- Must correctly mark incidents as **waiting**

---

## 🖥️ Frontend

CrisisFlow includes a modern dashboard UI for:

- Running simulations
- Viewing incidents
- Tracking teams
- Monitoring execution steps
- Visualizing overload situations

---

## 🚀 Setup Instructions

### 1. Clone repository

```bash
git clone <your-repo-link>
cd crisisflow

2. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

3. Install dependencies
pip install -r requirements.txt

▶️ Run Backend
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
Open:
http://127.0.0.1:8000/docs

▶️ Run Frontend
cd frontend
npm install
npm run dev
Open:
http://localhost:3000

▶️ Run Baseline Inference
python inference.py

🤖 Hugging Face Token Note
This project uses HF_TOKEN for model-based inference.
During local testing, Hugging Face credits may be exhausted, which can produce 402 errors. In such cases, the system automatically falls back to rule-based logic.

Required Environment Variables
API_BASE_URL=https://router.huggingface.co/v1
MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
HF_TOKEN=your_token_here

📊 Baseline Results
Easy → ✅ Success
Medium → ✅ Success
Hard → ✅ Success
Overload → ✅ Correct waiting handling
Average Score: 0.8750


🧾 Submission Notes
inference.py follows OpenAI-compatible API
openenv.yaml is correctly configured
Dockerfile is included
Backend uses FastAPI
Frontend is included for visualization
Invalid LLM outputs are handled safely
Infinite loops are prevented
Smart dispatch logic is implemented

👩‍💻 Author
Siddiqua Fathima

---
