import React, { useState, useRef, useEffect } from 'react';
import { Message } from '../types';
import { MessageBubble } from './MessageBubble';
import { askQuestion } from '../services/api';

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const promptSuggestions = [
    'Give me the key ideas in these videos',
    'What practical advice comes up most often?',
    'Compare the different perspectives',
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const { answer, sources } = await askQuestion(input);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: answer,
        sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error asking question:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '❌ Sorry, something went wrong. Please try again later.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const useSuggestion = (suggestion: string) => {
    setInput(suggestion);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <main className="chat-layout">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true"><span>Q</span></div>
          <div><div className="brand-name">Lumen / Q&amp;A</div><div className="brand-status"><span className="status-dot" /> Your video library, illuminated</div></div>
        </div>
        <div className="topbar-note"><span className="pulse-line" /> AI research companion</div>
      </header>
      <section className="conversation-panel">
        <div className="conversation-intro"><div className="eyebrow">Knowledge, made conversational</div><h1>Find the signal<br /><em>in the noise.</em></h1><p>Ask a question across your video collection. Lumen pulls together the most useful ideas, context, and sources.</p></div>
        <div className="message-scroll">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-orbit" aria-hidden="true"><span>?</span></div>
            <div className="empty-copy"><span className="empty-kicker">Start with a spark</span><h2>What are you curious about?</h2><p>Try one of these to open a thread.</p></div>
            <div className="suggestions">{promptSuggestions.map((suggestion) => <button key={suggestion} onClick={() => useSuggestion(suggestion)} className="suggestion-card"><span>{suggestion}</span><span className="arrow" aria-hidden="true">↗</span></button>)}</div>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))
        )}
        {isLoading && (
          <div className="loading-message"><div className="assistant-avatar">Q</div><div className="loading-bubble"><span /> <span /> <span /><b>Thinking through the library</b></div>
          </div>
        )}
        <div ref={messagesEndRef} />
        </div>
        <div className="composer-wrap"><div className="composer-hint"><span>⌘</span> Ask anything about the videos</div><div className="composer"><textarea rows={1} placeholder="What should we explore?" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyPress} disabled={isLoading} /><button onClick={handleSend} disabled={isLoading || !input.trim()} className="send-button" aria-label="Send question"><span>Send</span><span className="send-arrow" aria-hidden="true">↗</span></button></div><div className="composer-footer"><span>Responses are grounded in your indexed transcripts.</span><span>Enter to send <i>•</i> Shift + Enter for a new line</span></div></div>
      </section>
      <footer className="page-footer"><span>LUMEN</span><span>Thoughtful answers from your own library</span><span>v1.0 / private workspace</span></footer>
    </main>
  );
};