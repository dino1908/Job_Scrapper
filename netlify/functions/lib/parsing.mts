import type { JobRecord } from "./contracts.mjs";

export const parseCsvList = (value: string | undefined): string[] => {
  if (!value) {
    return [];
  }

  const parsed: string[] = [];
  const seen = new Set<string>();

  for (const part of value.split(",")) {
    const cleaned = part.trim();
    const normalized = cleaned.toLowerCase();
    if (!cleaned || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    parsed.push(cleaned);
  }

  return parsed;
};

export const normalize = (value: string | null | undefined): string =>
  (value ?? "").toLowerCase().trim().replace(/\s+/g, " ");

export const tokenize = (value: string): string[] =>
  normalize(value)
    .split(/[\s,/\\\-()|]+/)
    .filter(Boolean);

export const roleVariants = (role: string): string[] => {
  const roleNorm = normalize(role);
  const variants = new Set<string>([roleNorm]);

  if (roleNorm === "pm") {
    variants.add("product manager");
    variants.add("product management");
    variants.add("program manager");
    variants.add("project manager");
  }

  if (roleNorm.includes("product manager") || roleNorm.includes("product management")) {
    variants.add("product manager");
    variants.add("product management");
    variants.add("pm");
  }

  if (roleNorm.includes("program manager")) {
    variants.add("program manager");
    variants.add("program management");
  }

  if (roleNorm.includes("project manager")) {
    variants.add("project manager");
    variants.add("project management");
  }

  return [...variants].sort((left, right) => right.length - left.length);
};

export const matchesRole = (job: Pick<JobRecord, "title" | "description">, role: string): boolean => {
  const roleNorm = normalize(role);
  if (!roleNorm) {
    return true;
  }

  const titleText = normalize(job.title);
  const descriptionText = normalize(job.description);
  const combined = `${titleText} ${descriptionText}`.trim();
  if (!combined) {
    return false;
  }

  if (roleVariants(roleNorm).some((variant) => variant && combined.includes(variant))) {
    return true;
  }

  const roleTokens = tokenize(roleNorm).filter((token) => token !== "and" && token !== "or");
  const titleTokens = new Set(tokenize(titleText));
  if (roleTokens.length === 0 || titleTokens.size === 0) {
    return false;
  }

  const overlap = roleTokens.filter((token) => titleTokens.has(token)).length;
  if (roleTokens.length <= 2) {
    return overlap === roleTokens.length;
  }

  return overlap >= Math.max(2, Math.round(roleTokens.length * 0.6));
};

const extractPrimaryCityToken = (location: string): string | null => {
  const firstSegment = normalize(location).split(",")[0]?.trim() ?? "";
  const tokens = tokenize(firstSegment).filter((token) => token.length >= 3);
  return tokens[0] ?? null;
};

export const matchesLocation = (
  job: Pick<JobRecord, "location" | "job_type">,
  desiredLocation: string,
): boolean => {
  const desired = normalize(desiredLocation);
  if (!desired) {
    return true;
  }

  const jobLocation = normalize(job.location);
  const jobType = normalize(job.job_type);

  if (desired.includes("remote")) {
    return jobLocation.includes("remote") || jobType.includes("remote");
  }

  if (jobLocation.includes("remote")) {
    return false;
  }

  if (!jobLocation) {
    return false;
  }

  if (jobLocation.includes(desired)) {
    return true;
  }

  const desiredCity = extractPrimaryCityToken(desired);
  if (desiredCity && !jobLocation.includes(desiredCity)) {
    return false;
  }

  const desiredTokens = tokenize(desired).filter(
    (token) => !["india", "united", "states", "state", "region"].includes(token),
  );

  return desiredTokens.some((token) => jobLocation.includes(token));
};

export const matchesJob = (job: Pick<JobRecord, "title" | "description" | "location" | "job_type">, role: string, location: string): boolean =>
  matchesRole(job, role) && matchesLocation(job, location);

export const dedupeKey = (job: Pick<JobRecord, "apply_url" | "title" | "company" | "location">): string => {
  const applyUrl = normalize(job.apply_url);
  if (applyUrl) {
    return `url:${applyUrl}`;
  }

  return [
    "fallback",
    normalize(job.title),
    normalize(job.company),
    normalize(job.location),
  ].join("|");
};
