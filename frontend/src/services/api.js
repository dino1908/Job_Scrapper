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
    recent_days: 10,
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
 * @param {string} options.taskId - Optional task id
 * @returns {Promise} - Scraped jobs
 */
export const getScrapedJobs = async (options = {}) => {
  const payload = {
    limit: options.limit ?? 25,
    task_id: options.taskId || null,
  };

  const response = await api.post('/jobs', payload);
  return response.data;
};

/**
 * Poll scraping status until complete.
 * @param {string} taskId - Task ID
 * @param {Function} onProgress - Progress callback
 * @param {number} interval - Polling interval in ms
 * @returns {Promise} - Final task status
 */
export const pollScrapingStatus = async (
  taskId,
  onProgress = null,
  interval = 2000
) => {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await getScrapingStatus(taskId);

        if (onProgress) {
          onProgress(status);
        }

        if (status.status === 'completed') {
          resolve(status);
        } else if (status.status === 'failed') {
          reject(new Error(status.error_message || 'Scraping failed'));
        } else {
          setTimeout(poll, interval);
        }
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
};

export default api;
