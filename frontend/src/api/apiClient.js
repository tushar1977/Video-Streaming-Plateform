import axios from "axios"

// Create base API client with common configuration
const apiClient = axios.create({
  baseURL: "https://127.0.0.1:3000", // Use http locally; https only if Flask has SSL
  withCredentials: true,             // ✅ crucial if using cookies
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor: add token to headers automatically
apiClient.interceptors.request.use(
  (config) => {
    config.withCredentials = true

    // Add token to headers if available
    const token = localStorage.getItem("token") // Ensure this key matches where you store JWT
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)

export default apiClient
// Create specialized client for file uploads
export const uploadClient = axios.create({
  baseURL: "https://127.0.0.1:3000", // Flask backend
  withCredentials: true,
  headers: {
    "Content-Type": "multipart/form-data",
  },
})

// Add same interceptors to upload client
uploadClient.interceptors.request.use(
  (config) => {
    config.withCredentials = true

    // Add token to headers if available
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error),
)

uploadClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('isLoggedIn')
      localStorage.removeItem('user')
      localStorage.removeItem('authToken')
      // Don't redirect automatically, let components handle it
    }
    return Promise.reject(error)
  }
)

