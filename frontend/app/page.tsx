"use client";

import { useState } from "react";
import { motion } from "framer-motion";

type Team = {
  team_id: string;
  team_type: string;
  status: string;
  current_incident_id: string | null;
};

type Incident = {
  incident_id: string;
  title: string;
  incident_type: string;
  zone: string;
  severity: string;
  status: string;
  affected_people: number;
  verified: boolean;
  priority_rank: number | null;
  required_team_types: string[];
  assigned_team_ids: string[];
  escalation_required: boolean;
  escalation_done: boolean;
  notes: string | null;
};

type ActionLog = {
  step_number: number;
  action_type: string;
  incident_id: string | null;
  team_id: string | null;
  message: string;
};

type StepItem = {
  step_number: number;
  action: {
    action_type: string;
    incident_id: string | null;
    team_id: string | null;
    priority_rank: number | null;
    escalation_type: string | null;
  };
  reward: {
    value: number;
    reason: string;
  };
  done: boolean;
  info: {
    success: boolean;
    failure_reason: string | null;
    total_reward: number;
  };
};

type SimulationResponse = {
  task_id: string;
  steps: StepItem[];
  final_state: {
    incidents: Incident[];
    teams: Team[];
    action_log: ActionLog[];
    total_reward: number;
    done: boolean;
    success: boolean;
    failure_reason?: string | null;
  };
  success: boolean;
  final_score: number;
};

function getSeverityCardStyle(severity: string) {
  if (severity === "critical") return "border-red-500/60 bg-red-500/10";
  if (severity === "high") return "border-orange-500/60 bg-orange-500/10";
  if (severity === "medium") return "border-yellow-500/60 bg-yellow-500/10";
  return "border-zinc-700 bg-zinc-800/40";
}

function getSeverityBadgeStyle(severity: string) {
  if (severity === "critical") return "bg-red-500/20 text-red-300 border border-red-500/40";
  if (severity === "high") return "bg-orange-500/20 text-orange-300 border border-orange-500/40";
  if (severity === "medium") return "bg-yellow-500/20 text-yellow-300 border border-yellow-500/40";
  return "bg-zinc-700/30 text-zinc-300 border border-zinc-600";
}

function getStatusStyle(status: string) {
  if (status === "available") return "text-emerald-400";
  if (status === "busy") return "text-orange-400";
  if (status === "resolved") return "text-emerald-400";
  if (status === "verified") return "text-sky-400";
  if (status === "dispatched") return "text-violet-400";
  if (status === "escalated") return "text-red-400";
  if (status === "waiting") return "text-yellow-300";
  if (status === "reported") return "text-zinc-300";
  return "text-zinc-300";
}

function getStatusBadgeStyle(status: string) {
  if (status === "resolved") return "bg-emerald-500/15 text-emerald-300 border border-emerald-500/40";
  if (status === "waiting") return "bg-yellow-500/15 text-yellow-300 border border-yellow-500/40";
  if (status === "verified") return "bg-sky-500/15 text-sky-300 border border-sky-500/40";
  if (status === "dispatched") return "bg-violet-500/15 text-violet-300 border border-violet-500/40";
  if (status === "escalated") return "bg-red-500/15 text-red-300 border border-red-500/40";
  if (status === "busy") return "bg-orange-500/15 text-orange-300 border border-orange-500/40";
  if (status === "available") return "bg-emerald-500/15 text-emerald-300 border border-emerald-500/40";
  return "bg-zinc-700/30 text-zinc-300 border border-zinc-600";
}

export default function Home() {
  const [task, setTask] = useState("task_easy_apartment_fire");
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = async () => {
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/simulate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ task_id: task }),
      });

      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error(error);
    }

    setLoading(false);
  };

  const activeIncidents =
    result?.final_state.incidents.filter(
      (incident) => incident.status !== "resolved"
    ) ?? [];

  const waitingCount =
    result?.final_state.incidents.filter(
      (incident) => incident.status === "waiting"
    ).length ?? 0;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#1e293b_0%,_#09090b_35%,_#000000_100%)] text-white">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-10 text-center"
        >
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1 text-sm text-zinc-300 backdrop-blur">
            <span>🚨</span>
            <span>AI Emergency Response Control Center</span>
          </div>

          <h1 className="text-4xl font-bold tracking-tight md:text-6xl">
            CrisisFlow Dashboard
          </h1>

          <p className="mx-auto mt-4 max-w-2xl text-sm text-zinc-400 md:text-base">
            Simulate priority-based emergency response, assign the correct teams,
            and detect overload situations when incidents must wait for resources.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mx-auto mb-8 flex max-w-4xl flex-col items-center justify-center gap-4 rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl md:flex-row"
        >
          <select
            className="w-full rounded-2xl border border-zinc-700 bg-zinc-950/70 px-4 py-3 text-white outline-none md:w-80"
            value={task}
            onChange={(e) => setTask(e.target.value)}
          >
            <option value="task_easy_apartment_fire">Easy Task</option>
            <option value="task_medium_multi_incident_dispatch">Medium Task</option>
            <option value="task_hard_cascading_gas_leak">Hard Task</option>
            <option value="task_busy_city_overload">Busy Overload Demo</option>
          </select>

          <button
            onClick={runSimulation}
            className="w-full rounded-2xl bg-blue-600 px-6 py-3 font-semibold transition hover:scale-[1.02] hover:bg-blue-500 md:w-auto"
          >
            {loading ? "Running Simulation..." : "Run Simulation"}
          </button>
        </motion.div>

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45 }}
            className="space-y-8"
          >
            {result.final_state.failure_reason && (
              <motion.div
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-3xl border border-yellow-500/30 bg-yellow-500/10 p-5 text-yellow-100 backdrop-blur-xl"
              >
                <p className="text-sm uppercase tracking-wide text-yellow-300">
                  Dispatch Note
                </p>
                <p className="mt-2 text-base font-medium">
                  {result.final_state.failure_reason}
                </p>
              </motion.div>
            )}

            <div className="grid gap-4 md:grid-cols-5">
              <motion.div
                whileHover={{ y: -4 }}
                className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl"
              >
                <p className="mb-2 text-sm text-zinc-400">Simulation Result</p>
                <h2 className="text-2xl font-bold">
                  {result.success ? "✅ Success" : "⚠️ Incomplete"}
                </h2>
                <p className="mt-2 text-zinc-300">
                  Score: {result.final_score}
                </p>
              </motion.div>

              <motion.div
                whileHover={{ y: -4 }}
                className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl"
              >
                <p className="mb-2 text-sm text-zinc-400">Active Incidents</p>
                <h2 className="text-3xl font-bold">{activeIncidents.length}</h2>
                <p className="mt-2 text-zinc-300">Still unresolved</p>
              </motion.div>

              <motion.div
                whileHover={{ y: -4 }}
                className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl"
              >
                <p className="mb-2 text-sm text-zinc-400">Waiting Incidents</p>
                <h2 className="text-3xl font-bold">{waitingCount}</h2>
                <p className="mt-2 text-zinc-300">Blocked by resource limits</p>
              </motion.div>

              <motion.div
                whileHover={{ y: -4 }}
                className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl"
              >
                <p className="mb-2 text-sm text-zinc-400">Response Teams</p>
                <h2 className="text-3xl font-bold">
                  {result.final_state.teams.length}
                </h2>
                <p className="mt-2 text-zinc-300">Tracked units</p>
              </motion.div>

              <motion.div
                whileHover={{ y: -4 }}
                className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl"
              >
                <p className="mb-2 text-sm text-zinc-400">Executed Steps</p>
                <h2 className="text-3xl font-bold">{result.steps.length}</h2>
                <p className="mt-2 text-zinc-300">Dispatch actions</p>
              </motion.div>
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
              <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                <h3 className="mb-5 text-2xl font-semibold">Incidents</h3>

                <div className="space-y-4">
                  {result.final_state.incidents.map((incident, index) => (
                    <motion.div
                      key={incident.incident_id}
                      initial={{ opacity: 0, y: 18 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.08 }}
                      className={`rounded-2xl border p-4 ${getSeverityCardStyle(
                        incident.severity
                      )}`}
                    >
                      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <h4 className="text-lg font-semibold">
                            {incident.title}
                          </h4>
                          <p className="text-sm text-zinc-300">
                            {incident.incident_id}
                          </p>
                        </div>

                        <div className="flex flex-wrap gap-2">
                          <span
                            className={`rounded-full px-3 py-1 text-xs uppercase tracking-wide ${getSeverityBadgeStyle(
                              incident.severity
                            )}`}
                          >
                            {incident.severity}
                          </span>

                          <span
                            className={`rounded-full px-3 py-1 text-xs uppercase tracking-wide ${getStatusBadgeStyle(
                              incident.status
                            )}`}
                          >
                            {incident.status}
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3 text-sm text-zinc-200">
                        <p>Type: {incident.incident_type}</p>
                        <p>Zone: {incident.zone}</p>
                        <p>Affected: {incident.affected_people}</p>
                        <p>Verified: {incident.verified ? "Yes" : "No"}</p>
                      </div>

                      <div className="mt-3 text-sm text-zinc-300">
                        <p>
                          Based Required Teams: {incident.required_team_types.join(", ")}
                        </p>
                        <p>
                          Assigned Teams:{" "}
                          {incident.assigned_team_ids.length > 0
                            ? incident.assigned_team_ids.join(", ")
                            : "None"}
                        </p>
                        <p className="mt-1 text-xs text-zinc-400">
                            Runtime dispatch may add extra teams dynamically based on severity,
                            incident type, and affected people.
                        </p>
                      </div>

                      {incident.notes && (
                        <p className="mt-3 text-sm text-zinc-300">
                          {incident.notes}
                        </p>
                      )}
                    </motion.div>
                  ))}
                </div>
              </section>

              <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                <h3 className="mb-5 text-2xl font-semibold">Teams</h3>

                <div className="space-y-4">
                  {result.final_state.teams.map((team, index) => (
                    <motion.div
                      key={team.team_id}
                      initial={{ opacity: 0, y: 18 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.06 }}
                      className="rounded-2xl border border-zinc-700/70 bg-zinc-900/50 p-4"
                    >
                      <div className="mb-2 flex items-center justify-between">
                        <h4 className="text-lg font-semibold">{team.team_id}</h4>
                        <span
                          className={`rounded-full px-3 py-1 text-xs uppercase tracking-wide ${getStatusBadgeStyle(
                            team.status
                          )}`}
                        >
                          {team.status}
                        </span>
                      </div>

                      <div className="space-y-1 text-sm text-zinc-300">
                        <p>Type: {team.team_type}</p>
                        <p>Current Incident: {team.current_incident_id ?? "None"}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </section>
            </div>

            <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
              <h3 className="mb-5 text-2xl font-semibold">Simulation Steps</h3>

              <div className="max-h-[420px] space-y-3 overflow-y-auto pr-1">
                {result.steps.map((step, index) => (
                  <motion.div
                    key={`${step.step_number}-${index}`}
                    initial={{ opacity: 0, x: -16 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.04 }}
                    className="rounded-2xl border border-zinc-700/70 bg-zinc-900/50 p-4"
                  >
                    <div className="mb-1 flex items-center justify-between">
                      <p className="font-semibold">Step {step.step_number}</p>
                      <span className="text-xs text-zinc-400">
                        {step.action.action_type}
                      </span>
                    </div>

                    <p className="text-sm text-zinc-300">
                      Incident: {step.action.incident_id ?? "N/A"} | Team: {step.action.team_id ?? "N/A"}
                    </p>

                    <p className="mt-2 text-sm text-zinc-200">
                      Reward: {step.reward.value}
                    </p>
                    <p className="text-sm text-zinc-400">{step.reward.reason}</p>
                  </motion.div>
                ))}
              </div>
            </section>
          </motion.div>
        )}
      </div>
    </main>
  );
}