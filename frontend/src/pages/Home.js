import React from 'react';
import VideoGrid from '../Components/videoGrid';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Your video grid and other content */}
      <div className="container mx-auto px-4 py-8">
        <VideoGrid />
      </div>
    </div>
  )
}
