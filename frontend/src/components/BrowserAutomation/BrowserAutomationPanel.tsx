import React, { useState, useEffect, useRef } from 'react'
import { 
  PlayIcon, 
  StopIcon, 
  DocumentTextIcon, 
  PhotoIcon,
  ClipboardDocumentIcon,
  CodeBracketIcon,
  WrenchScrewdriverIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

interface BrowserAction {
  type: string
  selector?: string
  text?: string
  url?: string
  wait_for?: string
  timeout?: number
}

interface BrowserTask {
  id: string
  name: string
  description: string
  actions: BrowserAction[]
  headless: boolean
  browser_type: string
  viewport: { width: number; height: number }
}

interface TaskResult {
  task_id: string
  status: string
  result: any
  screenshots: string[]
  logs: string[]
  duration: number
  error?: string
}

const BrowserAutomationPanel: React.FC = () => {
  const [tasks, setTasks] = useState<BrowserTask[]>([])
  const [currentTask, setCurrentTask] = useState<BrowserTask | null>(null)
  const [taskResults, setTaskResults] = useState<{ [key: string]: TaskResult }>({})
  const [isRunning, setIsRunning] = useState(false)
  const [activeTab, setActiveTab] = useState<'builder' | 'results' | 'monitoring'>('builder')
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  
  const wsRef = useRef<WebSocket | null>(null)

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8004/ws/automation')
    
    ws.onopen = () => {
      setLogs(prev => [...prev, '🔗 Connected to Browser Agent'])
      setWsConnection(ws)
    }
    
    ws.onmessage = (event) => {
      const message = event.data
      setLogs(prev => [...prev, `📥 ${message}`])
    }
    
    ws.onclose = () => {
      setLogs(prev => [...prev, '❌ Disconnected from Browser Agent'])
      setWsConnection(null)
    }
    
    wsRef.current = ws
    
    return () => {
      ws.close()
    }
  }, [])

  // Create a new task
  const createNewTask = () => {
    const newTask: BrowserTask = {
      id: `task_${Date.now()}`,
      name: 'New Automation Task',
      description: 'Describe what this automation does',
      actions: [
        { type: 'navigate', url: 'https://example.com' },
        { type: 'screenshot' }
      ],
      headless: true,
      browser_type: 'chromium',
      viewport: { width: 1920, height: 1080 }
    }
    setTasks([...tasks, newTask])
    setCurrentTask(newTask)
  }

  // Add action to current task
  const addAction = (actionType: string) => {
    if (!currentTask) return
    
    const newAction: BrowserAction = {
      type: actionType,
      timeout: 30000
    }
    
    // Set defaults based on action type
    switch (actionType) {
      case 'navigate':
        newAction.url = 'https://example.com'
        break
      case 'click':
        newAction.selector = 'button'
        break
      case 'type':
        newAction.selector = 'input'
        newAction.text = 'Hello World'
        break
      case 'wait':
        newAction.selector = '.loading'
        break
    }
    
    const updatedTask = {
      ...currentTask,
      actions: [...currentTask.actions, newAction]
    }
    
    setCurrentTask(updatedTask)
    setTasks(tasks.map(t => t.id === currentTask.id ? updatedTask : t))
  }

  // Update action in current task
  const updateAction = (index: number, updates: Partial<BrowserAction>) => {
    if (!currentTask) return
    
    const updatedActions = [...currentTask.actions]
    updatedActions[index] = { ...updatedActions[index], ...updates }
    
    const updatedTask = {
      ...currentTask,
      actions: updatedActions
    }
    
    setCurrentTask(updatedTask)
    setTasks(tasks.map(t => t.id === currentTask.id ? updatedTask : t))
  }

  // Remove action from current task
  const removeAction = (index: number) => {
    if (!currentTask) return
    
    const updatedActions = currentTask.actions.filter((_, i) => i !== index)
    const updatedTask = {
      ...currentTask,
      actions: updatedActions
    }
    
    setCurrentTask(updatedTask)
    setTasks(tasks.map(t => t.id === currentTask.id ? updatedTask : t))
  }

  // Run automation task
  const runTask = async (task: BrowserTask) => {
    if (!task) return
    
    setIsRunning(true)
    setLogs(prev => [...prev, `🚀 Starting task: ${task.name}`])
    
    try {
      const response = await fetch('http://localhost:8004/automation/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(task)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      setLogs(prev => [...prev, `✅ Task queued: ${result.task_id}`])
      
      // Poll for results
      pollTaskResult(result.task_id)
      
    } catch (error) {
      setLogs(prev => [...prev, `❌ Failed to start task: ${error}`])
    } finally {
      setIsRunning(false)
    }
  }

  // Poll for task results
  const pollTaskResult = async (taskId: string) => {
    const maxAttempts = 30
    let attempts = 0
    
    const poll = async () => {
      try {
        const response = await fetch(`http://localhost:8004/tasks/${taskId}/result`)
        
        if (response.ok) {
          const result = await response.json()
          setTaskResults(prev => ({ ...prev, [taskId]: result }))
          setLogs(prev => [...prev, `📊 Task ${taskId} ${result.status}`])
          
          if (result.status === 'completed' || result.status === 'failed') {
            return
          }
        }
        
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000)
        }
      } catch (error) {
        setLogs(prev => [...prev, `❌ Error polling results: ${error}`])
      }
    }
    
    poll()
  }

  // Quick automation actions
  const quickActions = [
    { name: 'Screenshot', icon: PhotoIcon, action: 'screenshot' },
    { name: 'Navigate', icon: DocumentTextIcon, action: 'navigate' },
    { name: 'Click', icon: ClipboardDocumentIcon, action: 'click' },
    { name: 'Type', icon: CodeBracketIcon, action: 'type' },
    { name: 'Wait', icon: WrenchScrewdriverIcon, action: 'wait' },
    { name: 'Scroll', icon: ChartBarIcon, action: 'scroll' }
  ]

  return (
    <div className="h-full bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">🤖 Browser Automation</h2>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${wsConnection ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600">
              {wsConnection ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
        
        {/* Tab Navigation */}
        <div className="mt-4 flex space-x-1">
          {[
            { key: 'builder', label: '🛠️ Builder' },
            { key: 'results', label: '📊 Results' },
            { key: 'monitoring', label: '📈 Monitoring' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`px-3 py-2 text-sm font-medium rounded-md ${
                activeTab === tab.key
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'builder' && (
          <div className="h-full flex">
            {/* Task List */}
            <div className="w-1/3 border-r border-gray-200 bg-white">
              <div className="p-4 border-b border-gray-200">
                <button
                  onClick={createNewTask}
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center justify-center gap-2"
                >
                  <PlayIcon className="w-4 h-4" />
                  New Task
                </button>
              </div>
              
              <div className="overflow-y-auto">
                {tasks.map(task => (
                  <div
                    key={task.id}
                    onClick={() => setCurrentTask(task)}
                    className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                      currentTask?.id === task.id ? 'bg-blue-50 border-blue-200' : ''
                    }`}
                  >
                    <h3 className="font-medium text-gray-900">{task.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {task.actions.length} actions
                      </span>
                      <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {task.browser_type}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Task Builder */}
            <div className="flex-1 bg-white">
              {currentTask ? (
                <div className="h-full flex flex-col">
                  {/* Task Header */}
                  <div className="p-4 border-b border-gray-200">
                    <input
                      type="text"
                      value={currentTask.name}
                      onChange={(e) => setCurrentTask({...currentTask, name: e.target.value})}
                      className="text-lg font-medium border-none outline-none w-full"
                    />
                    <textarea
                      value={currentTask.description}
                      onChange={(e) => setCurrentTask({...currentTask, description: e.target.value})}
                      className="text-sm text-gray-600 mt-1 w-full border-none outline-none resize-none"
                      rows={2}
                    />
                    
                    <div className="flex items-center gap-4 mt-4">
                      <button
                        onClick={() => runTask(currentTask)}
                        disabled={isRunning}
                        className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                      >
                        {isRunning ? <StopIcon className="w-4 h-4" /> : <PlayIcon className="w-4 h-4" />}
                        {isRunning ? 'Running...' : 'Run Task'}
                      </button>
                      
                      <select
                        value={currentTask.browser_type}
                        onChange={(e) => setCurrentTask({...currentTask, browser_type: e.target.value})}
                        className="border border-gray-300 rounded-md px-3 py-2"
                      >
                        <option value="chromium">Chromium</option>
                        <option value="firefox">Firefox</option>
                        <option value="webkit">WebKit</option>
                      </select>
                      
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={currentTask.headless}
                          onChange={(e) => setCurrentTask({...currentTask, headless: e.target.checked})}
                        />
                        <span className="text-sm">Headless</span>
                      </label>
                    </div>
                  </div>
                  
                  {/* Quick Actions */}
                  <div className="p-4 border-b border-gray-200 bg-gray-50">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Quick Actions</h4>
                    <div className="flex flex-wrap gap-2">
                      {quickActions.map(action => (
                        <button
                          key={action.name}
                          onClick={() => addAction(action.action)}
                          className="flex items-center gap-1 px-3 py-1 bg-white border border-gray-300 rounded-md hover:bg-gray-50 text-sm"
                        >
                          <action.icon className="w-4 h-4" />
                          {action.name}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  {/* Actions List */}
                  <div className="flex-1 overflow-y-auto p-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-4">Actions</h4>
                    {currentTask.actions.map((action, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4 mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <select
                            value={action.type}
                            onChange={(e) => updateAction(index, { type: e.target.value })}
                            className="border border-gray-300 rounded px-2 py-1"
                          >
                            <option value="navigate">Navigate</option>
                            <option value="click">Click</option>
                            <option value="type">Type</option>
                            <option value="wait">Wait</option>
                            <option value="scroll">Scroll</option>
                            <option value="screenshot">Screenshot</option>
                          </select>
                          <button
                            onClick={() => removeAction(index)}
                            className="text-red-600 hover:text-red-800"
                          >
                            Remove
                          </button>
                        </div>
                        
                        {action.type === 'navigate' && (
                          <input
                            type="url"
                            placeholder="URL"
                            value={action.url || ''}
                            onChange={(e) => updateAction(index, { url: e.target.value })}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                          />
                        )}
                        
                        {(action.type === 'click' || action.type === 'wait') && (
                          <input
                            type="text"
                            placeholder="CSS Selector"
                            value={action.selector || ''}
                            onChange={(e) => updateAction(index, { selector: e.target.value })}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                          />
                        )}
                        
                        {action.type === 'type' && (
                          <div className="space-y-2">
                            <input
                              type="text"
                              placeholder="CSS Selector"
                              value={action.selector || ''}
                              onChange={(e) => updateAction(index, { selector: e.target.value })}
                              className="w-full border border-gray-300 rounded px-3 py-2"
                            />
                            <input
                              type="text"
                              placeholder="Text to type"
                              value={action.text || ''}
                              onChange={(e) => updateAction(index, { text: e.target.value })}
                              className="w-full border border-gray-300 rounded px-3 py-2"
                            />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <WrenchScrewdriverIcon className="w-16 h-16 mx-auto mb-4" />
                    <p>Select a task to edit or create a new one</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        
        {activeTab === 'results' && (
          <div className="h-full p-4 bg-white">
            <h3 className="text-lg font-medium mb-4">Task Results</h3>
            <div className="space-y-4">
              {Object.entries(taskResults).map(([taskId, result]) => (
                <div key={taskId} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{taskId}</h4>
                    <span className={`px-2 py-1 rounded text-sm ${
                      result.status === 'completed' ? 'bg-green-100 text-green-800' :
                      result.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {result.status}
                    </span>
                  </div>
                  
                  <div className="text-sm text-gray-600">
                    Duration: {result.duration.toFixed(2)}s
                  </div>
                  
                  {result.screenshots.length > 0 && (
                    <div className="mt-2">
                      <h5 className="font-medium mb-1">Screenshots:</h5>
                      <div className="flex gap-2">
                        {result.screenshots.map((screenshot, index) => (
                          <img
                            key={index}
                            src={`http://localhost:8004/screenshots/${screenshot.split('/').pop()}`}
                            alt={`Screenshot ${index + 1}`}
                            className="w-32 h-20 object-cover border border-gray-300 rounded"
                          />
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {result.error && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                      <p className="text-sm text-red-800">{result.error}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {activeTab === 'monitoring' && (
          <div className="h-full p-4 bg-white">
            <h3 className="text-lg font-medium mb-4">Live Monitoring</h3>
            <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm h-96 overflow-y-auto">
              {logs.map((log, index) => (
                <div key={index} className="mb-1">
                  {new Date().toLocaleTimeString()} - {log}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default BrowserAutomationPanel
