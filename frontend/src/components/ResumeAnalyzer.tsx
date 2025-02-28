import React, { useState } from "react";
import axios from "axios";
import FileUpload from "./FileUpload";

const ResumeAnalyzer: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [feedback, setFeedback] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const analyzeResume = async () => {
    if (!file) {
      alert("Please upload a resume.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    try {
      const response = await axios.post("http://127.0.0.1:8000/analyze_resume/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setFeedback(response.data.feedback);
    } catch (error) {
      console.error("Error analyzing resume:", error);
      alert("Failed to analyze resume.");
    }
    setLoading(false);
  };

  return (
    <div className="container">
      <h2>Upload Your Resume</h2>
      <FileUpload onFileSelect={setFile} />
      <button onClick={analyzeResume} disabled={loading}>
        {loading ? "Analyzing..." : "Analyze Resume"}
      </button>
      {feedback && (
        <div className="feedback-box">
          <h3>AI Feedback:</h3>
          <p>{feedback}</p>
        </div>
      )}
    </div>
  );
};

export default ResumeAnalyzer;
