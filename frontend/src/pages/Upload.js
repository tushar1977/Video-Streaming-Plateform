import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../Context/AuthContext";
import apiClient, { uploadClient } from "../api/apiClient";

export default function Upload() {
  const navigate = useNavigate();
  const { isAuthenticated, user, token } = useAuth();
  const [videoTitle, setVideoTitle] = useState("");
  const [videoDesc, setVideoDesc] = useState("");
  const [thumbnail, setThumbnail] = useState(null);
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState("");
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/auth");
    }
  }, [isAuthenticated, navigate]);

  const uploadWithProgress = async (e) => {
    e.preventDefault();

    if (!isAuthenticated) {
      setError("Please log in to upload videos");
      navigate("/auth");
      return;
    }

    if (!file || !thumbnail) {
      setError("Please select both video and thumbnail.");
      return;
    }

    const formData = new FormData();
    formData.append("video_title", videoTitle);
    formData.append("video_desc", videoDesc);
    formData.append("img", thumbnail);
    formData.append("file", file);

    try {
      setUploading(true);
      setError("");
      setUploadProgress(0);
      setProcessingProgress(0);
      setCurrentStage("Preparing upload...");

      // Simulate preparation stage
      await new Promise(resolve => setTimeout(resolve, 500));
      setCurrentStage("Uploading video...");

      const response = await uploadClient.post("/upload", formData, {
        headers: {
          "Content-Type": "multipartw/form-data",
          Authorization: `Bearer ${token}`,

        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100);
            setUploadProgress(percent);

            // Update stage based on progress
            if (percent < 20) {
              setCurrentStage("Uploading video...");
            } else if (percent < 80) {
              setCurrentStage("Uploading video...");
            } else if (percent < 100) {
              setCurrentStage("Finalizing upload...");
            }
          }
        },
      });

      if (response.status === 200) {
        setUploadProgress(100);
        setCurrentStage("Processing video...");

        // Simulate processing stages since backend doesn't provide real-time progress
        const processingStages = [
          "Converting to HLS format...",
          "Generating quality variants...",
          "Creating master playlist...",
          "Saving thumbnail...",
          "Finalizing video..."
        ];

        for (let i = 0; i < processingStages.length; i++) {
          setCurrentStage(processingStages[i]);
          setProcessingProgress(Math.round(((i + 1) / processingStages.length) * 100));
          await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
        }

        setCurrentStage("Upload complete!");
        setSuccess(true);

        // Redirect after showing success
        setTimeout(() => {
          if (response.data.redirect_url) {
            navigate(response.data.redirect_url);
          } else {
            navigate("/profile");
          }
        }, 2000);
      }
    } catch (error) {
      console.error("Upload error:", error);
      setError("Upload failed. Please try again.");

      if (error.response) {
        const errorMessage = error.response.data?.error || error.response.data?.message || "Unknown error";
        setError(`Upload failed: ${errorMessage}`);
      } else {
        setError("Upload failed: " + error.message);
      }
    } finally {
      setUploading(false);
      // Don't reset progress immediately to show completion
      setTimeout(() => {
        setUploadProgress(0);
        setProcessingProgress(0);
        setCurrentStage("");
      }, 3000);
    }
  };

  // Show unauthorized if user navigates here manually
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-white text-xl">Please log in to upload videos</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center p-6">
      <div className="bg-gray-900 w-full max-w-lg p-6 rounded-2xl shadow-lg">
        <h1 className="text-white text-2xl font-bold mb-6 text-center">Upload Your Video</h1>

        <form onSubmit={uploadWithProgress} className="flex flex-col gap-4">
          {error && (
            <div className="bg-red-900/20 border border-red-500 text-red-400 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <input
            type="text"
            placeholder="Video Title"
            value={videoTitle}
            onChange={(e) => setVideoTitle(e.target.value)}
            className="bg-gray-800 text-white p-3 rounded-lg outline-none focus:ring-2 focus:ring-purple-500"
            required
            disabled={uploading}
          />
          <textarea
            placeholder="Video Description"
            value={videoDesc}
            onChange={(e) => setVideoDesc(e.target.value)}
            className="bg-gray-800 text-white p-3 rounded-lg outline-none h-24 resize-none focus:ring-2 focus:ring-purple-500"
            disabled={uploading}
          />
          <label className="text-gray-400 text-sm">Thumbnail Image</label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setThumbnail(e.target.files[0])}
            className="text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700"
            required
            disabled={uploading}
          />
          <label className="text-gray-400 text-sm">Video File</label>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setFile(e.target.files[0])}
            className="text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700"
            required
            disabled={uploading}
          />

          <button
            type="submit"
            disabled={uploading}
            className={`${uploading
              ? "bg-purple-800 cursor-not-allowed"
              : "bg-purple-600 hover:bg-purple-700"
              } text-white font-semibold py-3 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:hover:scale-100`}
          >
            {uploading ? "Processing..." : "Upload Video"}
          </button>
        </form>
      </div>

      {/* Enhanced Progress Modal */}
      {uploading && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
        >
          <div className="bg-gray-900 text-white rounded-2xl shadow-xl p-8 w-full max-w-md mx-4">
            <div className="text-center mb-6">
              <div className="w-16 h-16 mx-auto mb-4 bg-purple-600 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <h3 className="text-xl font-bold mb-2">Uploading Video</h3>
              <p className="text-gray-400 text-sm">{currentStage}</p>
            </div>

            {/* Upload Progress */}
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-2">
                <span>Upload Progress</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <motion.div
                  className="bg-purple-500 h-2 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadProgress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </div>

            {/* Processing Progress */}
            {uploadProgress === 100 && (
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-2">
                  <span>Processing Video</span>
                  <span>{processingProgress}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <motion.div
                    className="bg-blue-500 h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${processingProgress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </div>
            )}

            {/* Stage Indicator */}
            <div className="text-center">
              <div className="inline-flex items-center px-3 py-1 rounded-full bg-gray-800 text-sm">
                <div className="w-2 h-2 bg-purple-500 rounded-full mr-2 animate-pulse"></div>
                {currentStage}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Success Dialog */}
      {success && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
        >
          <div className="bg-gray-900 text-center p-8 rounded-2xl shadow-xl max-w-md mx-4">
            <div className="w-16 h-16 mx-auto mb-4 bg-green-600 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-white text-xl font-bold mb-2">🎉 Upload Complete!</h2>
            <p className="text-gray-400 mb-4">Your video has been successfully uploaded and processed.</p>
            <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Redirecting to your profile...</span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
