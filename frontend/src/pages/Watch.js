"use client"

import { useState, useEffect, useRef } from "react"
import { Share2, MessageCircle } from "lucide-react"
import { useNavigate, useParams } from "react-router-dom"
import LikeDislikeButton from "./Like"
import apiClient from "../api/apiClient"
import { useAuth } from "../Context/AuthContext"

export default function VideoPlayer() {

  const navigate = useNavigate();
  const { uniqueName } = useParams()
  const [videoData, setVideoData] = useState(null)
  const [quality, setQuality] = useState("auto")
  const [comments, setComments] = useState([])
  const [newComment, setNewComment] = useState("")
  const [loading, setLoading] = useState(true)
  const [likeCount, setLikeCount] = useState(0)
  const [dislikeCount, setDislikeCount] = useState(0)
  const [userLiked, setUserLiked] = useState(false)
  const [userDisliked, setUserDisliked] = useState(false)
  const [availableQualities, setAvailableQualities] = useState([])
  const [commentLoading, setCommentLoading] = useState(false)
  const { isAuthenticated, user, token } = useAuth()

  const videoRef = useRef(null)
  const hlsRef = useRef(null)

  // Fetch Video Data
  useEffect(() => {
    if (!uniqueName) return
    const fetchVideoData = async () => {
      try {
        console.log("Fetching video data for:", uniqueName)
        const res = await fetch(`https://127.0.0.1:3000/api/video/${uniqueName}`)
        const data = await res.json()
        console.log("Video data:", data)

        setVideoData(data)
        setComments(data.comments || [])
        setUserLiked(data.user_has_liked)
        setUserDisliked(data.user_has_disliked || false)
        setLikeCount(data.like_count)
        setDislikeCount(data.dislike_count || 0)
      } catch (err) {
        console.error("Error fetching video data:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchVideoData()
  }, [uniqueName])

  useEffect(() => {
    if (!uniqueName) return
    const fetchComments = async () => {
      try {
        const res = await apiClient.get(`/comment/${uniqueName}`)
        if (res.data.success) {
          setComments(res.data.comments)
        }
      } catch (err) {
        console.error("Error fetching comments:", err)
      }
    }

    fetchComments()
  }, [uniqueName])

  // HLS Initialization
  useEffect(() => {
    let hls
    let retryTimer

    const setupHLS = async () => {
      if (!videoRef.current) {
        console.warn("Video element not ready yet")
        retryTimer = setTimeout(setupHLS, 50)
        return
      }

      console.log("Video element ready, initializing HLS...")
      const HLS = (await import("hls.js")).default

      if (HLS.isSupported()) {
        hls = new HLS({
          enableWorker: true,
          lowLatencyMode: true,
          autoStartLoad: true,
        })
        hlsRef.current = hls

        hls.attachMedia(videoRef.current)
        hls.on(HLS.Events.MEDIA_ATTACHED, () => {
          console.log("Media attached, loading manifest...")
          hls.loadSource(`https://127.0.0.1:3000/watch/${uniqueName}/master.m3u8`)
        })

        hls.on(HLS.Events.MANIFEST_PARSED, (_, data) => {
          const levels = data.levels.map((lvl) => lvl.height.toString())
          setAvailableQualities(levels)
          setQuality("auto")
          hls.currentLevel = -1
          console.log("Available qualities:", levels)
        })

        hls.on(HLS.Events.LEVEL_SWITCHED, (_, data) => {
          const currentLevel = hls.levels[data.level]
          if (currentLevel) {
            console.log("Auto-switched to:", currentLevel.height + "p")
            if (quality === "auto") {
              setQuality("auto")
            }
          }
        })

        hls.on(HLS.Events.ERROR, (_, data) => {
          console.error("HLS error:", data)
        })
      } else if (videoRef.current.canPlayType("application/vnd.apple.mpegurl")) {
        videoRef.current.src = `https://127.0.0.1:3000/watch/${uniqueName}/master.m3u8`
      }
    }

    setupHLS()

    return () => {
      if (retryTimer) clearTimeout(retryTimer)
      if (hls) hls.destroy()
    }
  }, [uniqueName])

  // Quality Change
  const handleQualityChange = (newQuality) => {
    const hls = hlsRef.current
    const video = videoRef.current
    if (!hls || !video) return

    const currentTime = video.currentTime
    const wasPlaying = !video.paused

    if (newQuality === "auto") {
      console.log("Switched to Auto (adaptive) mode")
      hls.currentLevel = -1
      setQuality("auto")
    } else {
      const levelIndex = hls.levels.findIndex((lvl) => lvl.height.toString() === newQuality)
      if (levelIndex !== -1) {
        console.log("Switching to manual quality:", newQuality)
        hls.currentLevel = levelIndex
        setQuality(newQuality)
      } else {
        console.warn("Quality not found:", newQuality)
      }
    }

    video.currentTime = currentTime
    if (wasPlaying) video.play().catch(() => { })
  }

  const handleCommentSubmit = async (e) => {
    e.preventDefault()
    if (!newComment.trim()) return
    if (!isAuthenticated) {

      navigate("/auth");
    }

    setCommentLoading(true)
    try {
      const res = await apiClient.post(
        `/comment/${uniqueName}`,
        { comments: newComment },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        },
      )

      if (res.data.success && res.data.comments) {
        const newCommentObj = res.data.comments[0] || res.data.comments
        setComments((prev) => [...prev, newCommentObj])
        setNewComment("")
      }
    } catch (err) {
      console.error("Error posting comment:", err)
    } finally {
      setCommentLoading(false)
    }
  }

  const handleLikeCountChange = (newLikeCount, newDislikeCount, liked, disliked) => {
    setLikeCount(newLikeCount)
    setDislikeCount(newDislikeCount)
    setUserLiked(liked)
    setUserDisliked(disliked)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
        <div className="text-white text-xl">Loading video...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Video Player */}
        <div className="mb-8">
          <div className="relative bg-black rounded-xl overflow-hidden shadow-2xl">
            <video ref={videoRef} controls className="w-full aspect-video" poster="/video-thumbnail.png" />
          </div>

          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <label className="text-slate-300 font-medium">Quality:</label>
              <select
                value={quality}
                onChange={(e) => handleQualityChange(e.target.value)}
                className="px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 hover:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
              >
                <option value="auto">Auto</option>
                {availableQualities.map((q) => (
                  <option key={q} value={q}>
                    {q}p
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Video Info Section */}
        <div className="bg-slate-800 rounded-xl shadow-xl p-6 mb-8 border border-slate-700">
          <h1 className="text-4xl font-bold text-white mb-4">{videoData?.video_title}</h1>

          {/* Action Buttons */}
          <div className="flex items-center gap-4 mb-6 pb-6 border-b border-slate-700">
            <LikeDislikeButton
              videoId={uniqueName}
              initialLikeCount={likeCount}
              initialDislikeCount={dislikeCount}
              initialUserLiked={userLiked}
              initialUserDisliked={userDisliked}
              onLikeChange={handleLikeCountChange}
            />
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 font-medium transition">
              <Share2 size={20} />
              <span>Share</span>
            </button>
          </div>

          {/* Video Description */}
          <div className="bg-slate-700 rounded-lg p-4">
            <h3 className="text-slate-300 font-semibold mb-2">Description</h3>
            <p className="text-slate-400 leading-relaxed">{videoData?.video_description}</p>
          </div>
        </div>

        {/* Comments Section */}
        <div className="bg-slate-800 rounded-xl shadow-xl p-6 border border-slate-700">
          <div className="flex items-center gap-2 mb-6">
            <MessageCircle size={24} className="text-blue-500" />
            <h2 className="text-2xl font-bold text-white">{comments.length} Comments</h2>
          </div>

          {/* Comment Input */}
          <form onSubmit={handleCommentSubmit} className="mb-8 pb-8 border-b border-slate-700">
            <div className="flex gap-4">
              <img
                src={videoData?.current_user_avatar || "/placeholder.svg?height=40&width=40"}
                alt="Your avatar"
                className="w-10 h-10 rounded-full object-cover"
              />
              <div className="flex-1">
                <textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Add a public comment..."
                  className="w-full px-4 py-3 bg-slate-700 text-white rounded-lg border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none placeholder-slate-500"
                  rows={3}
                  disabled={commentLoading}
                />
                <div className="flex justify-end mt-3">
                  <button
                    type="submit"
                    disabled={commentLoading}
                    className="px-6 py-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {commentLoading ? "Posting..." : "Comment"}
                  </button>
                </div>
              </div>
            </div>
          </form>

          {/* Comments List */}
          <div className="space-y-4">
            {comments.length === 0 ? (
              <p className="text-slate-400 text-center py-8">No comments yet. Be the first to comment!</p>
            ) : (
              comments.map((comment) => (
                <div key={comment._id} className="flex gap-4 p-4 bg-slate-700 rounded-lg hover:bg-slate-600 transition">
                  <img src="/placeholder.svg" alt="User" className="w-10 h-10 rounded-full object-cover" />

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-semibold text-white">User {comment.user_id}</p>
                      <span className="text-xs text-slate-400">
                        {comment.created_at ? new Date(comment.created_at).toLocaleDateString() : "now"}
                      </span>
                    </div>

                    <p className="text-slate-300 mb-3">{comment.text}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
