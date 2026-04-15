/**
 * API service for communicating with the backend.
 */
import axios from 'axios';

const getApiUrl = () => {
  const rawApiUrl = (process.env.REACT_APP_API_URL || '').trim();
  if (rawApiUrl) {
    return rawApiUrl
      .replace(/\/+$/, '')
      .replace(/\/api$/i, '');
  }

  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin;
  }

  return '';
};

const API_URL = getApiUrl();

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Start job scraping from direct role/location inputs.
 * @param {Object} params - Scraping params
 * @param {string} params.roleTitles - Comma-separated role titles
 * @param {string} params.locations - Comma-separated locations
 * @param {number} params.targetJobs - Target jobs (1-200)
 * @returns {Promise} - Task information
 */
export const startScraping = async ({
  roleTitles,
  locations,
  targetJobs = 25,
}) => {
  const payload = {
    role_titles: roleTitles,
    locations: locations || '',
    target_jobs: targetJobs,
  };

  const response = await api.post('/scrape-jobs', payload);
  return response.data;
};

/**
 * Get scraping task status
 * @param {string} taskId - Scraping task ID
 * @returns {Promise} - Task status
 */
export const getScrapingStatus = async (taskId) => {
  const response = await api.get(`/scraping-status?taskId=${encodeURIComponent(taskId)}`);
  return response.data;
};

/**
 * Get latest scraped jobs.
 * @param {Object} options - Options
 * @param {number} options.limit - Max jobs
 * @returns {Promise} - Scraped jobs
 */
export const getScrapedJobs = async (options = {}) => {
  const payload = {
    limit: options.limit ?? 25,
  };

  const response = await api.post(`/jobs?taskId=${encodeURIComponent(options.taskId || '')}`, payload);
  return response.data;
};

export default api;
