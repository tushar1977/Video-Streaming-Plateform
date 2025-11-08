"use client"

import { useState, useEffect } from "react"
import { ThumbsUp, ThumbsDown } from "lucide-react"
import { io } from "socket.io-client"
import { useAuth } from "../Context/AuthContext"
import { useNavigate } from "react-router-dom"
import apiClient from "../api/apiClient"

export default function LikeDislikeButton({
  videoId,
  initialLikeCount,
  initialDislikeCount,
  initialUserLiked,
  initialUserDisliked,
  onLikeChange,
}) {
  const [likeCount, setLikeCount] = useState(initialLikeCount)

  const navigate = useNavigate();
  const [dislikeCount, setDislikeCount] = useState(initialDislikeCount)
  const [userLiked, setUserLiked] = useState(initialUserLiked)
  const [userDisliked, setUserDisliked] = useState(initialUserDisliked)
  const [likeAnimating, setLikeAnimating] = useState(false)
  const [dislikeAnimating, setDislikeAnimating] = useState(false)
  const { isAuthenticated, user, token } = useAuth();
  const [error, setError] = useState("");

  useEffect(() => {
    // Connect to Flask-SocketIO
    const socket = io("https://127.0.0.1:3000", {
      transports: ["websocket"],
      secure: true,
      reconnection: true,
      withCredentials: true,
      reconnectionAttempts: 5,
    })

    // Join a specific video "room" for updates
    socket.emit("join", { room: `video_${videoId}` })

    // Listen for updates from Flask backend
    socket.on("like_update", (data) => {
      if (data.video_id === videoId) {
        setLikeCount(data.like_count)
        setDislikeCount(data.dislike_count)
        setUserLiked(data.user_has_liked)
        setUserDisliked(data.user_has_disliked)
      }
    })

    socket.on("connect", () => {
      console.log("Connected to Socket.IO server")
    })

    socket.on("disconnect", () => {
      console.warn("Disconnected from Socket.IO server")
    })

    return () => {
      socket.emit("leave", { room: `video_${videoId}` })
      socket.disconnect()
    }
  }, [videoId])

  const handleLike = async () => {
    try {

      if (!isAuthenticated) {
        setError("Please log in to upload videos");
        navigate("/auth");
        return;
      }
      setLikeAnimating(true)
      const res = await apiClient.post(`/like_action/like/${videoId}`)
      const data = res.data
      setUserLiked(data.user_has_liked)
      setLikeCount(data.like_count)
      setUserDisliked(false)
      setDislikeCount(data.dislike_count || dislikeCount)
      onLikeChange?.(data.like_count, data.dislike_count || dislikeCount, data.user_has_liked, false)
      setTimeout(() => setLikeAnimating(false), 600)
    } catch (err) {
      console.error("Error liking video:", err)
      setLikeAnimating(false)
    }
  }

  const handleDislike = async () => {
    try {

      if (!isAuthenticated) {
        setError("Please log in to upload videos");
        navigate("/auth");
        return;
      }
      setDislikeAnimating(true)

      const res = await apiClient.post(`/like_action/dislike/${videoId}`)
      const data = res.data
      setUserDisliked(data.user_has_disliked)
      setDislikeCount(data.dislike_count)
      setUserLiked(false)
      setLikeCount(data.like_count || likeCount)
      onLikeChange?.(data.like_count || likeCount, data.dislike_count, false, data.user_has_disliked)
      setTimeout(() => setDislikeAnimating(false), 600)
    } catch (err) {
      console.error("Error disliking video:", err)
      setDislikeAnimating(false)
    }
  }

  return (
    <div className="flex items-center gap-2">
      {/* Like Button */}
      <button
        onClick={handleLike}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${userLiked
          ? "bg-blue-600 text-white shadow-lg shadow-blue-500/50"
          : "bg-slate-700 text-slate-300 hover:bg-slate-600"
          } ${likeAnimating ? "scale-110" : "scale-100"}`}
      >
        <div className={`transition-transform duration-300 ${likeAnimating ? "animate-bounce" : ""}`}>
          <ThumbsUp size={20} />
        </div>
        <span className="font-semibold">{likeCount}</span>
      </button>

      {/* Dislike Button */}
      <button
        onClick={handleDislike}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${userDisliked
          ? "bg-red-600 text-white shadow-lg shadow-red-500/50"
          : "bg-slate-700 text-slate-300 hover:bg-slate-600"
          } ${dislikeAnimating ? "scale-110" : "scale-100"}`}
      >
        <div className={`transition-transform duration-300 ${dislikeAnimating ? "animate-bounce" : ""}`}>
          <ThumbsDown size={20} />
        </div>
        <span className="font-semibold">{dislikeCount}</span>
      </button>
    </div>
  )
}
