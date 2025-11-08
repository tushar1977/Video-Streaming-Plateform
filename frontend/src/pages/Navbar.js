"use client"

import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../Context/AuthContext";

export default function Navbar() {
  const { isAuthenticated, user, logout, loading } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  // Toggle mobile menu
  const toggleMenu = () => setIsOpen((prev) => !prev);

  // Logout
  const handleLogout = () => {
    logout();
    setIsOpen(false);
  };

  // Close menu when navigating
  useEffect(() => setIsOpen(false), [location.pathname]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (isOpen && !e.target.closest("nav")) setIsOpen(false);
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [isOpen]);

  // Prevent background scroll on mobile
  useEffect(() => {
    document.body.style.overflow = isOpen ? "hidden" : "unset";
    return () => (document.body.style.overflow = "unset");
  }, [isOpen]);

  // Loading State
  if (loading) {
    return (
      <nav className="bg-slate-900 shadow-lg border-b border-slate-800">
        <div className="mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="text-lg font-bold text-white">
              <Link to="/">
                <span className="text-white">STREAM</span>
                <span className="text-blue-500">X</span>
              </Link>
            </div>
            <div className="text-gray-400 text-sm flex items-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-500"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 
                  5.291A7.962 7.962 0 014 12H0c0 
                  3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Loading...
            </div>
          </div>
        </div>
      </nav>
    );
  }

  return (
    <nav className="bg-slate-900 shadow-lg border-b h-16 border-slate-800 relative z-50">
      <div className="mx-auto h-full px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-full">
          {/* Logo */}
          <div className="text-lg font-bold text-white">
            <Link
              to="/"
              className="hover:opacity-90 transition-opacity flex items-center"
              onClick={() => setIsOpen(false)}
            >
              <span className="text-white">STREAM</span>
              <span className="text-blue-500">X</span>
            </Link>
          </div>

          {/* Desktop Menu */}
          <div className="hidden sm:flex space-x-6 text-gray-100 items-center">
            {isAuthenticated ? (
              <>
                <Link
                  to="/"
                  className="hover:text-blue-500 transition-colors font-medium"
                >
                  Home
                </Link>
                <Link
                  to="/profile"
                  className="hover:text-blue-500 transition-colors font-medium"
                >
                  Profile
                </Link>
                <Link
                  to="/upload"
                  className="hover:text-blue-500 transition-colors font-medium"
                >
                  Upload
                </Link>
                <span
                  className="text-sm text-gray-300 ml-2 max-w-32 truncate"
                  title={`Welcome, ${user?.name || user?.email || "User"}`}
                >
                  Welcome, {user?.name || user?.email || "User"}
                </span>
                <button
                  onClick={handleLogout}
                  className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link
                to="/auth"
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors font-medium"
              >
                Login / Sign Up
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="sm:hidden">
            <button
              onClick={toggleMenu}
              className="text-gray-300 hover:text-white focus:outline-none text-2xl transition-transform duration-200"
              aria-label="Toggle menu"
              aria-expanded={isOpen}
            >
              {isOpen ? "✖" : "☰"}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="sm:hidden fixed inset-0 bg-black bg-opacity-50 z-40 top-16"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Mobile Dropdown */}
      {isOpen && (
        <div className="sm:hidden fixed top-16 left-0 right-0 bg-slate-900 shadow-lg z-50 border-t border-slate-800 max-h-[calc(100vh-4rem)] overflow-y-auto">
          <div className="flex flex-col text-gray-300">
            {isAuthenticated ? (
              <>
                <Link
                  to="/"
                  className="hover:text-blue-500 transition-colors py-4 px-6 border-b border-slate-800 font-medium"
                  onClick={() => setIsOpen(false)}
                >
                  Home
                </Link>
                <Link
                  to="/profile"
                  className="hover:text-blue-500 transition-colors py-4 px-6 border-b border-slate-800 font-medium"
                  onClick={() => setIsOpen(false)}
                >
                  Profile
                </Link>
                <Link
                  to="/upload"
                  className="hover:text-blue-500 transition-colors py-4 px-6 border-b border-slate-800 font-medium"
                  onClick={() => setIsOpen(false)}
                >
                  Upload
                </Link>

                <div className="py-3 px-6 border-b border-slate-800 bg-slate-800">
                  <div className="text-sm text-gray-300 font-medium">
                    Welcome, {user?.name || user?.email || "User"}
                  </div>
                </div>

                <div className="p-4 border-b border-slate-800">
                  <button
                    onClick={handleLogout}
                    className="w-full bg-slate-800 hover:bg-slate-700 text-white px-4 py-3 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                  >
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <div className="p-4 border-b border-slate-800">
                <Link
                  to="/auth"
                  className="block w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-lg transition-colors text-center font-medium"
                  onClick={() => setIsOpen(false)}
                >
                  Login / Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
