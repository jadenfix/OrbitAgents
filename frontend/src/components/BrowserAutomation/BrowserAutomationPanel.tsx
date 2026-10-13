import React, { useState, useEffect, useRef } from 'react';
import {
  PlayIcon,
  StopIcon,
  DocumentTextIcon,
  PhotoIcon,
  ClipboardDocumentIcon,
  CodeBracketIcon,
  WrenchScrewdriverIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

interface BrowserAction {
  type: string;
  selector?: string;
  text?: string;
  url?: string;
  wait_for?: string;
  timeout?: number;
}

interface BrowserTask {
  id: string;
  name: string;
  description: string;
  actions: BrowserAction[];
  headless: boolean;
  browser_type: string;
  viewport: { width: number; height: number };
}

interface TaskResult {
  task_id: string;
  status: string;
  result: unknown;
  screenshots: string[];
  logs: string[];
  duration: number;
  error?: string;
}

const BrowserAutomationPanel: React.FC = () => {
  const [tasks, setTasks] = useState<BrowserTask[]>([]);
  const [currentTask, setCurrentTask] = useState<BrowserTask | null>(null);
  const [taskResults, setTaskResults] = useState<{ [key: string]: TaskResult }>(
    {}
  );
  const [isRunning, setIsRunning] = useState(false);
  const [activeTab, setActiveTab] = useState<
    'builder' | 'results' | 'monitoring'
  >('builder');
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8004/ws/automation');

    ws.onopen = () => {
      setLogs((prev) => [...prev, '🔗 Connected to Browser Agent']);
      setWsConnection(ws);
    };

    ws.onmessage = (event) => {
      const message = event.data;
      setLogs((prev) => [...prev, `📥 ${message}`]);
    };

    ws.onclose = () => {
      setLogs((prev) => [...prev, '❌ Disconnected from Browser Agent']);
      setWsConnection(null);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  // Create a new task
  const createNewTask = () => {
    const newTask: BrowserTask = {
      id: `task_${Date.now()}`,
      name: 'New Automation Task',
      description: 'Describe what this automation does',
      actions: [
        { type: 'navigate', url: 'https://example.com' },
        { type: 'screenshot' },
      ],
      headless: true,
      browser_type: 'chromium',
      viewport: { width: 1920, height: 1080 },
    };
    setTasks([...tasks, newTask]);
    setCurrentTask(newTask);
  };

  // Add action to current task
  const addAction = (actionType: string) => {
    if (!currentTask) return;

    const newAction: BrowserAction = {
      type: actionType,
      timeout: 30000,
    };

    // Set defaults based on action type
    switch (actionType) {
      case 'navigate':
        newAction.url = 'https://example.com';
        break;
      case 'click':
        newAction.selector = 'button';
        break;
      case 'type':
        newAction.selector = 'input';
        newAction.text = 'Hello World';
        break;
      case 'wait':
        newAction.selector = '.loading';
        break;
    }

    const updatedTask = {
      ...currentTask,
      actions: [...currentTask.actions, newAction],
    };

    setCurrentTask(updatedTask);
    setTasks(tasks.map((t) => (t.id === currentTask.id ? updatedTask : t)));
  };

  // Update action in current task
  const updateAction = (index: number, updates: Partial<BrowserAction>) => {
    if (!currentTask) return;

    const updatedActions = [...currentTask.actions];
    updatedActions[index] = { ...updatedActions[index], ...updates };

    const updatedTask = {
      ...currentTask,
      actions: updatedActions,
    };

    setCurrentTask(updatedTask);
    setTasks(tasks.map((t) => (t.id === currentTask.id ? updatedTask : t)));
  };

  // Remove action from current task
  const removeAction = (index: number) => {
    if (!currentTask) return;

    const updatedActions = currentTask.actions.filter((_, i) => i !== index);
    const updatedTask = {
      ...currentTask,
      actions: updatedActions,
    };

    setCurrentTask(updatedTask);
    setTasks(tasks.map((t) => (t.id === currentTask.id ? updatedTask : t)));
  };

  // Run automation task
  const runTask = async (task: BrowserTask) => {
    if (!task) return;

    setIsRunning(true);
    setLogs((prev) => [...prev, `🚀 Starting task: ${task.name}`]);

    try {
      const response = await fetch('http://localhost:8004/automation/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(task),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setLogs((prev) => [...prev, `✅ Task queued: ${result.task_id}`]);

      // Poll for results
      pollTaskResult(result.task_id);
    } catch (error) {
      setLogs((prev) => [...prev, `❌ Failed to start task: ${error}`]);
    } finally {
      setIsRunning(false);
    }
  };

  // Poll for task results
  const pollTaskResult = async (taskId: string) => {
    const maxAttempts = 30;
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(
          `http://localhost:8004/tasks/${taskId}/result`
        );

        if (response.ok) {
          const result = await response.json();
          setTaskResults((prev) => ({ ...prev, [taskId]: result }));
          setLogs((prev) => [...prev, `📊 Task ${taskId} ${result.status}`]);

          if (result.status === 'completed' || result.status === 'failed') {
            return;
          }
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        }
      } catch (error) {
        setLogs((prev) => [...prev, `❌ Error polling results: ${error}`]);
      }
    };

    poll();
  };

  // Quick automation actions
  const quickActions = [
    { name: 'Screenshot', icon: PhotoIcon, action: 'screenshot' },
    { name: 'Navigate', icon: DocumentTextIcon, action: 'navigate' },
    { name: 'Click', icon: ClipboardDocumentIcon, action: 'click' },
    { name: 'Type', icon: CodeBracketIcon, action: 'type' },
    { name: 'Wait', icon: WrenchScrewdriverIcon, action: 'wait' },
    { name: 'Scroll', icon: ChartBarIcon, action: 'scroll' },
  ];

  return (
    <div className="flex h-full flex-col bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            🤖 Browser Automation
          </h2>
          <div className="flex items-center gap-2">
            <div
              className={`h-3 w-3 rounded-full ${wsConnection ? 'bg-green-500' : 'bg-red-500'}`}
            />
            <span className="text-sm text-gray-600">
              {wsConnection ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mt-4 flex space-x-1">
          {(
            [
              { key: 'builder', label: '🛠️ Builder' },
              { key: 'results', label: '📊 Results' },
              { key: 'monitoring', label: '📈 Monitoring' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`rounded-md px-3 py-2 text-sm font-medium ${
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
          <div className="flex h-full">
            {/* Task List */}
            <div className="w-1/3 border-r border-gray-200 bg-white">
              <div className="border-b border-gray-200 p-4">
                <button
                  onClick={createNewTask}
                  className="flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                >
                  <PlayIcon className="h-4 w-4" />
                  New Task
                </button>
              </div>

              <div className="overflow-y-auto">
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    onClick={() => setCurrentTask(task)}
                    className={`cursor-pointer border-b border-gray-100 p-4 hover:bg-gray-50 ${
                      currentTask?.id === task.id
                        ? 'border-blue-200 bg-blue-50'
                        : ''
                    }`}
                  >
                    <h3 className="font-medium text-gray-900">{task.name}</h3>
                    <p className="mt-1 text-sm text-gray-600">
                      {task.description}
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="rounded bg-gray-100 px-2 py-1 text-xs">
                        {task.actions.length} actions
                      </span>
                      <span className="rounded bg-gray-100 px-2 py-1 text-xs">
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
                <div className="flex h-full flex-col">
                  {/* Task Header */}
                  <div className="border-b border-gray-200 p-4">
                    <input
                      type="text"
                      value={currentTask.name}
                      onChange={(e) =>
                        setCurrentTask({ ...currentTask, name: e.target.value })
                      }
                      className="w-full border-none text-lg font-medium outline-none"
                    />
                    <textarea
                      value={currentTask.description}
                      onChange={(e) =>
                        setCurrentTask({
                          ...currentTask,
                          description: e.target.value,
                        })
                      }
                      className="mt-1 w-full resize-none border-none text-sm text-gray-600 outline-none"
                      rows={2}
                    />

                    <div className="mt-4 flex items-center gap-4">
                      <button
                        onClick={() => runTask(currentTask)}
                        disabled={isRunning}
                        className="flex items-center gap-2 rounded-md bg-green-600 px-4 py-2 text-white hover:bg-green-700 disabled:opacity-50"
                      >
                        {isRunning ? (
                          <StopIcon className="h-4 w-4" />
                        ) : (
                          <PlayIcon className="h-4 w-4" />
                        )}
                        {isRunning ? 'Running...' : 'Run Task'}
                      </button>

                      <select
                        value={currentTask.browser_type}
                        onChange={(e) =>
                          setCurrentTask({
                            ...currentTask,
                            browser_type: e.target.value,
                          })
                        }
                        className="rounded-md border border-gray-300 px-3 py-2"
                      >
                        <option value="chromium">Chromium</option>
                        <option value="firefox">Firefox</option>
                        <option value="webkit">WebKit</option>
                      </select>

                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={currentTask.headless}
                          onChange={(e) =>
                            setCurrentTask({
                              ...currentTask,
                              headless: e.target.checked,
                            })
                          }
                        />
                        <span className="text-sm">Headless</span>
                      </label>
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="border-b border-gray-200 bg-gray-50 p-4">
                    <h4 className="mb-2 text-sm font-medium text-gray-700">
                      Quick Actions
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {quickActions.map((action) => (
                        <button
                          key={action.name}
                          onClick={() => addAction(action.action)}
                          className="flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50"
                        >
                          <action.icon className="h-4 w-4" />
                          {action.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Actions List */}
                  <div className="flex-1 overflow-y-auto p-4">
                    <h4 className="mb-4 text-sm font-medium text-gray-700">
                      Actions
                    </h4>
                    {currentTask.actions.map((action, index) => (
                      <div
                        key={index}
                        className="mb-4 rounded-lg border border-gray-200 p-4"
                      >
                        <div className="mb-2 flex items-center justify-between">
                          <select
                            value={action.type}
                            onChange={(e) =>
                              updateAction(index, { type: e.target.value })
                            }
                            className="rounded border border-gray-300 px-2 py-1"
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
                            onChange={(e) =>
                              updateAction(index, { url: e.target.value })
                            }
                            className="w-full rounded border border-gray-300 px-3 py-2"
                          />
                        )}

                        {(action.type === 'click' ||
                          action.type === 'wait') && (
                          <input
                            type="text"
                            placeholder="CSS Selector"
                            value={action.selector || ''}
                            onChange={(e) =>
                              updateAction(index, { selector: e.target.value })
                            }
                            className="w-full rounded border border-gray-300 px-3 py-2"
                          />
                        )}

                        {action.type === 'type' && (
                          <div className="space-y-2">
                            <input
                              type="text"
                              placeholder="CSS Selector"
                              value={action.selector || ''}
                              onChange={(e) =>
                                updateAction(index, {
                                  selector: e.target.value,
                                })
                              }
                              className="w-full rounded border border-gray-300 px-3 py-2"
                            />
                            <input
                              type="text"
                              placeholder="Text to type"
                              value={action.text || ''}
                              onChange={(e) =>
                                updateAction(index, { text: e.target.value })
                              }
                              className="w-full rounded border border-gray-300 px-3 py-2"
                            />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex h-full items-center justify-center text-gray-500">
                  <div className="text-center">
                    <WrenchScrewdriverIcon className="mx-auto mb-4 h-16 w-16" />
                    <p>Select a task to edit or create a new one</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'results' && (
          <div className="h-full bg-white p-4">
            <h3 className="mb-4 text-lg font-medium">Task Results</h3>
            <div className="space-y-4">
              {Object.entries(taskResults).map(([taskId, result]) => (
                <div
                  key={taskId}
                  className="rounded-lg border border-gray-200 p-4"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <h4 className="font-medium">{taskId}</h4>
                    <span
                      className={`rounded px-2 py-1 text-sm ${
                        result.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : result.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {result.status}
                    </span>
                  </div>

                  <div className="text-sm text-gray-600">
                    Duration: {result.duration.toFixed(2)}s
                  </div>

                  {result.screenshots.length > 0 && (
                    <div className="mt-2">
                      <h5 className="mb-1 font-medium">Screenshots:</h5>
                      <div className="flex gap-2">
                        {result.screenshots.map((screenshot, index) => (
                          <img
                            key={index}
                            src={`http://localhost:8004/screenshots/${screenshot.split('/').pop()}`}
                            alt={`Screenshot ${index + 1}`}
                            className="h-20 w-32 rounded border border-gray-300 object-cover"
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {result.error && (
                    <div className="mt-2 rounded border border-red-200 bg-red-50 p-2">
                      <p className="text-sm text-red-800">{result.error}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'monitoring' && (
          <div className="h-full bg-white p-4">
            <h3 className="mb-4 text-lg font-medium">Live Monitoring</h3>
            <div className="h-96 overflow-y-auto rounded-lg bg-black p-4 font-mono text-sm text-green-400">
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
  );
};

export default BrowserAutomationPanel;
