/**
 * Main App component for Job Scrapper.
 */
import React, { useState } from 'react';
import * as XLSX from 'xlsx';
import ScrapingProgress from './components/ScrapingProgress';
import JobList from './components/JobList';
import {
  startScraping,
  pollScrapingStatus,
  getScrapedJobs,
} from './services/api';
import './App.css';

function App() {
  const [step, setStep] = useState('search'); // search, scraping, results
  const [roleTitles, setRoleTitles] = useState('');
  const [locations, setLocations] = useState('');
  const [scrapingStatus, setScrapingStatus] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [error, setError] = useState(null);
  const [meta, setMeta] = useState({ parsedRoles: [], parsedLocations: [], targetJobs: 200 });

  const handleStartScraping = async () => {
    if (!roleTitles.trim()) {
      setError('Please enter at least one role title.');
      return;
    }

    try {
      setError(null);
      setStep('scraping');
      setJobs([]);

      const taskResponse = await startScraping({
        roleTitles,
        locations,
        targetJobs: 200,
      });

      setMeta({
        parsedRoles: taskResponse.parsed_roles || [],
        parsedLocations: taskResponse.parsed_locations || [],
        targetJobs: taskResponse.target_jobs || 200,
      });

      await pollScrapingStatus(
        taskResponse.task_id,
        (status) => {
          setScrapingStatus(status);
        },
        2000
      );

      const response = await getScrapedJobs({
        limit: 200,
        taskId: taskResponse.task_id,
      });

      setJobs(response.jobs || []);
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
          <h1 className="text-3xl font-bold text-gray-900">Job Scrapper</h1>
          <p className="text-gray-600 mt-1">
            LinkedIn latest jobs scraper (last 10 days)
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
            <h2 className="text-2xl font-bold text-gray-800">Search Inputs</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Role Titles (comma-separated)
              </label>
              <input
                type="text"
                value={roleTitles}
                onChange={(e) => setRoleTitles(e.target.value)}
                placeholder="SDE, SDE1, Software Engineer, Backend Engineer"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Locations (comma-separated)
              </label>
              <input
                type="text"
                value={locations}
                onChange={(e) => setLocations(e.target.value)}
                placeholder="United States, Remote, New York, San Francisco"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
              Target: 200 jobs | Minimum expected: 100 (if available) | Window: last 10 days
            </div>

            <button
              onClick={handleStartScraping}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors duration-200"
            >
              Start Scraping
            </button>
          </div>
        )}

        {step === 'scraping' && (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Scraping LinkedIn Jobs</h2>
              <p className="text-gray-600">
                Fetching latest jobs and paging backward until target count is reached...
              </p>
            </div>

            <ScrapingProgress status={scrapingStatus} />

            <div className="bg-white rounded-lg shadow-md p-6 max-w-3xl mx-auto">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Input Summary</h3>
              <div className="space-y-2 text-sm text-gray-700">
                <div><span className="font-medium">Roles:</span> {meta.parsedRoles.join(', ') || '-'}</div>
                <div><span className="font-medium">Locations:</span> {meta.parsedLocations.join(', ') || 'Any'}</div>
                <div><span className="font-medium">Target Jobs:</span> {meta.targetJobs}</div>
              </div>
            </div>
          </div>
        )}

        {step === 'results' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center mb-8">
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">Scraped Jobs</h2>
                <p className="text-gray-600">{jobs.length} jobs found</p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleDownloadExcel}
                  className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors duration-200"
                >
                  Download Excel
                </button>
                <button
                  onClick={handleReset}
                  className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white font-medium rounded-lg transition-colors duration-200"
                >
                  New Search
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
