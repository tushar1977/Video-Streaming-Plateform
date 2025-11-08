import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Upload from './pages/Upload';
import './App.css';
import AuthForm from './pages/Auth';
import Navbar from './pages/Navbar';
import { LoaderProvider } from './loader/loader';
import Loader from './loader/Loader';
import { AuthProvider } from './Context/AuthContext';
import ErrorDialog from './errorDialog/ErrorDialog';
import { ErrorDialogProvider } from './errorDialog/ErrorDialogContext';
import VideoPlayer from './pages/Watch';
function App() {
  return (
    <ErrorDialogProvider>
      <LoaderProvider>
        <Router>
          <AuthProvider>
            <div className="App">
              <Loader />
              <ErrorDialog />
              <Navbar />
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/Auth" element={<AuthForm />} />
                <Route path="/watch/:uniqueName" element={<VideoPlayer />} />
                <Route path="/upload" element={<Upload />} />
              </Routes>
            </div>
          </AuthProvider>
        </Router>
      </LoaderProvider>
    </ErrorDialogProvider>
  );
}

export default App;
