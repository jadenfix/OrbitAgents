import React, { useState, useRef, useEffect } from 'react'
import { PaperAirplaneIcon } from '@heroicons/react/24/outline'
import { useAuth } from '../../contexts/AuthContext'
import { useSearchContext } from '../../contexts/SearchContext'
import SearchResults from '../Search/SearchResults'

interface Message {
  id: string
  text: string
  sender: 'user' | 'assistant'
  timestamp: Date
}

const ChatPanel: React.FC = () => {
  const { user } = useAuth()
  const { search, results, total, isLoading: searchLoading, error, parsedQuery, metrics } = useSearchContext()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Welcome to OrbitAgents! I can help you search for properties. Try asking me something like "3 bedroom house under $600k" or "apartment near downtown with parking".',
      sender: 'assistant',
      timestamp: new Date()
    }
  ])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputText.trim() || isLoading || searchLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText.trim(),
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const query = inputText.trim()
    setInputText('')
    setIsLoading(true)

    try {
      // Perform the search
      await search(query, 10)
      
      // Create assistant response based on search results
      let assistantText = ''
      
      if (error) {
        assistantText = `I encountered an error while searching: ${error}. Please try rephrasing your query.`
      } else if (parsedQuery) {
        const confidence = Math.round(parsedQuery.confidence * 100)
        let parseInfo = `I understood you're looking for `
        
        const criteria = []
        if (parsedQuery.beds) criteria.push(`${parsedQuery.beds} bedroom${parsedQuery.beds > 1 ? 's' : ''}`)
        if (parsedQuery.property_type) criteria.push(parsedQuery.property_type)
        if (parsedQuery.city) criteria.push(`in ${parsedQuery.city}`)
        if (parsedQuery.max_price) criteria.push(`under $${parsedQuery.max_price.toLocaleString()}`)
        if (parsedQuery.has_parking) criteria.push('with parking')
        
        if (criteria.length > 0) {
          parseInfo += criteria.join(', ')
        } else {
          parseInfo += 'properties'
        }
        
        parseInfo += ` (${confidence}% confidence).`
        
        if (results.length > 0) {
          assistantText = `${parseInfo} I found ${total} matching properties! Showing the top ${results.length} results below.`
        } else {
          assistantText = `${parseInfo} Unfortunately, I didn't find any properties matching your criteria. Try adjusting your search terms or expanding your area.`
        }
        
        if (metrics) {
          assistantText += ` (Search completed in ${metrics.total_time_ms.toFixed(0)}ms)`
        }
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: assistantText,
        sender: 'assistant',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
      
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an unexpected error while processing your search. Please try again.',
        sender: 'assistant',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <h1 className="text-lg font-semibold text-gray-900">OrbitAgents Chat</h1>
        {user && (
          <p className="text-sm text-gray-500">Logged in as {user.email}</p>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.sender === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white border border-gray-200 text-gray-900'
              }`}
            >
              <p className="text-sm">{message.text}</p>
              <p
                className={`text-xs mt-1 ${
                  message.sender === 'user' ? 'text-blue-100' : 'text-gray-500'
                }`}
              >
                {formatTime(message.timestamp)}
              </p>
            </div>
          </div>
        ))}
        
        {(isLoading || searchLoading) && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 text-gray-900 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-sm text-gray-500">
                  {searchLoading ? 'Searching properties...' : 'Assistant is typing...'}
                </span>
              </div>
            </div>
          </div>
        )}
        
        {/* Search Results */}
        {results.length > 0 && (
          <div className="mt-4">
            <SearchResults 
              results={results}
              total={total}
              isLoading={searchLoading}
              error={error}
            />
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-4">
        <form onSubmit={handleSendMessage} className="flex space-x-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ask me anything..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !inputText.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PaperAirplaneIcon className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  )
}

export default ChatPanel 