import React, { useRef, useEffect, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useSearchContext } from '../../contexts/SearchContext'
import { PropertyListing } from '../../types/search'

// Note: You'll need to set your Mapbox access token
const MAPBOX_TOKEN = (process as any).env?.VITE_MAPBOX_TOKEN || 'pk.your-mapbox-token-here'

const MapPanel: React.FC = () => {
  const { results } = useSearchContext()
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  const [markers, setMarkers] = useState<mapboxgl.Marker[]>([])

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

  // Update markers when search results change
  useEffect(() => {
    if (!map.current || !mapLoaded) return

    // Clear existing markers
    markers.forEach(marker => marker.remove())
    setMarkers([])

    // Add new markers for search results
    if (results.length > 0) {
      const newMarkers: mapboxgl.Marker[] = []
      const bounds = new mapboxgl.LngLatBounds()

      results.forEach((listing: PropertyListing) => {
        const { lat, lon } = listing.location
        
        // Create custom marker element
        const el = document.createElement('div')
        el.className = 'property-marker'
        el.style.cssText = `
          background-color: #3B82F6;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          border: 2px solid white;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
          cursor: pointer;
        `

        // Format price for popup
        const formatPrice = (price: number) => {
          return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          }).format(price)
        }

        // Create popup content
        const popupContent = `
          <div class="property-popup">
            <h3 style="font-weight: bold; margin: 0 0 8px 0; font-size: 14px;">${listing.title}</h3>
            <div style="color: #059669; font-weight: bold; font-size: 16px; margin-bottom: 8px;">
              ${formatPrice(listing.price)}
            </div>
            <div style="font-size: 12px; color: #6B7280; margin-bottom: 4px;">
              ${listing.beds} bed • ${listing.baths} bath • ${listing.property_type}
            </div>
            <div style="font-size: 12px; color: #6B7280;">
              ${listing.address}
            </div>
          </div>
        `

        // Create marker with popup
        const marker = new mapboxgl.Marker(el)
          .setLngLat([lon, lat])
          .setPopup(new mapboxgl.Popup({ 
            offset: 25,
            closeButton: true,
            closeOnClick: true
          }).setHTML(popupContent))
          .addTo(map.current!)

        newMarkers.push(marker)
        bounds.extend([lon, lat])
      })

      setMarkers(newMarkers)

      // Fit map to show all markers
      if (results.length > 1) {
        map.current.fitBounds(bounds, {
          padding: { top: 50, bottom: 50, left: 50, right: 50 },
          maxZoom: 14
        })
      } else if (results.length === 1) {
        const { lat, lon } = results[0].location
        map.current.flyTo({
          center: [lon, lat],
          zoom: 13,
          duration: 1000
        })
      }
    }
  }, [results, mapLoaded, markers])

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