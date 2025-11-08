// components/Loader.jsx
"use client"

import { useLoader } from "./loader"


const Loader = () => {
  const { isLoading, message } = useLoader()

  if (!isLoading) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 flex flex-col items-center space-y-4 min-w-[200px]">
        {/* Spinner */}
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>

        {/* Message */}
        <p className="text-gray-700 font-medium text-center">
          {message}
        </p>
      </div>
    </div>
  )
}

export default Loader
