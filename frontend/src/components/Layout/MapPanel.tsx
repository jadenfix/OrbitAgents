import React, { useRef, useEffect, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useSearchContext } from '../../contexts/SearchContext'
import { PropertyListing } from '../../types/search'

// Note: You'll need to set your Mapbox access token
const MAPBOX_TOKEN = (process as any).env?.VITE_MAPBOX_TOKEN || 'pk.your-mapbox-token-here'

interface MapFilters {
  minPrice: number
  maxPrice: number
  beds: number[]
  priceRange: [number, number]
}

const MapPanel: React.FC = () => {
  const { results } = useSearchContext()
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  const [markers, setMarkers] = useState<mapboxgl.Marker[]>([])
  const [filters, setFilters] = useState<MapFilters>({
    minPrice: 0,
    maxPrice: 2000000,
    beds: [],
    priceRange: [0, 2000000]
  })

  // Calculate price range from results
  const priceRange = React.useMemo(() => {
    if (results.length === 0) return [0, 2000000]
    const prices = results.map(r => r.price)
    return [Math.min(...prices), Math.max(...prices)]
  }, [results])

  // Get unique bed counts
  const bedOptions = React.useMemo(() => {
    const beds = new Set(results.map(r => r.beds))
    return Array.from(beds).sort((a, b) => a - b)
  }, [results])

  // Filter results based on current filters
  const filteredResults = React.useMemo(() => {
    return results.filter(listing => {
      const priceInRange = listing.price >= filters.priceRange[0] && listing.price <= filters.priceRange[1]
      const bedsMatch = filters.beds.length === 0 || filters.beds.includes(listing.beds)
      return priceInRange && bedsMatch
    })
  }, [results, filters])

  // Format price for display
  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`
    } else if (price >= 1000) {
      return `$${(price / 1000).toFixed(0)}K`
    }
    return `$${price.toLocaleString()}`
  }

  const formatPriceFull = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price)
  }

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

  // Update markers when filtered results change
  useEffect(() => {
    if (!map.current || !mapLoaded) return

    // Clear existing markers
    markers.forEach(marker => marker.remove())
    setMarkers([])

    // Add new markers for filtered search results
    if (filteredResults.length > 0) {
      const newMarkers: mapboxgl.Marker[] = []
      const bounds = new mapboxgl.LngLatBounds()

      filteredResults.forEach((listing: PropertyListing) => {
        const { lat, lon } = listing.location
        
        // Create custom marker element with price label
        const el = document.createElement('div')
        el.className = 'property-marker'
        el.innerHTML = `
          <div style="
            background-color: #3B82F6;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            white-space: nowrap;
            border: 2px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            cursor: pointer;
            position: relative;
          ">
            ${formatPrice(listing.price)}
            <div style="
              position: absolute;
              bottom: -6px;
              left: 50%;
              transform: translateX(-50%);
              width: 0;
              height: 0;
              border-left: 6px solid transparent;
              border-right: 6px solid transparent;
              border-top: 6px solid #3B82F6;
            "></div>
          </div>
        `

        // Create popup content
        const popupContent = `
          <div class="property-popup">
            <h3 style="font-weight: bold; margin: 0 0 8px 0; font-size: 14px;">${listing.title}</h3>
            <div style="color: #059669; font-weight: bold; font-size: 18px; margin-bottom: 8px;">
              ${formatPriceFull(listing.price)}
            </div>
            <div style="font-size: 12px; color: #6B7280; margin-bottom: 4px;">
              <span style="background: #F3F4F6; padding: 2px 6px; border-radius: 4px; margin-right: 4px;">
                ${listing.beds} bed
              </span>
              <span style="background: #F3F4F6; padding: 2px 6px; border-radius: 4px; margin-right: 4px;">
                ${listing.baths} bath
              </span>
              <span style="background: #F3F4F6; padding: 2px 6px; border-radius: 4px;">
                ${listing.property_type}
              </span>
            </div>
            <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">
              ${listing.address}
            </div>
            ${listing.amenities && listing.amenities.length > 0 ? `
              <div style="font-size: 11px; color: #9CA3AF;">
                ${listing.amenities.slice(0, 3).join(' • ')}
              </div>
            ` : ''}
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
      if (filteredResults.length > 1) {
        map.current.fitBounds(bounds, {
          padding: { top: 100, bottom: 50, left: 50, right: 50 },
          maxZoom: 14
        })
      } else if (filteredResults.length === 1) {
        const { lat, lon } = filteredResults[0].location
        map.current.flyTo({
          center: [lon, lat],
          zoom: 13,
          duration: 1000
        })
      }
    }
  }, [filteredResults, mapLoaded, markers])

  // Update filters when price range changes
  useEffect(() => {
    if (priceRange[0] !== filters.priceRange[0] || priceRange[1] !== filters.priceRange[1]) {
      setFilters(prev => ({
        ...prev,
        priceRange: [priceRange[0], priceRange[1]]
      }))
    }
  }, [priceRange])

  const handleBedFilter = (bedCount: number) => {
    setFilters(prev => ({
      ...prev,
      beds: prev.beds.includes(bedCount) 
        ? prev.beds.filter(b => b !== bedCount)
        : [...prev.beds, bedCount]
    }))
  }

  const handlePriceRangeChange = (values: [number, number]) => {
    setFilters(prev => ({
      ...prev,
      priceRange: values
    }))
  }

  const clearFilters = () => {
    setFilters({
      minPrice: priceRange[0],
      maxPrice: priceRange[1],
      beds: [],
      priceRange: [priceRange[0], priceRange[1]]
    })
  }

  return (
    <div className="relative h-full w-full">
      {/* Filter Controls */}
      {results.length > 0 && (
        <div className="absolute top-4 left-4 right-4 z-10 bg-white bg-opacity-95 backdrop-blur-sm rounded-lg p-4 shadow-lg">
          <div className="flex flex-wrap items-center gap-4">
            {/* Bed Filters */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Beds:</span>
              <div className="flex gap-1">
                {bedOptions.map(bedCount => (
                  <button
                    key={bedCount}
                    onClick={() => handleBedFilter(bedCount)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      filters.beds.includes(bedCount)
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {bedCount}
                  </button>
                ))}
              </div>
            </div>

            {/* Price Range */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Price:</span>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={priceRange[0]}
                  max={priceRange[1]}
                  value={filters.priceRange[0]}
                  onChange={(e) => handlePriceRangeChange([parseInt(e.target.value), filters.priceRange[1]])}
                  className="w-20"
                />
                <span className="text-xs text-gray-600">
                  {formatPrice(filters.priceRange[0])} - {formatPrice(filters.priceRange[1])}
                </span>
                <input
                  type="range"
                  min={priceRange[0]}
                  max={priceRange[1]}
                  value={filters.priceRange[1]}
                  onChange={(e) => handlePriceRangeChange([filters.priceRange[0], parseInt(e.target.value)])}
                  className="w-20"
                />
              </div>
            </div>

            {/* Clear Filters */}
            {(filters.beds.length > 0 || filters.priceRange[0] !== priceRange[0] || filters.priceRange[1] !== priceRange[1]) && (
              <button
                onClick={clearFilters}
                className="px-3 py-1 bg-gray-500 text-white rounded-full text-sm hover:bg-gray-600 transition-colors"
              >
                Clear All
              </button>
            )}

            {/* Results Count */}
            <div className="text-sm text-gray-600">
              {filteredResults.length} of {results.length} properties
            </div>
          </div>
        </div>
      )}

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

      {/* Attribution (required by Mapbox) */}
      <div className="absolute bottom-0 right-0 bg-white bg-opacity-75 px-2 py-1 text-xs text-gray-600">
        © Mapbox © OpenStreetMap
      </div>
    </div>
  )
}

export default MapPanel 