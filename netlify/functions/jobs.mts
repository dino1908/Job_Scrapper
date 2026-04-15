import type { Config } from "@netlify/functions";

import { readJobs } from "./lib/store.mjs";

const DEFAULT_LIMIT = 25;
const MAX_LIMIT = 200;

const parseLimit = async (req: Request): Promise<number> => {
  if (req.method === "POST") {
    try {
      const body = (await req.json()) as { limit?: number };
      if (Number.isInteger(body.limit)) {
        return Math.max(1, Math.min(MAX_LIMIT, Number(body.limit)));
      }
    } catch {
      return DEFAULT_LIMIT;
    }
  }

  const url = new URL(req.url);
  const rawLimit = Number.parseInt(url.searchParams.get("limit") ?? "", 10);
  if (Number.isFinite(rawLimit)) {
    return Math.max(1, Math.min(MAX_LIMIT, rawLimit));
  }

  return DEFAULT_LIMIT;
};

export default async (req: Request) => {
  const url = new URL(req.url);
  const taskId = url.searchParams.get("taskId")?.trim();
  if (!taskId) {
    return Response.json({ detail: "taskId is required" }, { status: 400 });
  }

  const limit = await parseLimit(req);
  const jobs = await readJobs(taskId);
  const sortedJobs = [...jobs].sort((left, right) => {
    const leftDate = left.posted_date ? new Date(left.posted_date).getTime() : 0;
    const rightDate = right.posted_date ? new Date(right.posted_date).getTime() : 0;
    return rightDate - leftDate;
  });

  return Response.json({
    total_jobs: Math.min(sortedJobs.length, limit),
    jobs: sortedJobs.slice(0, limit),
  });
};

export const config: Config = {
  path: "/api/jobs",
};
