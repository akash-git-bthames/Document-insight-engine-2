import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import DocumentUpload from './DocumentUpload';
import NLPQuery from './NLPQuery';
import Login from './Login';
import Register from './Register';

const App = () => {
  const [authToken, setAuthToken] = useState(localStorage.getItem('authToken') || '');

  useEffect(() => {
    if (authToken) {
      // Optionally, verify the token with the backend on app load
    }
  }, [authToken]);

  const isAuthenticated = !!authToken;

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={isAuthenticated ? <Navigate to="/upload" /> : <Login setAuthToken={setAuthToken} />}
        />
        <Route
          path="/register"
          element={isAuthenticated ? <Navigate to="/upload" /> : <Register />}
        />
        <Route
          path="/upload"
          element={isAuthenticated ? <DocumentUpload /> : <Navigate to="/" />}
        />
        <Route
          path="/query"
          element={isAuthenticated ? <NLPQuery /> : <Navigate to="/" />}
        />
      </Routes>
    </Router>
  );
};

export default App;