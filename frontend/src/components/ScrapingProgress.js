/**
 * Scraping progress component with status updates.
 */
import React from 'react';
import { FiLoader, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';

const ScrapingProgress = ({ status }) => {
  if (!status) return null;

  const { status: statusType, progress, total_jobs_scraped, sources_completed, error_message } = status;

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
        return 'Starting job search...';
      case 'running':
        return 'Scraping latest LinkedIn jobs...';
      case 'completed':
        return `Found ${total_jobs_scraped} jobs!`;
      case 'failed':
        return 'Job scraping failed';
      default:
        return '';
    }
  };

  const getStatusColor = () => {
    switch (statusType) {
      case 'pending':
      case 'running':
        return 'blue';
      case 'completed':
        return 'green';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  };

  const color = getStatusColor();

  return (
    <div className="w-full max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-6">
      <div className="flex flex-col items-center space-y-4">
        {/* Status Icon */}
        {getStatusIcon()}

        {/* Status Text */}
        <div className="text-center">
          <h3 className="text-xl font-semibold text-gray-800">{getStatusText()}</h3>

          {error_message && (
            <p className="text-sm text-red-600 mt-2">{error_message}</p>
          )}
        </div>

        {/* Progress Bar */}
        {(statusType === 'pending' || statusType === 'running') && (
          <div className="w-full">
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className={`h-full bg-${color}-500 transition-all duration-300 rounded-full`}
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 text-center mt-2">{progress}% complete</p>
          </div>
        )}

        {/* Sources Progress */}
        {sources_completed && sources_completed.length > 0 && (
          <div className="w-full mt-4">
            <p className="text-sm font-medium text-gray-700 mb-2">Completed Source:</p>
            <div className="flex flex-wrap gap-2">
              {sources_completed.map((source) => (
                <span
                  key={source}
                  className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium"
                >
                  {source}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Jobs Count */}
        {total_jobs_scraped > 0 && (
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-800">{total_jobs_scraped}</p>
            <p className="text-sm text-gray-600">jobs found</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScrapingProgress;
