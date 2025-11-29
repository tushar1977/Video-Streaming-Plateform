"use client"

import { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import { useAuth } from "../Context/AuthContext"
import { uploadClient } from "../api/apiClient"
import io from "socket.io-client"

export default function Upload() {
  const navigate = useNavigate()
  const { isAuthenticated, user, token } = useAuth()
  const [videoTitle, setVideoTitle] = useState("")
  const [videoDesc, setVideoDesc] = useState("")
  const [thumbnail, setThumbnail] = useState(null)
  const [file, setFile] = useState(null)
  const [error, setError] = useState("")
  const [socket, setSocket] = useState(null)
  const [progressCards, setProgressCards] = useState([])
  const socketRef = useRef(null)

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/auth")
    }
  }, [isAuthenticated, navigate])

  // Socket.IO setup - Connect to microservice port (3002)
  useEffect(() => {
    if (!user?.id) return

    // Clean up any existing connection first
    if (socketRef.current) {
      socketRef.current.disconnect()
    }

    const newSocket = io('https://localhost:3000', {
      transports: ['polling'],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      secure: true, // Add this for HTTPS
      rejectUnauthorized: false // Add this for self-signed certificates
    });

    socketRef.current = newSocket
    setSocket(newSocket)

    newSocket.on("connect", () => {
      console.log("[SOCKET] Connected:", newSocket.id)
      newSocket.emit("join", { room: `userId_${user.id}` })
      console.log(`[SOCKET] Joined room: userId_${user.id}`)

    })

    newSocket.on("send_updates", (data) => {
      console.log("[SOCKET] Progress update received:", data)
      console.log("[SOCKET] User ID match:", data.user_id, "===", user?.id)

      if (data.user_id === user?.id) {
        console.log("[SOCKET] Processing update for matching user")
        setProgressCards((prevCards) => {
          const existingIndex = prevCards.findIndex(
            (card) => card.base_name === data.base_name
          )

          const cardData = {
            base_name: data.base_name,
            status: data.status,
            progress: data.progress || 0,
            current_quality: data.current_quality,
            total_qualities: data.total_qualities,
            completed_qualities: data.completed_qualities,
            error: data.error,
            unique_name: data.unique_name,
            message: data.message,
            timestamp: new Date().toISOString(),
          }

          if (existingIndex !== -1) {
            const updated = [...prevCards]
            updated[existingIndex] = cardData
            return updated
          } else {
            return [...prevCards, cardData]
          }
        })
      }
    })

    newSocket.on("disconnect", () => {
      console.log("[SOCKET] Disconnected")
    })

    return () => {
      if (user?.id) {
        newSocket.emit("leave", { room: `userId_${user.id}` })
      }
      newSocket.close()
    }
  }, [user?.id])

  const uploadWithProgress = async (e) => {
    e.preventDefault()

    if (!isAuthenticated) {
      setError("Please log in to upload videos")
      navigate("/auth")
      return
    }

    if (!file || !thumbnail) {
      setError("Please select both video and thumbnail.")
      return
    }

    const formData = new FormData()
    formData.append("video_title", videoTitle)
    formData.append("video_desc", videoDesc)
    formData.append("img", thumbnail)
    formData.append("file", file)

    try {
      setError("")

      const response = await uploadClient.post("/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `Bearer ${token}`,
        },
      })

      if (response.status === 200) {
        // Reset form
        setVideoTitle("")
        setVideoDesc("")
        setThumbnail(null)
        setFile(null)
        // Reset file inputs
        e.target.reset()
      }
    } catch (error) {
      console.error("[UPLOAD ERROR]:", error)

      if (error.response) {
        const errorMessage = error.response.data?.error || error.response.data?.message || "Unknown error"
        setError(`Upload failed: ${errorMessage}`)
      } else {
        setError("Upload failed: " + error.message)
      }
    }
  }

  const removeCard = (baseName) => {
    setProgressCards((prev) => prev.filter((card) => card.base_name !== baseName))
  }

  const getProgressColor = (card) => {
    if (card.error || card.status === "processing_failed" || card.status === "quality_failed") {
      return "bg-red-500"
    }
    if (card.progress === 100 && card.completed_qualities === card.total_qualities) {
      return "bg-green-500"
    }
    return "bg-blue-500"
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-white text-xl">Please log in to upload videos</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center p-6">
      <div className="bg-gray-900 w-full max-w-lg p-6 rounded-2xl shadow-lg">
        <h1 className="text-white text-2xl font-bold mb-6 text-center">Upload Your Video</h1>

        <form onSubmit={uploadWithProgress} className="flex flex-col gap-4">
          {error && (
            <div className="bg-red-900/20 border border-red-500 text-red-400 p-3 rounded-lg text-sm">{error}</div>
          )}

          <input
            type="text"
            placeholder="Video Title"
            value={videoTitle}
            onChange={(e) => setVideoTitle(e.target.value)}
            className="bg-gray-800 text-white p-3 rounded-lg outline-none focus:ring-2 focus:ring-purple-500"
            required
          />
          <textarea
            placeholder="Video Description"
            value={videoDesc}
            onChange={(e) => setVideoDesc(e.target.value)}
            className="bg-gray-800 text-white p-3 rounded-lg outline-none h-24 resize-none focus:ring-2 focus:ring-purple-500"
          />
          <label className="text-gray-400 text-sm">Thumbnail Image</label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setThumbnail(e.target.files[0])}
            className="text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700"
            required
          />
          <label className="text-gray-400 text-sm">Video File</label>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setFile(e.target.files[0])}
            className="text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700"
            required
          />

          <button
            type="submit"
            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 rounded-lg transition-all duration-200 transform hover:scale-105"
          >
            Upload Video
          </button>
        </form>
      </div>

      {/* Processing Progress Cards - Bottom Right */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 w-80">
        <AnimatePresence>
          {progressCards.map((card) => (
            <motion.div
              key={card.base_name}
              initial={{ opacity: 0, x: 100, y: 20 }}
              animate={{ opacity: 1, x: 0, y: 0 }}
              exit={{ opacity: 0, x: 100 }}
              transition={{ type: "spring", stiffness: 200, damping: 25 }}
              className="bg-gray-900 border border-gray-800 rounded-lg shadow-2xl p-3"
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex-1 min-w-0 mr-2">
                  <h4 className="font-medium text-white text-sm truncate">{card.base_name}</h4>
                  <p className="text-xs text-gray-400 truncate">
                    {card.current_quality ? `Processing ${card.current_quality}` : card.message || card.status}
                  </p>
                </div>
                <button
                  onClick={() => removeCard(card.base_name)}
                  className="text-gray-500 hover:text-gray-300 transition-colors text-sm"
                >
                  ✕
                </button>
              </div>

              {/* Progress Bar */}
              <div className="mb-2">
                <div className="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
                  <motion.div
                    className={`${getProgressColor(card)} h-1.5 rounded-full`}
                    initial={{ width: 0 }}
                    animate={{ width: `${card.progress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">
                  {card.completed_qualities && card.total_qualities
                    ? `${card.completed_qualities}/${card.total_qualities} qualities`
                    : "Processing..."}
                </span>
                <span className="text-gray-500 font-medium">{card.progress}%</span>
              </div>

              {/* Error */}
              {card.error && (
                <div className="mt-2 text-xs text-red-400 bg-red-900/20 border border-red-500/30 rounded p-2">
                  {card.error}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
