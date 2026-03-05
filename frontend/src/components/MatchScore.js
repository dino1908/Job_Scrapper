/**
 * Match score visualization component.
 */
import React from 'react';

const MatchScore = ({ score, breakdown, size = 'normal' }) => {
  const getScoreColor = (score) => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'blue';
    if (score >= 40) return 'yellow';
    return 'gray';
  };

  const color = getScoreColor(score);
  const isLarge = size === 'large';

  const scoreClasses = {
    green: 'bg-green-100 text-green-800 border-green-300',
    blue: 'bg-blue-100 text-blue-800 border-blue-300',
    yellow: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    gray: 'bg-gray-100 text-gray-800 border-gray-300',
  };

  return (
    <div className={`inline-flex flex-col ${isLarge ? 'space-y-3' : 'space-y-2'}`}>
      {/* Score Badge */}
      <div
        className={`
          ${scoreClasses[color]}
          ${isLarge ? 'text-2xl px-4 py-2' : 'text-lg px-3 py-1'}
          border-2 rounded-lg font-bold text-center
        `}
      >
        {Math.round(score)}%
      </div>

      {/* Breakdown (if provided) */}
      {breakdown && isLarge && (
        <div className="text-xs text-gray-600 space-y-1">
          <div className="flex justify-between">
            <span>Skills:</span>
            <span className="font-medium">{breakdown.skills_score.toFixed(1)}/40</span>
          </div>
          <div className="flex justify-between">
            <span>Experience:</span>
            <span className="font-medium">{breakdown.experience_score.toFixed(1)}/25</span>
          </div>
          <div className="flex justify-between">
            <span>Title:</span>
            <span className="font-medium">{breakdown.title_score.toFixed(1)}/20</span>
          </div>
          <div className="flex justify-between">
            <span>Location:</span>
            <span className="font-medium">{breakdown.location_score.toFixed(1)}/10</span>
          </div>
          <div className="flex justify-between">
            <span>Job Type:</span>
            <span className="font-medium">{breakdown.job_type_score.toFixed(1)}/5</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default MatchScore;
