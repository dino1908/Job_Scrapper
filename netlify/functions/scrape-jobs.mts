import { randomUUID } from "node:crypto";

import type { Config } from "@netlify/functions";

import type { ScrapeRequestBody, TaskRecord } from "./lib/contracts.mjs";
import { parseCsvList } from "./lib/parsing.mjs";
import { writeJobs, writeTask } from "./lib/store.mjs";

const MAX_TARGET_JOBS = 200;

export default async (req: Request) => {
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ detail: "Method not allowed" }), {
      status: 405,
      headers: { "content-type": "application/json" },
    });
  }

  let payload: ScrapeRequestBody;
  try {
    payload = (await req.json()) as ScrapeRequestBody;
  } catch {
    return Response.json({ detail: "Invalid JSON payload" }, { status: 400 });
  }

  const parsedRoles = parseCsvList(payload.role_titles);
  const parsedLocations = parseCsvList(payload.locations);
  const targetJobs = Number.isInteger(payload.target_jobs) ? Number(payload.target_jobs) : 25;

  if (parsedRoles.length === 0) {
    return Response.json(
      { detail: "At least one role title is required (comma-separated supported)" },
      { status: 400 },
    );
  }

  if (targetJobs < 1 || targetJobs > MAX_TARGET_JOBS) {
    return Response.json({ detail: "target_jobs must be between 1 and 200" }, { status: 400 });
  }

  const taskId = randomUUID();
  const task: TaskRecord = {
    task_id: taskId,
    status: "pending",
    progress: 0,
    total_jobs_scraped: 0,
    sources_completed: [],
    error_message: null,
    started_at: null,
    completed_at: null,
    parsed_roles: parsedRoles,
    parsed_locations: parsedLocations.length > 0 ? parsedLocations : [""],
    target_jobs: targetJobs,
  };

  await writeTask(task);
  await writeJobs(taskId, []);

  const backgroundUrl = new URL("/api/run-scrape-background", req.url);
  const launchResponse = await fetch(backgroundUrl, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({
      taskId,
      roles: task.parsed_roles,
      locations: task.parsed_locations,
      targetJobs: task.target_jobs,
    }),
  });

  if (!launchResponse.ok && launchResponse.status !== 202) {
    return Response.json(
      { detail: "Unable to start background scraping task" },
      { status: 502 },
    );
  }

  return Response.json({
    task_id: taskId,
    status: "pending",
    message: "Scraping task started successfully",
    parsed_roles: task.parsed_roles,
    parsed_locations: task.parsed_locations,
    target_jobs: task.target_jobs,
  });
};

export const config: Config = {
  path: "/api/scrape-jobs",
};
