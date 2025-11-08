"use client"

import { useState } from "react"
import { Eye, EyeOff, PlayCircle } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../Context/AuthContext"
import { useLoader } from "../loader/loader"
import { useErrorDialog } from "../errorDialog/ErrorDialogContext"

export default function AuthForm() {
  const [isSignUp, setIsSignUp] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [name, setName] = useState("")
  const { showLoader, hideLoader } = useLoader();
  const [isLoading, setIsLoading] = useState(false)
  const { showError } = useErrorDialog()
  const { login, signup, isLoggedIn, loading } = useAuth()
  const navigate = useNavigate()
  if (loading) {
    // Optionally render a spinner or nothing while the check is running
    return <div>Loading authentication status...</div> // Or a proper spinner component
  }
  // Redirect if already logged in
  if (isLoggedIn) {
    navigate("/")
    return null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    showLoader(isSignUp ? "Creating your account..." : "Signing you in...");

    try {
      let result

      if (isSignUp) {
        result = await signup(email, password, name || email.split("@")[0])
      } else {
        result = await login(email, password)
      }

      if (result.success) {
        console.log("✅ Auth success:", result.user)


        navigate("/")
      } else {

        showError({
          title: "Authentication Failed",
          message: "Email or password is invalid",
        })
        hideLoader();
      }
    } catch (error) {
      showError({
        title: "Something Went Wrong",
        message: "Something went wrong. Please try again.",
      })
    } finally {

      hideLoader();
    }
  }

  return (
    <div className="min-h-screen flex bg-gray-50">
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-black via-slate-900 to-blue-900 flex-col justify-between p-12 relative overflow-hidden">
        {/* Background overlay / blur */}
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1525186402429-b4ff38bedbec?auto=format&fit=crop&w=1500&q=80')] bg-cover bg-center opacity-20"></div>

        {/* Top Logo */}
        <div className="text-white relative z-10">
          <h1 className="text-2xl font-bold italic tracking-wide">
            STREAM<span className="text-blue-500">X</span>
          </h1>
        </div>

        {/* Center Text */}
        <div className="space-y-6 relative z-10">
          <PlayCircle size={64} className="text-blue-400 drop-shadow-md" />
          <h2 className="text-5xl font-bold text-white leading-tight">
            Stream. Upload. <br /> Inspire the world.
          </h2>
        </div>

        {/* Bottom Footer */}
        <div className="text-gray-400 text-sm relative z-10">
          © 2025 StreamX. All rights reserved.
        </div>
      </div>

      {/* 🔐 Right Auth Section */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6">
        <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">
            {isSignUp ? "Create your account" : "Welcome back"}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name field for signup */}
            {isSignUp && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  className="w-full px-4 py-3 border-2 border-blue-100 rounded-lg focus:outline-none focus:border-blue-500"
                />
              </div>
            )}

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                className="w-full px-4 py-3 border-2 border-blue-100 rounded-lg focus:outline-none focus:border-blue-500"
                required
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 pr-12"
                  required
                  minLength={6}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 rounded-lg transition-colors flex justify-center items-center"
            >
              {isLoading ? (
                <div className="flex items-center">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  {isSignUp ? "Creating account..." : "Signing in..."}
                </div>
              ) : (
                isSignUp ? "Create account" : "Sign in"
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center">
            <div className="flex-1 border-t border-gray-300" />
            <span className="px-3 text-sm text-gray-500">or</span>
            <div className="flex-1 border-t border-gray-300" />
          </div>

          {/* Toggle */}
          <p className="text-center text-sm text-gray-600 mt-6">
            {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
            <button
              type="button"
              onClick={() => {
                setIsSignUp(!isSignUp)
                setEmail("")
                setPassword("")
                setName("")
              }}
              className="text-blue-500 hover:text-blue-600 font-medium"
              disabled={isLoading}
            >
              {isSignUp ? "Log in" : "Sign up"}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
