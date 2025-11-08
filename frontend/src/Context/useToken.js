import { useState, useEffect } from "react";

function useToken() {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("token"));

  // Save token to localStorage
  function saveToken(userToken) {
    localStorage.setItem("token", userToken);
    setToken(userToken);
    setIsAuthenticated(true);
  }

  // Remove token
  function removeToken() {
    localStorage.removeItem("token");
    setToken(null);
    setIsAuthenticated(false);
  }

  // Sync across tabs
  useEffect(() => {
    const sync = () => {
      const storedToken = localStorage.getItem("token");
      setToken(storedToken);
      setIsAuthenticated(!!storedToken);
    };

    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);

  return { token, setToken: saveToken, removeToken, isAuthenticated };
}

export default useToken;
