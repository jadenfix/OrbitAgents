import React, { useState } from 'react';
import { Allotment } from 'allotment';
import 'allotment/dist/style.css';
import ChatPanel from './ChatPanel';
import MapPanel from './MapPanel';
import SearchResults from '../Search/SearchResults';
import { SearchProvider } from '../../contexts/SearchContext';
import { useSearchContext } from '../../contexts/useSearchContext';

const MainContent: React.FC = () => {
  const { results, isLoading, query, error, total } = useSearchContext();
  const [view, setView] = useState<'split' | 'list' | 'map'>(() =>
    window.matchMedia('(min-width: 768px)').matches ? 'split' : 'list'
  );

  const ViewToggle = () => (
    <div className="flex items-center gap-2 border-b border-gray-200 bg-white p-3">
      <span className="text-sm font-medium text-gray-700">View:</span>
      <div className="flex overflow-hidden rounded-lg border border-gray-300">
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
          className={`border-l border-gray-300 px-3 py-1 text-sm font-medium transition-colors ${
            view === 'split'
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          📱 Split
        </button>
        <button
          onClick={() => setView('map')}
          className={`border-l border-gray-300 px-3 py-1 text-sm font-medium transition-colors ${
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
  );

  if (view === 'list') {
    return (
      <div className="flex min-h-screen w-full flex-col md:h-screen md:flex-row">
        {/* Left Panel - Chat Interface */}
        <div className="flex h-[55vh] min-h-[360px] w-full flex-col border-r border-gray-200 bg-gray-50 md:h-full md:w-1/3">
          <ChatPanel />
        </div>

        {/* Right Panel - List View */}
        <div className="flex min-h-[45vh] min-w-0 flex-1 flex-col bg-gray-100 md:h-full">
          <ViewToggle />
          <div className="flex-1 overflow-hidden">
            <SearchResults
              results={results}
              isLoading={isLoading}
              total={total}
              query={query}
              error={error}
            />
          </div>
        </div>
      </div>
    );
  }

  if (view === 'map') {
    return (
      <div className="flex min-h-screen w-full flex-col md:h-screen md:flex-row">
        {/* Left Panel - Chat Interface */}
        <div className="flex h-[55vh] min-h-[360px] w-full flex-col border-r border-gray-200 bg-gray-50 md:h-full md:w-1/3">
          <ChatPanel />
        </div>

        {/* Right Panel - Map View */}
        <div className="flex min-h-[45vh] min-w-0 flex-1 flex-col bg-gray-100 md:h-full">
          <ViewToggle />
          <div className="flex-1">
            <MapPanel />
          </div>
        </div>
      </div>
    );
  }

  // Split view (default)
  return (
    <div className="flex min-h-screen w-full flex-col md:h-screen md:flex-row">
      {/* Left Panel - Chat Interface */}
      <div className="flex h-[55vh] min-h-[360px] w-full flex-col border-r border-gray-200 bg-gray-50 md:h-full md:w-1/3">
        <ChatPanel />
      </div>

      {/* Right Panel - Split View */}
      <div className="flex min-h-[45vh] min-w-0 flex-1 flex-col bg-gray-100 md:h-full">
        <ViewToggle />
        <div className="flex-1">
          <Allotment vertical defaultSizes={[300, 300]} minSize={200}>
            <Allotment.Pane>
              <div className="h-full border-b border-gray-200 bg-white">
                <SearchResults
                  results={results}
                  isLoading={isLoading}
                  total={total}
                  query={query}
                  error={error}
                />
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
  );
};

const SplitPaneLayout: React.FC = () => {
  return (
    <SearchProvider>
      <MainContent />
    </SearchProvider>
  );
};

export default SplitPaneLayout;
