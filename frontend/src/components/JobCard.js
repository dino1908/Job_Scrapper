/**
 * Individual job card component.
 */
import React, { useState } from 'react';
import { FiMapPin, FiBriefcase, FiDollarSign, FiExternalLink, FiChevronDown, FiChevronUp } from 'react-icons/fi';

const JobCard = ({ job }) => {
  const [expanded, setExpanded] = useState(false);

  const {
    title,
    company,
    location,
    job_type,
    employment_type,
    description,
    required_skills,
    salary_range,
    apply_url,
    source,
  } = job;

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden">
      <div className="p-6">
        {/* Header */}
        <div className="mb-4">
          <div className="flex-1">
            <h3 className="text-xl font-bold text-gray-800 mb-1">{title}</h3>
            <p className="text-lg text-gray-600">{company}</p>
          </div>
        </div>

        {/* Metadata */}
        <div className="flex flex-wrap gap-3 mb-4 text-sm text-gray-600">
          {location && (
            <div className="flex items-center space-x-1">
              <FiMapPin />
              <span>{location}</span>
            </div>
          )}

          {job_type && (
            <div className="flex items-center space-x-1">
              <FiBriefcase />
              <span className="capitalize">{job_type}</span>
            </div>
          )}

          {employment_type && (
            <span className="px-2 py-1 bg-gray-100 rounded-full text-xs font-medium">
              {employment_type}
            </span>
          )}

          {salary_range && (
            <div className="flex items-center space-x-1">
              <FiDollarSign />
              <span>{salary_range}</span>
            </div>
          )}

          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
            {source}
          </span>
        </div>

        {/* Skills */}
        {required_skills && required_skills.length > 0 && (
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-700 mb-2">Skills:</p>
            <div className="flex flex-wrap gap-2">
              {required_skills.slice(0, 8).map((skill, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium"
                >
                  {skill}
                </span>
              ))}
              {required_skills.length > 8 && (
                <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                  +{required_skills.length - 8} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Description (Expandable) */}
        {description && (
          <div className="mb-4">
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center space-x-2 text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              <span>{expanded ? 'Hide' : 'Show'} Description</span>
              {expanded ? <FiChevronUp /> : <FiChevronDown />}
            </button>

            {expanded && (
              <div className="mt-3 text-sm text-gray-700 bg-gray-50 p-4 rounded-lg max-h-48 overflow-y-auto">
                {description.substring(0, 500)}
                {description.length > 500 && '...'}
              </div>
            )}
          </div>
        )}

        {/* Apply Button */}
        <a
          href={apply_url}
          target="_blank"
          rel="noopener noreferrer"
          className="
            inline-flex items-center space-x-2 px-6 py-3
            bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg
            transition-colors duration-200
          "
        >
          <span>Apply Now</span>
          <FiExternalLink />
        </a>
      </div>
    </div>
  );
};

export default JobCard;
