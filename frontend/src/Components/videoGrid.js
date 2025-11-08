"use client"
import { useEffect, useState } from "react"
import VideoCard from "./videoCard"

export default function VideoGrid() {
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchVideos = async () => {
      try {
        const response = await fetch("https://127.0.0.1:3000")
        const data = await response.json()

        if (data.success) {
          setVideos(data.videos)
        } else {
          setError(data.error || "Failed to fetch videos")
        }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchVideos()
  }, [])

  if (loading) {
    return <div className="text-center py-8 text-gray-400">Loading videos...</div>
  }

  if (error) {
    return <div className="text-center py-8 text-red-500">Error: {error}</div>
  }

  if (videos.length === 0) {
    return <div className="text-center py-8 text-gray-400">No videos found</div>
  }

  return (
    <div className="px-4 py-8 md:px-8 md:py-12">
      {/* ✅ Responsive grid: 1 / 2 / 3 / 4 columns */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 justify-items-center">
        {videos.map((video) => (
          <VideoCard
            key={video._id}
            videoId={video.unique_name}
            video={{
              title: video.title,
              channel: video.user_name || "Unknown User",
              views: video.views || "—",
              uploadedAt: video.uploadedAt
                ? new Date(video.uploadedAt).toLocaleDateString()
                : "—",
              duration: video.duration || "",
              thumbnail: video.image_url,
              avatar: "/gradient-purple-cyan-circle.jpg",
            }}
          />
        ))}
      </div>
    </div>
  )
}
