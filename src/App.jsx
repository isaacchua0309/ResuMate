import React, { useState, useEffect } from 'react';
import './App.css';
import ResumeAnalyzer from './components/ResumeAnalyzer';
import Modal from './components/Modal';

// Modal content components
const AboutContent = () => (
  <>
    <div className="modal-section">
      <h3 className="modal-section-title">About ResuMate AI</h3>
      <p>
        ResuMate AI is an intelligent resume optimization platform designed to help job seekers tailor their resumes to specific job descriptions using advanced AI technology.
      </p>
      <p>
        Our mission is to empower job seekers by providing actionable insights and personalized recommendations that increase their chances of landing interviews and ultimately securing their dream jobs.
      </p>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">How It Works</h3>
      <p>ResuMate AI analyzes your resume against specific job descriptions using advanced natural language processing and machine learning techniques to provide:</p>
      <ul>
        <li><strong>Comprehensive Analysis</strong> - Evaluation of your resume's skills match, impact statements, brevity, and overall style with personalized feedback</li>
        <li><strong>Resume Improvement Suggestions</strong> - Actionable recommendations for skills to highlight, skills to add, experience improvements, and formatting enhancements</li>
        <li><strong>Skill Development Plans</strong> - Personalized skill development strategies including priority skills to develop, relevant learning resources, and a structured action plan</li>
        <li><strong>Custom Cover Letters</strong> - Tailored cover letters that highlight your most relevant qualifications for the specific position</li>
      </ul>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">Our Technology</h3>
      <p>
        ResuMate AI is powered by state-of-the-art language models that analyze the semantic meaning of your resume and job descriptions, going beyond simple keyword matching to understand context, relevance, and industry-specific terminology.
      </p>
      <p>
        We use structured data analysis to ensure consistent, actionable feedback in every analysis, helping you make targeted improvements that matter to hiring managers.
      </p>
    </div>
  </>
);

const PrivacyPolicyContent = () => (
  <>
    <div className="modal-section">
      <h3 className="modal-section-title">Privacy Policy</h3>
      <p>Last Updated: {new Date().toLocaleDateString()}</p>
      <p>
        At ResuMate AI, we take your privacy seriously. This Privacy Policy explains how we collect, use, and protect your personal information when you use our resume analysis service.
      </p>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">Information We Collect</h3>
      <p>When you use ResuMate AI, we collect the following types of information:</p>
      <ul>
        <li><strong>Resume Data</strong> - The content of your resume that you upload for analysis, which may include personal identifiers, work history, education details, and skills</li>
        <li><strong>Job Description Data</strong> - The job descriptions you upload for comparison against your resume</li>
        <li><strong>Usage Data</strong> - Information about how you interact with our application, including features used and analysis results</li>
      </ul>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">How We Use Your Information</h3>
      <p>We use your information solely for the following purposes:</p>
      <ul>
        <li>To provide our resume analysis service and generate personalized recommendations</li>
        <li>To improve and enhance our AI algorithms and analysis capabilities</li>
        <li>To troubleshoot issues and optimize the performance of our application</li>
      </ul>
      <p>
        <strong>Important Note:</strong> Your resume and job description data are processed in real-time and are not permanently stored on our servers after analysis is complete. The analysis is performed within your current session only.
      </p>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">Data Security</h3>
      <p>
        We implement appropriate technical and organizational measures to protect your personal information against unauthorized access, accidental loss, or damage. Our services use secure HTTPS connections, and we regularly review our security practices.
      </p>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">Third-Party Services</h3>
      <p>
        ResuMate AI uses OpenAI's API for natural language processing capabilities. Any data processed through OpenAI's services is subject to their privacy policy. We only share the minimum necessary information required to perform the analysis.
      </p>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">Your Rights</h3>
      <p>You have the right to:</p>
      <ul>
        <li>Access the personal information we hold about you</li>
        <li>Request correction of inaccurate personal information</li>
        <li>Request deletion of your personal information</li>
        <li>Object to processing of your personal information</li>
        <li>Request restriction of processing your personal information</li>
      </ul>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">Contact Us</h3>
      <p>
        If you have any questions or concerns about this Privacy Policy or our data practices, please contact us at privacy@resumate.ai.
      </p>
    </div>
  </>
);

const TermsOfServiceContent = () => (
  <>
    <div className="modal-section">
      <h3 className="modal-section-title">Terms of Service</h3>
      <p>Last Updated: {new Date().toLocaleDateString()}</p>
      <p>
        Welcome to ResuMate AI. By accessing or using our services, you agree to be bound by these Terms of Service. Please read them carefully.
      </p>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">Service Description</h3>
      <p>
        ResuMate AI provides an AI-powered resume analysis service that compares user-provided resumes against job descriptions to generate personalized feedback, suggestions, and optimizations ("the Service").
      </p>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">User Responsibilities</h3>
      <p>As a user of ResuMate AI, you agree to:</p>
      <ul>
        <li>Provide accurate and truthful information in your resume</li>
        <li>Upload only your own resume or resumes you have permission to use</li>
        <li>Use the Service for legitimate job application purposes</li>
        <li>Not attempt to manipulate, reverse-engineer, or exploit the Service</li>
        <li>Not use the Service for any illegal or unauthorized purpose</li>
      </ul>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">Intellectual Property</h3>
      <p>
        The content, features, and functionality of the ResuMate AI Service, including but not limited to text, graphics, logos, and software, are owned by ResuMate AI and are protected by copyright, trademark, and other intellectual property laws.
      </p>
      <p>
        You retain all rights to your resume and job description content. By uploading this content, you grant us a limited license to use it solely for the purpose of providing the Service to you.
      </p>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">No Guarantees</h3>
      <p>
        While we strive to provide accurate and helpful analysis, ResuMate AI does not guarantee that using our Service will result in job interviews or offers. The effectiveness of our suggestions may vary based on many factors outside our control, including employer preferences and job market conditions.
      </p>
      <p>
        The analysis and suggestions provided are generated by AI technology and should be reviewed and used at your discretion. We recommend using our Service as a complementary tool alongside other job search strategies.
      </p>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">Limitation of Liability</h3>
      <p>
        To the maximum extent permitted by law, ResuMate AI shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use or inability to use the Service.
      </p>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">Modifications to Terms</h3>
      <p>
        We reserve the right to modify these Terms of Service at any time. Continued use of the Service after any such changes constitutes your acceptance of the new Terms of Service.
      </p>
    </div>

    <div className="modal-section">
      <h3 className="modal-section-title">Governing Law</h3>
      <p>
        These Terms shall be governed by and construed in accordance with the laws of the jurisdiction in which ResuMate AI operates, without regard to its conflict of law provisions.
      </p>
    </div>
  </>
);

function App() {
  const [modalContent, setModalContent] = useState(null);
  const [darkMode, setDarkMode] = useState(() => {
    // Check if user has a saved preference
    const savedTheme = localStorage.getItem('theme');
    // Check if user prefers dark mode at system level
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    return savedTheme === 'dark' || (!savedTheme && prefersDark);
  });

  // Apply theme when darkMode state changes
  useEffect(() => {
    if (darkMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  const toggleTheme = () => {
    setDarkMode(!darkMode);
  };

  const openModal = (content) => {
    setModalContent(content);
  };

  const closeModal = () => {
    setModalContent(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="theme-toggle-container">
          <button 
            className="theme-toggle" 
            onClick={toggleTheme}
            aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
          >
            {darkMode ? (
              <span className="theme-icon">☀️</span>
            ) : (
              <span className="theme-icon">🌙</span>
            )}
          </button>
        </div>
        <div className="header-content">
          <h1>ResuMate <span className="logo-accent">AI</span></h1>
          <p>Analyze your resume against job descriptions with advanced AI to get personalized insights, suggestions, and skill development plans</p>
        </div>
      </header>
      <main>
        <ResumeAnalyzer />
      </main>
      <footer>
        <div className="footer-content">
          <div className="footer-info">
            <p>© {new Date().getFullYear()} ResuMate AI - Your intelligent resume optimization companion</p>
            <p className="footer-tagline">Powered by advanced AI to help you land your dream job</p>
          </div>
          <div className="footer-links">
            <button 
              className="footer-link" 
              onClick={() => openModal({ title: 'About ResuMate AI', content: <AboutContent /> })}
            >
              About
            </button>
            <button 
              className="footer-link" 
              onClick={() => openModal({ title: 'Privacy Policy', content: <PrivacyPolicyContent /> })}
            >
              Privacy Policy
            </button>
            <button 
              className="footer-link" 
              onClick={() => openModal({ title: 'Terms of Service', content: <TermsOfServiceContent /> })}
            >
              Terms of Service
            </button>
          </div>
        </div>
      </footer>

      {modalContent && (
        <Modal
          isOpen={!!modalContent}
          onClose={closeModal}
          title={modalContent.title}
        >
          {modalContent.content}
        </Modal>
      )}
    </div>
  );
}

export default App; 