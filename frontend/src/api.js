const API_BASE_URL = 'https://192.168.1.132:3000';

export const AUTH_ENDPOINTS = {
  login: `${API_BASE_URL}/auth/login`,
  signup: `${API_BASE_URL}/auth/signup`,
  logout: `${API_BASE_URL}/auth/logout`,
  current_user: `${API_BASE_URL}/auth/current_user`
};
