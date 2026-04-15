import type { Config } from "@netlify/functions";

import { runScrapeTask } from "./lib/scraper.mjs";

interface BackgroundPayload {
  taskId: string;
  roles: string[];
  locations: string[];
  targetJobs: number;
}

export default async (req: Request) => {
  if (req.method !== "POST") {
    return;
  }

  const payload = (await req.json()) as BackgroundPayload;
  await runScrapeTask({
    taskId: payload.taskId,
    roles: Array.isArray(payload.roles) ? payload.roles : [],
    locations: Array.isArray(payload.locations) && payload.locations.length > 0 ? payload.locations : [""],
    targetJobs: payload.targetJobs,
  });
};

export const config: Config = {
  path: "/api/run-scrape-background",
};
