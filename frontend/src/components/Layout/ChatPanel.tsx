import React, { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useSearchContext } from '../../contexts/useSearchContext';
import SearchResults from '../Search/SearchResults';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

const ChatPanel: React.FC = () => {
  const { user, logout } = useAuth();
  const {
    search,
    results,
    total,
    isLoading: searchLoading,
  } = useSearchContext();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Welcome to OrbitAgents! I can help you search for properties. Try asking me something like "3 bedroom house under $600k" or "apartment near downtown with parking".',
      sender: 'assistant',
      timestamp: new Date(),
    },
  ]);
  const draftKey = `orbit-search-draft:${user?.id || user?.email || 'anonymous'}`;
  const [draftWarning, setDraftWarning] = useState('');
  const [inputText, setInputText] = useState(() => {
    try {
      return localStorage.getItem(draftKey)?.slice(0, 500) || '';
    } catch {
      return '';
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem(draftKey, inputText);
      setDraftWarning('');
    } catch {
      setDraftWarning('Draft could not be saved on this device.');
    }
  }, [inputText, draftKey]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading || searchLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText.trim(),
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const query = inputText.trim();
    setInputText('');
    setIsLoading(true);

    try {
      // Perform the search
      const response = await search(query);
      if (!response) throw new Error('Search service returned no data.');
      const {
        listings: currentResults,
        total: currentTotal,
        parse: parsedQuery,
      } = response;

      // Create assistant response based on search results
      let assistantText = '';

      if (parsedQuery) {
        const confidence = Math.round(parsedQuery.confidence * 100);
        let parseInfo = `I understood you're looking for `;

        const criteria = [];
        if (parsedQuery.beds)
          criteria.push(
            `${parsedQuery.beds} bedroom${parsedQuery.beds > 1 ? 's' : ''}`
          );
        if (parsedQuery.property_type) criteria.push(parsedQuery.property_type);
        if (parsedQuery.city) criteria.push(`in ${parsedQuery.city}`);
        if (parsedQuery.max_price)
          criteria.push(`under $${parsedQuery.max_price.toLocaleString()}`);
        if (parsedQuery.has_parking) criteria.push('with parking');

        if (criteria.length > 0) {
          parseInfo += criteria.join(', ');
        } else {
          parseInfo += 'properties';
        }

        parseInfo += ` (${confidence}% confidence).`;

        if (currentResults.length > 0) {
          assistantText = `${parseInfo} I found ${currentTotal} matching properties! Showing the top ${currentResults.length} results below.`;
        } else {
          assistantText = `${parseInfo} Unfortunately, I didn't find any properties matching your criteria. Try adjusting your search terms or expanding your area.`;
        }

        assistantText += ` (Search completed in ${response.total_time_ms.toFixed(0)}ms)`;
      } else {
        assistantText = `Found ${currentTotal} matching properties. Showing ${currentResults.length} results.`;
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: assistantText,
        sender: 'assistant',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Search unavailable: ${err instanceof Error ? err.message : 'Please try again.'}`,
        sender: 'assistant',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white p-4">
        <h1 className="text-lg font-semibold text-gray-900">
          OrbitAgents Chat
        </h1>
        {user && (
          <p className="text-sm text-gray-500">Logged in as {user.email}</p>
        )}
      </div>

      <button
        onClick={logout}
        className="self-start px-4 py-2 text-sm text-blue-700"
      >
        Sign out
      </button>
      {/* Messages */}
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs rounded-lg px-4 py-2 lg:max-w-md ${
                message.sender === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'border border-gray-200 bg-white text-gray-900'
              }`}
            >
              <p className="text-sm">{message.text}</p>
              <p
                className={`mt-1 text-xs ${
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
            <div className="max-w-xs rounded-lg border border-gray-200 bg-white px-4 py-2 text-gray-900 lg:max-w-md">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400"></div>
                  <div
                    className="h-2 w-2 animate-bounce rounded-full bg-gray-400"
                    style={{ animationDelay: '0.1s' }}
                  ></div>
                  <div
                    className="h-2 w-2 animate-bounce rounded-full bg-gray-400"
                    style={{ animationDelay: '0.2s' }}
                  ></div>
                </div>
                <span className="text-sm text-gray-500">
                  {searchLoading
                    ? 'Searching properties...'
                    : 'Assistant is typing...'}
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
            />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white p-4">
        {draftWarning && (
          <p role="status" className="mb-2 text-xs text-amber-700">
            {draftWarning}
          </p>
        )}
        <form onSubmit={handleSendMessage} className="flex space-x-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ask me anything..."
            aria-label="Property search"
            maxLength={500}
            className="min-w-0 flex-1 rounded-md border border-gray-300 px-3 py-2 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            aria-label="Search properties"
            disabled={isLoading || !inputText.trim()}
            className="rounded-md bg-blue-500 px-4 py-2 text-white hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <PaperAirplaneIcon className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatPanel;
