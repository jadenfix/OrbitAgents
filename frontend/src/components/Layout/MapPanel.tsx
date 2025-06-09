import React, { useRef, useEffect, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

// Note: You'll need to set your Mapbox access token
const MAPBOX_TOKEN = process.env.VITE_MAPBOX_TOKEN || 'pk.your-mapbox-token-here'

const MapPanel: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)

  useEffect(() => {
    if (map.current) return // Initialize map only once

    if (mapContainer.current) {
      mapboxgl.accessToken = MAPBOX_TOKEN

      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [-104.9903, 39.7392], // Denver, Colorado coordinates
        zoom: 10,
        bearing: 0,
        pitch: 0
      })

      // Add navigation controls
      map.current.addControl(new mapboxgl.NavigationControl(), 'top-right')

      // Add fullscreen control
      map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right')

      // Add scale control
      map.current.addControl(new mapboxgl.ScaleControl({
        maxWidth: 100,
        unit: 'imperial'
      }), 'bottom-left')

      // Map load event
      map.current.on('load', () => {
        setMapLoaded(true)
        
        // Add a marker for Denver
        if (map.current) {
          new mapboxgl.Marker({
            color: '#3B82F6',
            scale: 0.8
          })
          .setLngLat([-104.9903, 39.7392])
          .setPopup(new mapboxgl.Popup({ offset: 25 })
            .setHTML('<h3>Denver, Colorado</h3><p>Mile High City</p>'))
          .addTo(map.current)
        }
      })

      // Map error handling
      map.current.on('error', (e) => {
        console.error('Mapbox error:', e)
      })
    }

    // Cleanup function
    return () => {
      if (map.current) {
        map.current.remove()
        map.current = null
      }
    }
  }, [])

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      if (map.current) {
        map.current.resize()
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <div className="relative h-full w-full">
      {/* Map Container */}
      <div 
        ref={mapContainer} 
        className="h-full w-full"
        style={{ minHeight: '400px' }}
      />
      
      {/* Loading Overlay */}
      {!mapLoaded && (
        <div className="absolute inset-0 bg-gray-100 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-600">Loading map...</p>
          </div>
        </div>
      )}

      {/* Map Info Panel */}
      <div className="absolute top-4 left-4 bg-white bg-opacity-90 backdrop-blur-sm rounded-lg p-3 shadow-lg">
        <h3 className="text-sm font-semibold text-gray-900">Search Results Map</h3>
        <p className="text-xs text-gray-600 mt-1">
          Search results will appear as markers on this map
        </p>
        {mapLoaded && (
          <div className="mt-2 text-xs text-green-600">
            ✓ Map loaded successfully
          </div>
        )}
      </div>

      {/* Attribution (required by Mapbox) */}
      <div className="absolute bottom-0 right-0 bg-white bg-opacity-75 px-2 py-1 text-xs text-gray-600">
        © Mapbox © OpenStreetMap
      </div>
    </div>
  )
}

export default MapPanel 