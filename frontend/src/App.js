/**
 * Main App component for Job Scrapper.
 */
import React, { useState } from 'react';
import * as XLSX from 'xlsx';
import ScrapingProgress from './components/ScrapingProgress';
import JobList from './components/JobList';
import {
  startScraping,
  getScrapingStatus,
  getScrapedJobs,
} from './services/api';
import './App.css';

const DEFAULT_TARGET_JOBS = 25;
const MIN_TARGET_JOBS = 1;
const MAX_TARGET_JOBS = 200;
const POLL_INTERVAL_MS = 2500;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function App() {
  const [step, setStep] = useState('search'); // search, scraping, results
  const [roleTitles, setRoleTitles] = useState('');
  const [locations, setLocations] = useState('');
  const [targetJobs, setTargetJobs] = useState(String(DEFAULT_TARGET_JOBS));
  const [scrapingStatus, setScrapingStatus] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [error, setError] = useState(null);
  const [meta, setMeta] = useState({
    parsedRoles: [],
    parsedLocations: [],
    targetJobs: DEFAULT_TARGET_JOBS,
  });

  const pollTaskWithLiveJobs = async (taskId, jobsLimit) => {
    while (true) {
      const status = await getScrapingStatus(taskId);
      setScrapingStatus(status);

      try {
        const jobsResponse = await getScrapedJobs({
          limit: jobsLimit,
          taskId,
        });
        setJobs(jobsResponse.jobs || []);
      } catch (jobsError) {
        // Keep polling status even if jobs endpoint briefly fails.
      }

      if (status.status === 'completed') {
        return status;
      }
      if (status.status === 'failed') {
        throw new Error(status.error_message || 'Scraping failed');
      }

      await sleep(POLL_INTERVAL_MS);
    }
  };

  const handleStartScraping = async () => {
    if (!roleTitles.trim()) {
      setError('Enter at least one role title.');
      return;
    }

    const parsedTargetJobs = Number(targetJobs);
    if (!Number.isInteger(parsedTargetJobs) || parsedTargetJobs < MIN_TARGET_JOBS || parsedTargetJobs > MAX_TARGET_JOBS) {
      setError('Enter a target between 1 and 200 jobs.');
      return;
    }

    try {
      setError(null);
      setStep('scraping');
      setJobs([]);

      const taskResponse = await startScraping({
        roleTitles,
        locations,
        targetJobs: parsedTargetJobs,
      });

      setMeta({
        parsedRoles: taskResponse.parsed_roles || [],
        parsedLocations: taskResponse.parsed_locations || [],
        targetJobs: taskResponse.target_jobs || parsedTargetJobs,
      });

      await pollTaskWithLiveJobs(taskResponse.task_id, parsedTargetJobs);
      setStep('results');
    } catch (scrapeError) {
      const errorMsg = scrapeError.response?.data?.detail || scrapeError.message || 'Scraping failed';
      setError(errorMsg);
      setStep('search');
    }
  };

  const handleReset = () => {
    setStep('search');
    setScrapingStatus(null);
    setJobs([]);
    setError(null);
  };

  const handleDownloadExcel = () => {
    if (!jobs || jobs.length === 0) {
      return;
    }

    const sortedJobs = [...jobs].sort((a, b) => {
      const dateA = a.posted_date ? new Date(a.posted_date).getTime() : 0;
      const dateB = b.posted_date ? new Date(b.posted_date).getTime() : 0;
      return dateB - dateA;
    });

    const rows = sortedJobs.map((job) => {
      const postedDate = job.posted_date
        ? new Date(job.posted_date).toISOString().slice(0, 10)
        : '';

      return {
        'Company Name': job.company || '',
        'Role Name': job.title || '',
        Location: job.location || '',
        'Posted Date': postedDate,
        'Link to Apply': job.apply_url || '',
      };
    });

    const worksheet = XLSX.utils.json_to_sheet(rows);
    worksheet['!cols'] = [
      { wch: 30 },
      { wch: 45 },
      { wch: 25 },
      { wch: 14 },
      { wch: 80 },
    ];

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Jobs');
    XLSX.writeFile(workbook, `job_list_${new Date().toISOString().slice(0, 10)}.xlsx`);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Job Assistant</h1>
          <p className="text-gray-600 mt-1">
            Search the most recent jobs and export them.
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {step === 'search' && (
          <div className="bg-white rounded-lg shadow-md p-6 max-w-3xl mx-auto space-y-5">
            <h2 className="text-2xl font-bold text-gray-800">Search jobs</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Role titles
              </label>
              <input
                type="text"
                value={roleTitles}
                onChange={(e) => setRoleTitles(e.target.value)}
                placeholder="SDE, Software Engineer, Backend Engineer"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-2">Separate multiple titles with commas.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Locations
              </label>
              <input
                type="text"
                value={locations}
                onChange={(e) => setLocations(e.target.value)}
                placeholder="Remote, New York, San Francisco"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-2">Leave blank to search across all locations.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target jobs (up to 200)
              </label>
              <input
                type="number"
                min={MIN_TARGET_JOBS}
                max={MAX_TARGET_JOBS}
                step="1"
                value={targetJobs}
                onChange={(e) => setTargetJobs(e.target.value)}
                placeholder={String(DEFAULT_TARGET_JOBS)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
              Target: {targetJobs || DEFAULT_TARGET_JOBS} jobs. The scraper keeps going back in time until it reaches the target or runs out of matches.
            </div>

            <button
              onClick={handleStartScraping}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors duration-200"
            >
              Start search
            </button>
          </div>
        )}

        {step === 'scraping' && (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Searching jobs</h2>
              <p className="text-gray-600">
                Pulling the latest matches and loading results as they arrive.
              </p>
            </div>

            <ScrapingProgress status={scrapingStatus} />

            <div className="bg-white rounded-lg shadow-md p-6 max-w-3xl mx-auto">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Search summary</h3>
              <div className="space-y-2 text-sm text-gray-700">
                <div><span className="font-medium">Roles:</span> {meta.parsedRoles.join(', ') || '-'}</div>
                <div><span className="font-medium">Locations:</span> {meta.parsedLocations.join(', ') || 'Any'}</div>
                <div><span className="font-medium">Target:</span> {meta.targetJobs}</div>
                <div><span className="font-medium">Jobs found:</span> {jobs.length}</div>
              </div>
            </div>

            <div className="flex justify-between items-center">
              <h3 className="text-xl font-bold text-gray-800">Live results ({jobs.length})</h3>
              <button
                onClick={handleDownloadExcel}
                disabled={jobs.length === 0}
                className={`px-5 py-2 rounded-lg text-white font-medium transition-colors duration-200 ${
                  jobs.length === 0
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                Download
              </button>
            </div>
            <JobList jobs={jobs} />
          </div>
        )}

        {step === 'results' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center mb-8">
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">Results</h2>
                <p className="text-gray-600">{jobs.length} jobs found</p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleDownloadExcel}
                  className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors duration-200"
                >
                  Download
                </button>
                <button
                  onClick={handleReset}
                  className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white font-medium rounded-lg transition-colors duration-200"
                >
                  New search
                </button>
              </div>
            </div>

            <JobList jobs={jobs} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
