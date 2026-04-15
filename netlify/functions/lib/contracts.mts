export interface JobRecord {
  id: number;
  title: string;
  company: string;
  location: string | null;
  job_type: string | null;
  employment_type: string | null;
  description: string | null;
  required_skills: string[];
  required_experience: number | null;
  salary_range: string | null;
  apply_url: string;
  source: string;
  posted_date: string | null;
  scraped_at: string;
}

export interface TaskRecord {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  total_jobs_scraped: number;
  sources_completed: string[];
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  parsed_roles: string[];
  parsed_locations: string[];
  target_jobs: number;
}

export interface ScrapeRequestBody {
  role_titles: string;
  locations?: string;
  target_jobs?: number;
}
