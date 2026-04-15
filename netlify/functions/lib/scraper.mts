import { load } from "cheerio";

import type { JobRecord, TaskRecord } from "./contracts.mjs";
import { dedupeKey, matchesJob, normalize } from "./parsing.mjs";
import { readTask, writeJobs, writeTask } from "./store.mjs";

const LINKEDIN_BASE_URL = "https://www.linkedin.com";
const LINKEDIN_SEARCH_URL = `${LINKEDIN_BASE_URL}/jobs-guest/jobs/api/seeMoreJobPostings/search`;
const MAX_TARGET_JOBS = 200;
const MAX_LINKEDIN_RESULTS = 200;
const MAX_BACKFILL_DAYS = 45;
const EMPTY_ROUND_LIMIT = 3;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const randomBetween = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min;

const toIsoString = (value: Date | null): string | null => (value ? value.toISOString() : null);

const parseRelativeDate = (value: string): Date | null => {
  const text = normalize(value);
  if (!text) {
    return null;
  }

  const now = new Date();
  if (text.includes("today") || text.includes("just now")) {
    return now;
  }
  if (text.includes("yesterday")) {
    return new Date(now.getTime() - 24 * 60 * 60 * 1000);
  }

  const patterns: Array<[RegExp, number]> = [
    [/(\d+)\s*hour/, 60 * 60 * 1000],
    [/(\d+)\s*day/, 24 * 60 * 60 * 1000],
    [/(\d+)\s*week/, 7 * 24 * 60 * 60 * 1000],
    [/(\d+)\s*month/, 30 * 24 * 60 * 60 * 1000],
  ];

  for (const [pattern, unitMs] of patterns) {
    const match = text.match(pattern);
    if (!match) {
      continue;
    }
    const amount = Number.parseInt(match[1] ?? "", 10);
    if (!Number.isFinite(amount)) {
      continue;
    }
    return new Date(now.getTime() - amount * unitMs);
  }

  return null;
};

const parsePostedDate = (datetimeValue: string | undefined, relativeText: string): Date | null => {
  if (datetimeValue) {
    const parsed = new Date(datetimeValue);
    if (!Number.isNaN(parsed.getTime())) {
      return parsed;
    }
  }

  return parseRelativeDate(relativeText);
};

const canonicalizeUrl = (value: string): string => {
  try {
    const url = new URL(value, LINKEDIN_BASE_URL);
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch {
    return value;
  }
};

const toJobRecord = (
  id: number,
  raw: {
    title: string;
    company: string;
    location: string;
    job_type: string | null;
    apply_url: string;
    posted_date: Date | null;
  },
): JobRecord => ({
  id,
  title: raw.title,
  company: raw.company,
  location: raw.location || null,
  job_type: raw.job_type,
  employment_type: "full-time",
  description: "",
  required_skills: [],
  required_experience: null,
  salary_range: null,
  apply_url: raw.apply_url,
  source: "linkedin",
  posted_date: toIsoString(raw.posted_date),
  scraped_at: new Date().toISOString(),
});

const buildQueryVariants = (title: string): string[] => {
  const variants = new Set<string>();
  const cleanedTitle = title.trim();
  const shortTitle = cleanedTitle
    .split(/[\s,/\\-]+/)
    .filter(Boolean)
    .slice(0, 4)
    .join(" ");

  for (const variant of [cleanedTitle, shortTitle]) {
    if (variant) {
      variants.add(variant);
    }
  }

  const normalizedTitle = normalize(cleanedTitle).replaceAll(".", "");
  if (normalizedTitle === "pm") {
    variants.add("product manager");
    variants.add("program manager");
    variants.add("project manager");
  }
  if (normalizedTitle.includes("product manager")) {
    variants.add("product management");
  }

  return [...variants];
};

const scrapeLinkedInJobs = async ({
  title,
  location,
  limit,
  recentDays,
}: {
  title: string;
  location: string;
  limit: number;
  recentDays: number;
}): Promise<JobRecord[]> => {
  const effectiveLimit = Math.min(Math.max(limit, 50), MAX_LINKEDIN_RESULTS);
  const uniqueJobs: JobRecord[] = [];
  const seenKeys = new Set<string>();
  let nextId = 1;

  for (const query of buildQueryVariants(title)) {
    if (uniqueJobs.length >= effectiveLimit) {
      break;
    }

    let start = 0;
    const pageSize = 25;
    const maxPages = Math.min(12, Math.max(3, Math.ceil((effectiveLimit * 2) / pageSize)));

    for (let page = 0; page < maxPages; page += 1) {
      await sleep(randomBetween(300, 900));

      const params = new URLSearchParams({
        keywords: query,
        location,
        start: String(start),
        f_TPR: `r${recentDays * 24 * 60 * 60}`,
        sortBy: "DD",
      });
      start += pageSize;

      const response = await fetch(`${LINKEDIN_SEARCH_URL}?${params.toString()}`, {
        headers: {
          "accept-language": "en-US,en;q=0.9",
          "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        },
        signal: AbortSignal.timeout(30000),
      });

      if (!response.ok) {
        break;
      }

      const html = await response.text();
      const $ = load(html);
      const cards = $("li");

      if (cards.length === 0) {
        break;
      }

      for (const element of cards.toArray()) {
        if (uniqueJobs.length >= effectiveLimit) {
          break;
        }

        const titleText =
          $(element).find("h3.base-search-card__title").text().trim() ||
          $(element).find("h3").first().text().trim();
        const companyText =
          $(element).find("h4.base-search-card__subtitle a").text().trim() ||
          $(element).find("h4.base-search-card__subtitle").text().trim();
        const locationText = $(element).find("span.job-search-card__location").text().trim();
        const linkValue =
          $(element).find("a.base-card__full-link").attr("href") ||
          $(element).find("a[href*='/jobs/view/']").attr("href") ||
          "";
        const timeElement = $(element).find("time").first();

        if (!titleText || !companyText || !linkValue) {
          continue;
        }

        const applyUrl = canonicalizeUrl(linkValue);
        const locationLower = normalize(locationText);
        const jobType = locationLower.includes("remote")
          ? "remote"
          : locationLower.includes("hybrid")
            ? "hybrid"
            : null;

        const job = toJobRecord(nextId, {
          title: titleText,
          company: companyText,
          location: locationText,
          job_type: jobType,
          apply_url: applyUrl,
          posted_date: parsePostedDate(timeElement.attr("datetime"), timeElement.text().trim()),
        });

        const key = dedupeKey(job);
        if (seenKeys.has(key)) {
          continue;
        }

        seenKeys.add(key);
        uniqueJobs.push(job);
        nextId += 1;
      }
    }
  }

  uniqueJobs.sort((left, right) => {
    const leftDate = left.posted_date ? new Date(left.posted_date).getTime() : 0;
    const rightDate = right.posted_date ? new Date(right.posted_date).getTime() : 0;
    return rightDate - leftDate;
  });

  return uniqueJobs.slice(0, effectiveLimit);
};

const updateTask = async (taskId: string, patch: Partial<TaskRecord>): Promise<void> => {
  const existing = await readTask(taskId);
  if (!existing) {
    return;
  }

  await writeTask({
    ...existing,
    ...patch,
  });
};

export const runScrapeTask = async ({
  taskId,
  roles,
  locations,
  targetJobs,
}: {
  taskId: string;
  roles: string[];
  locations: string[];
  targetJobs: number;
}): Promise<void> => {
  const sanitizedTarget = Math.min(Math.max(targetJobs, 1), MAX_TARGET_JOBS);
  const combos = roles.flatMap((role) => locations.map((location) => ({ role, location })));
  const collectedJobs: JobRecord[] = [];
  const seenSelectedKeys = new Set<string>();
  let nextStoredId = 1;
  let emptyRounds = 0;

  await updateTask(taskId, {
    status: "running",
    started_at: new Date().toISOString(),
    progress: 1,
    sources_completed: [],
    error_message: null,
  });
  await writeJobs(taskId, []);

  try {
    const totalCombos = Math.max(combos.length, 1);
    const maxRounds = MAX_BACKFILL_DAYS;

    for (let roundIndex = 1; roundIndex <= maxRounds; roundIndex += 1) {
      if (collectedJobs.length >= sanitizedTarget) {
        break;
      }

      const currentWindowDays = roundIndex;
      let roundAdded = 0;
      const cutoff = Date.now() - currentWindowDays * 24 * 60 * 60 * 1000;

      await updateTask(taskId, {
        sources_completed: [`linkedin:last_${currentWindowDays}_days`],
      });

      for (let comboIndex = 0; comboIndex < combos.length; comboIndex += 1) {
        if (collectedJobs.length >= sanitizedTarget) {
          break;
        }

        const combo = combos[comboIndex];
        const remaining = sanitizedTarget - collectedJobs.length;
        const perComboLimit = Math.min(MAX_LINKEDIN_RESULTS, Math.max(80, remaining * 3));
        const scrapedJobs = await scrapeLinkedInJobs({
          title: combo.role,
          location: combo.location,
          limit: perComboLimit,
          recentDays: currentWindowDays,
        });

        for (const scrapedJob of scrapedJobs) {
          const postedAt = scrapedJob.posted_date ? new Date(scrapedJob.posted_date).getTime() : Number.POSITIVE_INFINITY;
          if (postedAt < cutoff) {
            continue;
          }

          if (!matchesJob(scrapedJob, combo.role, combo.location)) {
            continue;
          }

          const key = dedupeKey(scrapedJob);
          if (seenSelectedKeys.has(key)) {
            continue;
          }

          seenSelectedKeys.add(key);
          collectedJobs.push({
            ...scrapedJob,
            id: nextStoredId,
            scraped_at: new Date().toISOString(),
          });
          nextStoredId += 1;
          roundAdded += 1;

          if (collectedJobs.length >= sanitizedTarget) {
            break;
          }
        }

        const comboProgress = Math.round(((comboIndex + 1) / totalCombos) * 15);
        const roundProgress = Math.round((roundIndex / maxRounds) * 20);
        const countProgress = Math.round((collectedJobs.length / sanitizedTarget) * 60);

        await writeJobs(taskId, collectedJobs);
        await updateTask(taskId, {
          progress: Math.min(95, Math.max(1, comboProgress + roundProgress + countProgress)),
          total_jobs_scraped: collectedJobs.length,
        });
      }

      if (roundAdded === 0) {
        emptyRounds += 1;
      } else {
        emptyRounds = 0;
      }

      if (emptyRounds >= EMPTY_ROUND_LIMIT) {
        break;
      }
    }

    await writeJobs(taskId, collectedJobs);
    await updateTask(taskId, {
      status: "completed",
      completed_at: new Date().toISOString(),
      progress: 100,
      total_jobs_scraped: collectedJobs.length,
      sources_completed: ["linkedin"],
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unexpected scraping failure";
    await updateTask(taskId, {
      status: "failed",
      error_message: message,
      completed_at: new Date().toISOString(),
    });
  }
};
