/**
 * Simple jobs table sorted by posted date.
 */
import React from 'react';

const formatPostedDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleDateString();
};

const JobList = ({ jobs }) => {
  if (!jobs || jobs.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg">No jobs found.</p>
      </div>
    );
  }

  const sortedJobs = [...jobs].sort((a, b) => {
    const dateA = a.posted_date ? new Date(a.posted_date).getTime() : 0;
    const dateB = b.posted_date ? new Date(b.posted_date).getTime() : 0;
    return dateB - dateA;
  });

  return (
    <div className="w-full overflow-x-auto bg-white rounded-lg shadow-md">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Company Name</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Role Name</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Location</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Posted Date</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Link to Apply</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {sortedJobs.map((job, index) => (
            <tr key={`${job.id}-${index}`} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-800">{job.company || '-'}</td>
              <td className="px-4 py-3 text-sm text-gray-800">{job.title || '-'}</td>
              <td className="px-4 py-3 text-sm text-gray-800">{job.location || '-'}</td>
              <td className="px-4 py-3 text-sm text-gray-800">{formatPostedDate(job.posted_date)}</td>
              <td className="px-4 py-3 text-sm">
                {job.apply_url ? (
                  <a
                    href={job.apply_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-700 underline"
                  >
                    Apply
                  </a>
                ) : '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default JobList;
