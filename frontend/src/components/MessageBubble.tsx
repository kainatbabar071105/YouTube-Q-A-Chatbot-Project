import React from 'react';
import { Message } from '../types';

interface Props {
  message: Message;
}

const renderInlineText = (text: string) => {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) =>
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={index}>{part.slice(2, -2)}</strong>
      : part
  );
};

const renderMessage = (content: string) => content.split('\n').map((line, index) => {
  const trimmedLine = line.trim();
  if (!trimmedLine) return <div className="message-spacer" key={index} />;

  if (trimmedLine.startsWith('### ')) {
    return <h3 key={index}>{renderInlineText(trimmedLine.slice(4))}</h3>;
  }

  if (/^[-*] /.test(trimmedLine)) {
    return <div className="message-bullet" key={index}><span>•</span>{renderInlineText(trimmedLine.slice(2))}</div>;
  }

  return <div key={index}>{renderInlineText(line)}</div>;
});

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`message-row ${isUser ? 'user-row' : 'assistant-row'}`}>
      {!isUser && <div className="assistant-avatar">Q</div>}
      <div className={`message-content ${isUser ? 'user-message' : 'assistant-message'}`}>
        <div className="message-meta">{isUser ? 'You' : 'Lumen'} <span>{isUser ? 'QUESTION' : 'SYNTHESIS'}</span></div>
        <div className="message-text">{renderMessage(message.content)}</div>
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="source-list"><div className="source-heading">Best matching video <span>01</span></div><ul>
              {message.sources.map((url, idx) => (
                <li key={idx}>
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-link"
                  >
                    <span className="source-index">01</span> Open video source <span className="source-arrow">↗</span>
                  </a>
                </li>
              ))}
            </ul></div>
        )}
      </div>
    </div>
  );
};