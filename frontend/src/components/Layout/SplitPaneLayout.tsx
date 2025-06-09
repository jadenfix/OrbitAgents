import React, { useState } from 'react'
import SplitPane from 'react-split-pane'
import ChatPanel from './ChatPanel'
import MapPanel from './MapPanel'

const SplitPaneLayout: React.FC = () => {
  const [splitPos, setSplitPos] = useState<string | number>('50%')

  return (
    <div className="h-screen w-full">
      <SplitPane
        split="vertical"
        minSize={300}
        maxSize={800}
        defaultSize={splitPos}
        onChange={(size) => setSplitPos(size)}
        style={{ position: 'relative' }}
      >
        {/* Left Panel - Chat Interface */}
        <div className="h-full bg-gray-50 border-r border-gray-200">
          <ChatPanel />
        </div>
        
        {/* Right Panel - Map */}
        <div className="h-full bg-gray-100">
          <MapPanel />
        </div>
      </SplitPane>
    </div>
  )
}

export default SplitPaneLayout 