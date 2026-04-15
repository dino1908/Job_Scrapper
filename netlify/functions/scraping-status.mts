import { readTask } from "./lib/store.mjs";

export default async (req: Request) => {
  const url = new URL(req.url);
  const taskId = url.searchParams.get("taskId")?.trim();

  if (!taskId) {
    return Response.json({ detail: "taskId is required" }, { status: 400 });
  }

  const task = await readTask(taskId);
  if (!task) {
    return Response.json({ detail: "Scraping task not found" }, { status: 404 });
  }

  return Response.json(task);
};

export const config = {
  path: "/api/scraping-status",
};
