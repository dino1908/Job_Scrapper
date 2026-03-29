/**
 * Scraping progress component with status updates.
 */
import React from 'react';
import { FiLoader, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';

const STATUS_COLORS = {
  pending: 'bg-blue-500',
  running: 'bg-blue-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
};

const ScrapingProgress = ({ status }) => {
  if (!status) return null;

  const {
    status: statusType,
    progress = 0,
    total_jobs_scraped = 0,
    error_message,
  } = status;

  const getStatusIcon = () => {
    switch (statusType) {
      case 'pending':
      case 'running':
        return <FiLoader className="animate-spin text-blue-500 text-4xl" />;
      case 'completed':
        return <FiCheckCircle className="text-green-500 text-4xl" />;
      case 'failed':
        return <FiAlertCircle className="text-red-500 text-4xl" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (statusType) {
      case 'pending':
        return 'Starting your search...';
      case 'running':
        return 'Finding matching jobs...';
      case 'completed':
        return `Found ${total_jobs_scraped} jobs`;
      case 'failed':
        return 'Search failed';
      default:
        return '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-6">
      <div className="flex flex-col items-center space-y-4">
        {getStatusIcon()}

        <div className="text-center">
          <h3 className="text-xl font-semibold text-gray-800">{getStatusText()}</h3>

          {error_message && (
            <p className="text-sm text-red-600 mt-2">{error_message}</p>
          )}
        </div>

        {(statusType === 'pending' || statusType === 'running') && (
          <div className="w-full">
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className={`h-full transition-all duration-300 rounded-full ${STATUS_COLORS[statusType] || 'bg-gray-500'}`}
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 text-center mt-2">{progress}% complete</p>
          </div>
        )}

        {total_jobs_scraped > 0 && (
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-800">{total_jobs_scraped}</p>
            <p className="text-sm text-gray-600">jobs found so far</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScrapingProgress;
