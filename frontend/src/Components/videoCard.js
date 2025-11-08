import { Link } from "react-router-dom"

export default function VideoCard({ video, videoId }) {
  return (
    <Link to={`/watch/${videoId}`} className="group cursor-pointer w-full max-w-xs">
      {/* Thumbnail Container */}
      <div className="relative mb-3 overflow-hidden rounded-lg bg-gray-900">
        <img
          src={video.thumbnail || "/placeholder.svg"}
          alt={video.title}
          className="h-40 w-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
        {video.duration && (
          <div className="absolute bottom-2 right-2 rounded bg-black/80 px-2 py-1 text-xs font-semibold text-white">
            {video.duration}
          </div>
        )}
      </div>

      {/* Video Info */}
      <div className="flex gap-3">
        {/* Avatar */}
        <img
          src={video.avatar || "/placeholder.svg"}
          alt={video.channel}
          className="h-9 w-9 rounded-full object-cover flex-shrink-0"
        />

        {/* Title & Metadata */}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-white text-sm line-clamp-2 group-hover:text-blue-400 transition-colors">
            {video.title}
          </h3>
          <p className="text-xs text-gray-400 mt-1">{video.channel}</p>
          <p className="text-xs text-gray-500 mt-0.5">
            {video.views} views • {video.uploadedAt}
          </p>
        </div>
      </div>
    </Link>
  )
}
