import React, { useState } from 'react';
import './App.css';
import ResumeAnalyzer from './components/ResumeAnalyzer';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Resume Analyzer</h1>
        <p>Compare your resume with a job description to receive personalized feedback</p>
      </header>
      <main>
        <ResumeAnalyzer />
      </main>
      <footer>
        <p>© {new Date().getFullYear()} Resume Analyzer</p>
      </footer>
    </div>
  );
}

export default App; 