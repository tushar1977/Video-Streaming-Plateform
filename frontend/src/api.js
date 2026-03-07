const API_BASE_URL = process.env.REACT_APP_baseURL;

export const AUTH_ENDPOINTS = {
  login: `${API_BASE_URL}/auth/login`,
  signup: `${API_BASE_URL}/auth/signup`,
  logout: `${API_BASE_URL}/auth/logout`,
  current_user: `${API_BASE_URL}/auth/current_user`
};
