/**
 * API service for communicating with the backend.
 */
import axios from 'axios';

const RAW_API_URL = (process.env.REACT_APP_API_URL || 'http://localhost:8000').trim();
const API_URL = RAW_API_URL
  .replace(/\/+$/, '')      // remove trailing slashes
  .replace(/\/api$/i, '');  // remove accidental /api suffix

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
  const response = await api.get(`/scraping-status/${taskId}`);
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

  const response = await api.post('/jobs', payload);
  return response.data;
};

export default api;
