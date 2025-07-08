import React, { useState } from 'react'
import { Allotment } from 'allotment'
import 'allotment/dist/style.css'
import ChatPanel from './ChatPanel'
import MapPanel from './MapPanel'
import SearchResults from '../Search/SearchResults'
import { SearchProvider, useSearchContext } from '../../contexts/SearchContext'

const MainContent: React.FC = () => {
  const { results, isLoading } = useSearchContext()
  const [view, setView] = useState<'split' | 'list' | 'map'>('split')

  const ViewToggle = () => (
    <div className="flex items-center gap-2 p-3 bg-white border-b border-gray-200">
      <span className="text-sm font-medium text-gray-700">View:</span>
      <div className="flex rounded-lg border border-gray-300 overflow-hidden">
        <button
          onClick={() => setView('list')}
          className={`px-3 py-1 text-sm font-medium transition-colors ${
            view === 'list'
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          📋 List
        </button>
        <button
          onClick={() => setView('split')}
          className={`px-3 py-1 text-sm font-medium transition-colors border-l border-gray-300 ${
            view === 'split'
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          📱 Split
        </button>
        <button
          onClick={() => setView('map')}
          className={`px-3 py-1 text-sm font-medium transition-colors border-l border-gray-300 ${
            view === 'map'
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          🗺️ Map
        </button>
      </div>
      {results.length > 0 && (
        <div className="ml-auto text-sm text-gray-500">
          {results.length} properties
        </div>
      )}
    </div>
  )

  if (view === 'list') {
    return (
      <div className="h-screen w-full flex">
        {/* Left Panel - Chat Interface */}
        <div className="w-1/3 h-full bg-gray-50 border-r border-gray-200 flex flex-col">
          <ChatPanel />
        </div>
        
        {/* Right Panel - List View */}
        <div className="flex-1 h-full bg-gray-100 flex flex-col">
          <ViewToggle />
          <div className="flex-1 overflow-hidden">
            <SearchResults results={results} isLoading={isLoading} total={results.length} />
          </div>
        </div>
      </div>
    )
  }

  if (view === 'map') {
    return (
      <div className="h-screen w-full flex">
        {/* Left Panel - Chat Interface */}
        <div className="w-1/3 h-full bg-gray-50 border-r border-gray-200 flex flex-col">
          <ChatPanel />
        </div>
        
        {/* Right Panel - Map View */}
        <div className="flex-1 h-full bg-gray-100 flex flex-col">
          <ViewToggle />
          <div className="flex-1">
            <MapPanel />
          </div>
        </div>
      </div>
    )
  }

  // Split view (default)
  return (
    <div className="h-screen w-full flex">
      {/* Left Panel - Chat Interface */}
      <div className="w-1/3 h-full bg-gray-50 border-r border-gray-200 flex flex-col">
        <ChatPanel />
      </div>
      
      {/* Right Panel - Split View */}
      <div className="flex-1 h-full bg-gray-100 flex flex-col">
        <ViewToggle />
        <div className="flex-1">
          <Allotment vertical defaultSizes={[300, 300]} minSize={200}>
            <Allotment.Pane>
              <div className="h-full bg-white border-b border-gray-200">
                <SearchResults results={results} isLoading={isLoading} total={results.length} />
              </div>
            </Allotment.Pane>
            <Allotment.Pane>
              <div className="h-full bg-gray-100">
                <MapPanel />
              </div>
            </Allotment.Pane>
          </Allotment>
        </div>
      </div>
    </div>
  )
}

const SplitPaneLayout: React.FC = () => {
  return (
    <SearchProvider>
      <MainContent />
    </SearchProvider>
  )
}

export default SplitPaneLayout 