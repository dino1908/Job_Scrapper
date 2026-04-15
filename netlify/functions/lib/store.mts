import { getStore } from "@netlify/blobs";

import type { JobRecord, TaskRecord } from "./contracts.mjs";

const TASK_STORE_NAME = "job-scrapper-tasks";
const JOB_STORE_NAME = "job-scrapper-jobs";

const getTaskStore = () => getStore(TASK_STORE_NAME, { consistency: "strong" });
const getJobStore = () => getStore(JOB_STORE_NAME, { consistency: "strong" });

const taskKey = (taskId: string) => `${taskId}:status`;
const jobsKey = (taskId: string) => `${taskId}:jobs`;

export const readTask = async (taskId: string): Promise<TaskRecord | null> => {
  const value = await getTaskStore().get(taskKey(taskId), { type: "json" });
  return (value as TaskRecord | null) ?? null;
};

export const writeTask = async (task: TaskRecord): Promise<void> => {
  await getTaskStore().setJSON(taskKey(task.task_id), task);
};

export const readJobs = async (taskId: string): Promise<JobRecord[]> => {
  const value = await getJobStore().get(jobsKey(taskId), { type: "json" });
  return Array.isArray(value) ? (value as JobRecord[]) : [];
};

export const writeJobs = async (taskId: string, jobs: JobRecord[]): Promise<void> => {
  await getJobStore().setJSON(jobsKey(taskId), jobs);
};
