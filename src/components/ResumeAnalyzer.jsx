import React, { useState, useEffect } from 'react';
import './ResumeAnalyzer.css';

const ResumeAnalyzer = () => {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescFile, setJobDescFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [activeTab, setActiveTab] = useState('analysis');
  const [copied, setCopied] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [loadingStage, setLoadingStage] = useState(0);
  const [loadingProgress, setLoadingProgress] = useState(0);

  useEffect(() => {
    if (results) {
      setAnalysisComplete(true);
      // Scroll to results after a short delay
      const timer = setTimeout(() => {
        document.querySelector('.results')?.scrollIntoView({ 
          behavior: 'smooth',
          block: 'start'
        });
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [results]);

  const handleResumeChange = (e) => {
    const file = e.target.files[0];
    if (file && (file.type === 'application/pdf' || 
                 file.type === 'application/msword' || 
                 file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')) {
      setResumeFile(file);
      setError(null);
    } else {
      setResumeFile(null);
      setError('Please upload a valid PDF or Word document for your resume');
    }
  };

  const handleJobDescChange = (e) => {
    const file = e.target.files[0];
    if (file && (file.type === 'application/pdf' || 
                 file.type === 'application/msword' || 
                 file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')) {
      setJobDescFile(file);
      setError(null);
    } else {
      setJobDescFile(null);
      setError('Please upload a valid PDF or Word document for the job description');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!resumeFile || !jobDescFile) {
      setError('Please upload both a resume and job description');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);
    setAnalysisComplete(false);
    setLoadingStage(0);
    setLoadingProgress(0);

    const formData = new FormData();
    formData.append('resume_file', resumeFile);
    formData.append('job_description_file', jobDescFile);
    
    console.log('Submitting files:', resumeFile, jobDescFile);

    try {
      // Start loading animation
      const simulateProgress = () => {
        // Simulate progress stages
        const stages = [
          { stage: 0, progress: 10, message: "Extracting text from documents..." },
          { stage: 1, progress: 25, message: "Analyzing resume content..." },
          { stage: 2, progress: 40, message: "Comparing with job description..." },
          { stage: 3, progress: 60, message: "Generating tailored recommendations..." },
          { stage: 4, progress: 80, message: "Preparing interview questions..." },
          { stage: 5, progress: 95, message: "Finalizing results..." }
        ];

        let currentStage = 0;
        
        const interval = setInterval(() => {
          if (currentStage < stages.length) {
            setLoadingStage(stages[currentStage].stage);
            setLoadingProgress(stages[currentStage].progress);
            currentStage++;
          } else {
            clearInterval(interval);
          }
        }, 2000); // Change stage every 2 seconds
        
        return interval;
      };

      const progressInterval = simulateProgress();

      console.log('Making API request to: http://localhost:8000/analyze_resume/');
      // Updated API endpoint to match the backend
      const response = await fetch('http://localhost:8000/analyze_resume/', {
        method: 'POST',
        body: formData,
        // Adding proper headers to handle CORS
        headers: {
          // Removing Content-Type header to let the browser set it with the boundary for FormData
          'Accept': 'application/json',
        },
      });

      // Clear the interval once we get a response
      clearInterval(progressInterval);
      setLoadingProgress(100);

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(`Error analyzing resume: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatResumeSuggestions = (suggestions) => {
    if (!suggestions) return null;
    
    // Split the content by section headers (Markdown ## style)
    const sectionRegex = /##\s+([^\n]+)/g;
    const sections = [];
    const sectionMatches = [...suggestions.matchAll(sectionRegex)];
    
    // Process each section
    sectionMatches.forEach((match, index) => {
      const sectionTitle = match[1].trim();
      const startPos = match.index + match[0].length;
      const endPos = (index < sectionMatches.length - 1) 
        ? sectionMatches[index + 1].index 
        : suggestions.length;
      
      const sectionContent = suggestions.substring(startPos, endPos).trim();
      const bulletPoints = extractBulletPoints(sectionContent);
      
      sections.push({
        title: sectionTitle,
        items: bulletPoints
      });
    });
    
    // If no sections found using markdown headers, try the old way
    if (sections.length === 0) {
      return fallbackFormatting(suggestions);
    }
    
    // Render the formatted sections
    return (
      <>
        {sections.map((section, sectionIndex) => (
          <div 
            key={sectionIndex} 
            className="suggestion-section"
            data-section={section.title}
          >
            <h3 className="suggestion-section-title">
              {getIconForSection(section.title)}
              {section.title}
            </h3>
            <div className="suggestion-section-content">
              {section.items.map((item, itemIndex) => {
                if (item.type === 'bullet') {
                  return (
                    <div key={itemIndex} className="suggestion-bullet">
                      <span className="bullet-point">•</span>
                      <span dangerouslySetInnerHTML={{ __html: item.content }}></span>
                    </div>
                  );
                } else if (item.type === 'sub-bullet') {
                  return (
                    <div key={itemIndex} className="suggestion-sub-bullet">
                      <span className="bullet-point">◦</span>
                      <span dangerouslySetInnerHTML={{ __html: item.content }}></span>
                    </div>
                  );
                } else {
                  return <p key={itemIndex} className="suggestion-paragraph" dangerouslySetInnerHTML={{ __html: item.content }}></p>;
                }
              })}
            </div>
          </div>
        ))}
      </>
    );
  };

  // Get icon for section title
  const getIconForSection = (title) => {
    const lowerTitle = title.toLowerCase();
    
    if (lowerTitle.includes('skill')) {
      return <span className="section-icon">💡</span>;
    } else if (lowerTitle.includes('experience')) {
      return <span className="section-icon">📝</span>;
    } else if (lowerTitle.includes('format')) {
      return <span className="section-icon">✨</span>;
    } else if (lowerTitle.includes('resources')) {
      return <span className="section-icon">📚</span>;
    } else if (lowerTitle.includes('action') || lowerTitle.includes('plan')) {
      return <span className="section-icon">🎯</span>;
    } else if (lowerTitle.includes('priority')) {
      return <span className="section-icon">⭐</span>;
    }
    
    return <span className="section-icon">📋</span>;
  };

  // Helper function to extract bullet points from a section
  const extractBulletPoints = (sectionContent) => {
    const lines = sectionContent.split('\n');
    const items = [];
    
    lines.forEach(line => {
      line = line.trim();
      if (!line) return;
      
      // Check if it's a bullet point starting with •, -, or *
      if (line.match(/^[•\-*]\s+/)) {
        // Process line content for skill importance
        let content = line.replace(/^[•\-*]\s+/, '');
        content = highlightSkillImportance(content);
        
        items.push({
          type: 'bullet',
          content
        });
      } 
      // Check if it's an indented sub-bullet
      else if (line.match(/^\s+[•\-*]\s+/)) {
        let content = line.replace(/^\s+[•\-*]\s+/, '');
        content = highlightSkillImportance(content);
        
        items.push({
          type: 'sub-bullet',
          content
        });
      }
      // Plain paragraph text
      else if (line.length > 0) {
        let content = line;
        content = highlightSkillImportance(content);
        
        items.push({
          type: 'paragraph',
          content
        });
      }
    });
    
    return items;
  };

  // Fallback formatting method for non-standardized responses
  const fallbackFormatting = (suggestions) => {
    // Original parsing logic
    const lines = suggestions.split('\n');
    let currentSection = '';
    let sections = [];
    let currentItems = [];
    
    // Process each line
    lines.forEach((line, index) => {
      // Check if this is a new section header (numbered or with a colon)
      const sectionMatch = line.match(/^\d+\.\s+(.*?):|^([A-Z][A-Za-z\s]+):$/);
      
      if (sectionMatch || index === lines.length - 1) {
        // Save previous section if it exists
        if (currentSection && currentItems.length > 0) {
          sections.push({
            title: currentSection,
            items: [...currentItems]
          });
          currentItems = [];
        }
        
        // Start a new section if we matched a header
        if (sectionMatch) {
          currentSection = sectionMatch[1] || sectionMatch[2];
        }
      } 
      // Check if this is a bullet point or a detail under a section
      else if (line.trim()) {
        // Process the content similar to extractBulletPoints
        if (line.trim().match(/^[•\-*]\s+/)) {
          let content = line.trim().replace(/^[•\-*]\s+/, '');
          content = highlightSkillImportance(content);
          
          currentItems.push({
            type: 'bullet',
            content
          });
        } 
        else if (line.trim().match(/^\s+[•\-*]\s+/)) {
          let content = line.trim().replace(/^\s+[•\-*]\s+/, '');
          content = highlightSkillImportance(content);
          
          currentItems.push({
            type: 'sub-bullet',
            content
          });
        }
        else if (line.trim().length > 0) {
          let content = line.trim();
          content = highlightSkillImportance(content);
          
          currentItems.push({
            type: 'paragraph',
            content
          });
        }
      }
    });
    
    // Add the last section if needed
    if (currentSection && currentItems.length > 0) {
      sections.push({
        title: currentSection,
        items: [...currentItems]
      });
    }
    
    // If no clear sections were found, treat the whole content as general recommendations
    if (sections.length === 0 && lines.filter(line => line.trim()).length > 0) {
      const items = lines
        .filter(line => line.trim())
        .map(line => {
          if (line.trim().match(/^[•\-*]\s+/)) {
            let content = line.trim().replace(/^[•\-*]\s+/, '');
            content = highlightSkillImportance(content);
            
            return {
              type: 'bullet',
              content
            };
          } else {
            let content = line.trim();
            content = highlightSkillImportance(content);
            
            return {
              type: 'paragraph',
              content
            };
          }
        });
      
      sections.push({
        title: 'Recommendations',
        items
      });
    }
    
    // Format the same way as the primary formatter
    return (
      <>
        {sections.map((section, sectionIndex) => (
          <div 
            key={sectionIndex} 
            className="suggestion-section"
            data-section={section.title}
          >
            <h3 className="suggestion-section-title">
              {getIconForSection(section.title)}
              {section.title}
            </h3>
            <div className="suggestion-section-content">
              {section.items.map((item, itemIndex) => {
                if (item.type === 'bullet') {
                  return (
                    <div key={itemIndex} className="suggestion-bullet">
                      <span className="bullet-point">•</span>
                      <span dangerouslySetInnerHTML={{ __html: item.content }}></span>
                    </div>
                  );
                } else if (item.type === 'sub-bullet') {
                  return (
                    <div key={itemIndex} className="suggestion-sub-bullet">
                      <span className="bullet-point">◦</span>
                      <span dangerouslySetInnerHTML={{ __html: item.content }}></span>
                    </div>
                  );
                } else {
                  return <p key={itemIndex} className="suggestion-paragraph" dangerouslySetInnerHTML={{ __html: item.content }}></p>;
                }
              })}
            </div>
          </div>
        ))}
      </>
    );
  };

  // Function to highlight skill importance levels and other formatting enhancements
  const highlightSkillImportance = (text) => {
    if (!text) return '';
    
    // First, handle skill importance levels with (High), (Medium), (Low) format
    let formattedText = text.replace(/\((High|Medium|Low)\)/gi, (match, priority) => {
      const lowerPriority = priority.toLowerCase();
      return `<span class="skill-importance-${lowerPriority}">${priority} Priority</span>`;
    });
    
    // Next, highlight skill names in "Skill Name: " format (common in skill gaps section)
    formattedText = formattedText.replace(/^([^:]+):\s/i, (match, skillName) => {
      return `<strong class="skill-name">${skillName}</strong>: `;
    });
    
    // Highlight course/resource names in "For X: [Resource]" format
    formattedText = formattedText.replace(/For\s+.+?:\s+([^-]+)\s+-/i, (match, resource, offset) => {
      if (offset === 0 || formattedText[offset-1] === '\n') {
        return match.replace(resource, `<em class="resource-name">${resource.trim()}</em>`);
      }
      return match;
    });
    
    // Create links for any URLs
    formattedText = formattedText.replace(
      /(https?:\/\/[^\s,]+)/g,
      '<a href="$1" target="_blank" rel="noopener noreferrer" class="recommendation-link">$1</a>'
    );
    
    return formattedText;
  };

  // Function to handle copy to clipboard
  const handleCopy = (text, type) => {
    navigator.clipboard.writeText(text);
    setCopied(type);
    setTimeout(() => setCopied(false), 2000);
  };

  // Format scores to display as a percentage
  const formatScore = (score) => {
    return Math.round((score / 10) * 100);
  };

  // Loading stages messages
  const loadingMessages = [
    "Extracting text from documents...",
    "Analyzing resume content...",
    "Comparing with job description...",
    "Generating tailored recommendations...",
    "Preparing interview questions...",
    "Finalizing results..."
  ];

  // Add click handler for the entire file upload area
  const handleFileUploadClick = (inputId) => {
    document.getElementById(inputId).click();
  };

  // Add function to truncate filename for display
  const formatFileName = (fileName) => {
    if (!fileName) return "";
    
    // Keep full name in tooltip, but truncate display if needed
    if (fileName.length > 25) {
      const extension = fileName.split('.').pop();
      const nameWithoutExt = fileName.substring(0, fileName.lastIndexOf('.'));
      const truncatedName = nameWithoutExt.substring(0, 20) + '...';
      return `${truncatedName}.${extension}`;
    }
    
    return fileName;
  };

  return (
    <div className="resume-analyzer">
      <form onSubmit={handleSubmit} className={analysisComplete ? 'form-minimized' : ''}>
        <div className="upload-section">
          <div 
            className={`file-upload ${resumeFile ? 'file-selected' : ''}`}
            onClick={() => handleFileUploadClick('resume')}
          >
            <h3>{analysisComplete ? 'Resume' : 'Upload Your Resume'}</h3>
            <div className="upload-icon">📄</div>
            <input 
              type="file" 
              id="resume" 
              onChange={handleResumeChange}
              accept=".pdf,.doc,.docx"
              aria-label="Upload resume file"
            />
            <div className="file-name-container" aria-live="polite">
              {resumeFile ? (
                <p className="file-name" title={resumeFile.name}>
                  {formatFileName(resumeFile.name)}
                </p>
              ) : (
                <p className="file-placeholder">No file selected</p>
              )}
            </div>
            <label htmlFor="resume" className="file-label" onClick={(e) => e.stopPropagation()}>
              {resumeFile ? 'Change File' : 'Choose File'}
            </label>
          </div>

          <div 
            className={`file-upload ${jobDescFile ? 'file-selected' : ''}`}
            onClick={() => handleFileUploadClick('jobDesc')}
          >
            <h3>{analysisComplete ? 'Job Description' : 'Upload Job Description'}</h3>
            <div className="upload-icon">📋</div>
            <input 
              type="file" 
              id="jobDesc" 
              onChange={handleJobDescChange}
              accept=".pdf,.doc,.docx"
              aria-label="Upload job description file"
            />
            <div className="file-name-container" aria-live="polite">
              {jobDescFile ? (
                <p className="file-name" title={jobDescFile.name}>
                  {formatFileName(jobDescFile.name)}
                </p>
              ) : (
                <p className="file-placeholder">No file selected</p>
              )}
            </div>
            <label htmlFor="jobDesc" className="file-label" onClick={(e) => e.stopPropagation()}>
              {jobDescFile ? 'Change File' : 'Choose File'}
            </label>
          </div>
          
          {analysisComplete && (
            <button 
              type="submit" 
              className="analyze-button"
              disabled={loading || !resumeFile || !jobDescFile}
            >
              {loading ? 'Analyzing...' : 'Re-Analyze'}
            </button>
          )}
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span> {error}
          </div>
        )}

        {!analysisComplete && (
          <button 
            type="submit" 
            className="analyze-button"
            disabled={loading || !resumeFile || !jobDescFile}
          >
            {loading ? 'Analyzing Resume...' : 'Analyze My Resume'}
          </button>
        )}
      </form>

      {loading && (
        <div className="loading">
          <div className="progress-container">
            <div 
              className="progress-bar-animated" 
              style={{width: `${loadingProgress}%`}}
            ></div>
          </div>
          <div className="spinner"></div>
          <p className="loading-message">{loadingMessages[loadingStage]}</p>
          <p className="loading-tip">This may take 15-30 seconds</p>
          <div className="loading-stages">
            {loadingMessages.map((message, index) => (
              <div 
                key={index} 
                className={`loading-stage ${index <= loadingStage ? 'active' : ''}`}
              >
                <span className="stage-dot"></span>
                <span className="stage-label">{index + 1}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {results && (
        <div className="results">
          <div className="tabs">
            <button 
              className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
              onClick={() => setActiveTab('analysis')}
            >
              <span className="tab-icon">📊</span> Analysis
            </button>
            <button 
              className={`tab ${activeTab === 'cover-letter' ? 'active' : ''}`}
              onClick={() => setActiveTab('cover-letter')}
            >
              <span className="tab-icon">📝</span> Cover Letter
            </button>
            <button 
              className={`tab ${activeTab === 'resume-suggestions' ? 'active' : ''}`}
              onClick={() => setActiveTab('resume-suggestions')}
            >
              <span className="tab-icon">🔍</span> Resume Suggestions
            </button>
            <button 
              className={`tab ${activeTab === 'skill-development' ? 'active' : ''}`}
              onClick={() => setActiveTab('skill-development')}
            >
              <span className="tab-icon">📈</span> Skill Development
            </button>
            <button 
              className={`tab ${activeTab === 'interview-questions' ? 'active' : ''}`}
              onClick={() => setActiveTab('interview-questions')}
              aria-label="Interview Prep"
            >
              <span className="tab-icon">💬</span> Interview Prep
            </button>
          </div>

          <div className="tab-content">
            {activeTab === 'analysis' && (
              <div className="analysis">
                <h2><span className="section-icon">📊</span> Resume Analysis</h2>
                
                <div className="score-overview">
                  {results.scores_and_feedback && Object.entries(results.scores_and_feedback).map(([category, data]) => (
                    <div key={category} className="score-card">
                      <h3>{category}</h3>
                      <div className="score-value">{data.score}/10</div>
                      <div className="progress-bar">
                        <div 
                          className="progress" 
                          style={{width: `${formatScore(data.score)}%`}}
                        ></div>
                      </div>
                      <div className="feedback">{data.feedback}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'cover-letter' && (
              <div className="cover-letter">
                <h2><span className="section-icon">📝</span> Generated Cover Letter</h2>
                <div className="cover-letter-content">
                  {results.cover_letter}
                </div>
                <button 
                  className="copy-button"
                  onClick={() => handleCopy(results.cover_letter, 'cover-letter')}
                >
                  {copied === 'cover-letter' ? '✓ Copied!' : 'Copy to Clipboard'}
                </button>
              </div>
            )}

            {activeTab === 'resume-suggestions' && (
              <div className="resume-suggestions">
                <h2><span className="section-icon">🔍</span> Resume Improvement Suggestions</h2>
                <div className="resume-suggestions-content">
                  {formatResumeSuggestions(results.ideal_resume)}
                </div>
                <button 
                  className="copy-button"
                  onClick={() => handleCopy(results.ideal_resume, 'resume-suggestions')}
                >
                  {copied === 'resume-suggestions' ? '✓ Copied!' : 'Copy to Clipboard'}
                </button>
              </div>
            )}

            {activeTab === 'skill-development' && (
              <div className="skill-development">
                <h2><span className="section-icon">📈</span> Skill Development Plan</h2>
                <div className="skill-development-content">
                  {formatResumeSuggestions(results.skill_development)}
                </div>
                <button 
                  className="copy-button"
                  onClick={() => handleCopy(results.skill_development, 'skill-development')}
                >
                  {copied === 'skill-development' ? '✓ Copied!' : 'Copy to Clipboard'}
                </button>
              </div>
            )}

            {activeTab === 'interview-questions' && (
              <div className="interview-questions">
                <h2><span className="section-icon">💬</span> Interview Questions & Answers</h2>
                <div className="interview-questions-content">
                  {formatResumeSuggestions(results.interview_questions)}
                </div>
                <button 
                  className="copy-button"
                  onClick={() => handleCopy(results.interview_questions, 'interview-questions')}
                >
                  {copied === 'interview-questions' ? '✓ Copied!' : 'Copy to Clipboard'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeAnalyzer; 