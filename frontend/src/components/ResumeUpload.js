/**
 * Resume upload component with drag-and-drop support.
 */
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { FiUpload, FiFile, FiCheckCircle } from 'react-icons/fi';

const ResumeUpload = ({ onUploadSuccess, onUploadError }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setUploadedFile(file);
      setUploading(true);

      // Call parent's upload handler
      if (onUploadSuccess) {
        onUploadSuccess(file)
          .then(() => {
            setUploading(false);
          })
          .catch((error) => {
            setUploading(false);
            setUploadedFile(null);
            if (onUploadError) {
              onUploadError(error);
            }
          });
      }
    }
  }, [onUploadSuccess, onUploadError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: false,
    disabled: uploading,
  });

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-all duration-200
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'}
          ${uploading ? 'opacity-50 cursor-not-allowed' : 'hover:border-blue-400 hover:bg-gray-50'}
        `}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center space-y-4">
          {uploading ? (
            <>
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500"></div>
              <p className="text-lg font-medium text-gray-700">Analyzing resume...</p>
              <p className="text-sm text-gray-500">This may take a few seconds</p>
            </>
          ) : uploadedFile ? (
            <>
              <FiCheckCircle className="text-green-500 text-6xl" />
              <p className="text-lg font-medium text-gray-700">
                Resume uploaded successfully!
              </p>
              <p className="text-sm text-gray-500">{uploadedFile.name}</p>
            </>
          ) : (
            <>
              <FiUpload className="text-gray-400 text-6xl" />
              <div>
                <p className="text-lg font-medium text-gray-700">
                  {isDragActive ? 'Drop your resume here' : 'Upload your resume'}
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  Drag and drop, or click to select
                </p>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-400">
                <FiFile />
                <span>Supports PDF and DOCX (max 10MB)</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResumeUpload;
