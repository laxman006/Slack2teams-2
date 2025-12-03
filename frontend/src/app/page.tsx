'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

// Extend Window interface for marked.js
declare global {
  interface Window {
    marked?: {
      parse: (text: string) => string;
    };
    copyMessage?: (button: HTMLElement) => void;
    submitFeedback?: (button: HTMLElement, rating: string) => void;
    editMessage?: (button: HTMLElement) => void;
    cancelEdit?: (button: HTMLElement) => void;
    saveEdit?: (button: HTMLElement) => void;
    askRecommendedQuestion?: (button: HTMLElement) => void;
    showFeedbackModal?: (messageDiv: HTMLElement, traceId: string) => void;
    submitDetailedFeedback?: () => void;
    copyUserMessage?: (button: HTMLElement) => void;
  }
}

export default function ChatPage() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Verify token with Microsoft Graph API
  const verifyToken = useCallback(async (accessToken: string): Promise<boolean> => {
    try {
      const response = await fetch('https://graph.microsoft.com/v1.0/me', {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        },
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });
      return response.ok;
    } catch (error) {
      console.error('[AUTH] Token verification failed:', error);
      return false;
    }
  }, []);

  // Authentication check BEFORE rendering
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Check localStorage for existing user
        const userStr = localStorage.getItem('user');
        
        if (!userStr) {
          console.log('[AUTH] No user found, redirecting to login');
          router.push('/login');
          return;
        }

        const user = JSON.parse(userStr);
        
        if (!user.access_token) {
          console.log('[AUTH] No access token found, redirecting to login');
          localStorage.removeItem('user');
          router.push('/login');
          return;
        }

        // Verify token is still valid with Microsoft Graph
        console.log('[AUTH] Verifying access token...');
        const isValid = await verifyToken(user.access_token);
        
        if (!isValid) {
          console.log('[AUTH] Token is invalid or expired, redirecting to login');
          localStorage.removeItem('user');
          router.push('/login?error=session_expired');
          return;
        }

        // Check if user email is from cloudfuze.com
        if (!user.email || !user.email.endsWith('@cloudfuze.com')) {
          console.log('[AUTH] Non-CloudFuze email detected, redirecting to login');
          localStorage.removeItem('user');
          router.push('/login?error=unauthorized_domain&email=' + encodeURIComponent(user.email || ''));
          return;
        }

        // All checks passed - user is authenticated
        console.log('[AUTH] User authenticated successfully:', user.email);
        setIsAuthenticated(true);
        setIsLoading(false);
        
      } catch (error) {
        console.error('[AUTH] Authentication check failed:', error);
        localStorage.removeItem('user');
        router.push('/login?error=verification_failed');
      }
    };

    checkAuth();
  }, [router, verifyToken]);

  // Initialize chat app ONLY after authentication is confirmed
  useEffect(() => {
    if (isAuthenticated) {
    // Wait for marked.js to load
    const checkMarked = setInterval(() => {
      if (typeof window.marked !== 'undefined') {
        clearInterval(checkMarked);
        initializeChatApp();
      }
    }, 100);

    return () => clearInterval(checkMarked);
    }
  }, [isAuthenticated]);

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'white',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{
          width: '50px',
          height: '50px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #0129ac',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
        <p style={{ 
          marginTop: '20px', 
          color: '#666',
          fontSize: '16px'
        }}>
          Verifying authentication...
        </p>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Don't render anything if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  // Only render chat interface if user is authenticated  

  return (
    <div className="chatgpt-container">
      {/* ChatGPT-Style Sidebar */}
      <aside className={`chatgpt-sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="sidebar-top-row">
            <button 
              className="sidebar-icon" 
              onClick={() => window.location.reload()}
              title="Reload page"
              style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}
            >
              <Image 
                src="/images/CloudFuze-icon-64x64.png" 
                alt="CloudFuze" 
                width={42} 
                height={42} 
                priority 
              />
            </button>
            <button 
              className="sidebar-toggle-btn-new" 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              title={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
              </svg>
            </button>
          </div>
          
          <button className="new-chat-btn-sidebar" id="newChatBtn" title="New chat">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            <span className="btn-text">New chat</span>
          </button>
        </div>
        
        <div id="sidebar-history" className="sidebar-history">
          {/* Chat history will be populated here */}
        </div>
        
        <div className="sidebar-footer">
          <div className="sidebar-user" id="userMenu">
            <div className="user-avatar" id="userAvatar">U</div>
            <div className="user-details">
              <span className="user-name" id="userName">User</span>
              <span className="user-email-small" id="userEmailSidebar"></span>
            </div>
            <div className="user-dropdown-sidebar" id="userDropdown">
              <div className="dropdown-item" id="userEmail"></div>
              <div className="dropdown-item logout" id="logoutBtn">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M7 19H3a2 2 0 01-2-2V3a2 2 0 012-2h4"/>
                  <path d="M14 15l5-5-5-5"/>
                  <line x1="19" y1="10" x2="7" y2="10"/>
                </svg>
                <span>Log out</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* ChatGPT-Style Main Content */}
      <main className="chatgpt-main">
        {/* Top Logo */}
        <div className="main-header">
          <Image 
            src="/images/CloudFuze Horizontal Logo.svg" 
            alt="CloudFuze" 
            width={200} 
            height={52} 
            priority 
          />
        </div>

        {/* Messages Container */}
        <div className="messages-container">
          {/* Empty State - Shows when no messages */}
          <div id="empty-state" className="empty-state">
            <div className="empty-state-content">
              {/* Welcome Message */}
              <div className="welcome-section">
                <h1 className="welcome-title">How can I help you today?</h1>
              </div>

              {/* Input Section for Empty State */}
              <div className="empty-state-input">
                <div className="input-wrapper-chatgpt">
                  <textarea
                    id="user-input-empty"
                    className="chatgpt-textarea"
                    placeholder="Ask me anything about CloudFuze..."
                    rows={1}
                  />
                  <button id="send-btn-empty" className="chatgpt-send-btn">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M8 1a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L7 12.586V2a1 1 0 011-1z" transform="rotate(180 8 8)"/>
                    </svg>
                  </button>
                </div>
                {/* Suggested Questions */}
                <div className="suggested-questions-container">
                  <button className="suggested-question-btn" data-question="How do I migrate data from Slack to Microsoft Teams?">
                    How do I migrate data from Slack to Microsoft Teams?
                  </button>
                  <button className="suggested-question-btn" data-question="What are the best practices for cloud migration?">
                    What are the best practices for cloud migration?
                  </button>
                  <button className="suggested-question-btn" data-question="How can I track migration progress?">
                    How can I track migration progress?
                  </button>
                  <button className="suggested-question-btn" data-question="What are the key features of CloudFuze?">
                    What are the key features of CloudFuze?
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Messages List */}
          <div id="messages" className="messages-list"></div>
      </div>

        {/* Scroll to Bottom Button */}
        <button id="scroll-to-bottom-btn" className="scroll-to-bottom" title="Scroll to bottom">
          <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 3a1 1 0 011 1v10.586l3.293-3.293a1 1 0 111.414 1.414l-5 5a1 1 0 01-1.414 0l-5-5a1 1 0 111.414-1.414L9 14.586V4a1 1 0 011-1z"/>
        </svg>
      </button>

      {/* Feedback Modal */}
      <div id="feedback-modal" className="feedback-modal-overlay">
        <div className="feedback-modal">
          <div className="feedback-modal-header">
            <h3>Provide additional feedback</h3>
            <button className="feedback-modal-close" id="feedback-modal-close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"/>
              </svg>
            </button>
          </div>
          <div className="feedback-modal-body">
            <div className="feedback-categories">
              <button className="feedback-category-btn" data-category="Incorrect">
                Incorrect
              </button>
              <button className="feedback-category-btn" data-category="Irrelevant/Out of context">
                Irrelevant/Out of context
              </button>
              <button className="feedback-category-btn" data-category="Partially correct">
                Partially correct
              </button>
              <button className="feedback-category-btn" data-category="Too generic/not Specific">
                Too generic/not Specific
              </button>
              <button className="feedback-category-btn" data-category="Restricted response">
                Restricted response
              </button>
              <button className="feedback-category-btn" data-category="Too verbose">
                Too verbose
              </button>
              <button className="feedback-category-btn" data-category="Other">
                Other
              </button>
            </div>
            <textarea 
              id="feedback-comment" 
              className="feedback-comment-textarea" 
              placeholder="(Optional) Feel free to add specific details"
              rows={3}
            ></textarea>
            <div className="feedback-modal-note">
              Submitting feedback will include this full conversation to help improve CloudFuze AI.
            </div>
          </div>
          <div className="feedback-modal-footer">
            <button className="feedback-submit-btn" id="feedback-submit-btn">
              Submit
            </button>
          </div>
        </div>
      </div>

        {/* ChatGPT-Style Input Section - Shows when there are messages */}
        <div className="chatgpt-input-section">
          <div className="input-container-inner">
            <div className="input-wrapper-chatgpt">
              <textarea
                ref={textareaRef}
                id="user-input"
                className="chatgpt-textarea"
                placeholder="Ask me anything about CloudFuze..."
                rows={1}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = '24px';
                  target.style.height = Math.min(target.scrollHeight, 200) + 'px';
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    const sendBtn = document.getElementById('send-btn') as HTMLButtonElement;
                    if (sendBtn) sendBtn.click();
                  }
                }}
              />
              <button id="send-btn" className="chatgpt-send-btn">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 1a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L7 12.586V2a1 1 0 011-1z" transform="rotate(180 8 8)"/>
                </svg>
          </button>
            </div>
            {/* Suggested Questions */}
            <div className="suggested-questions-container">
              <button className="suggested-question-btn" data-question="How do I migrate data from Slack to Microsoft Teams?">
                How do I migrate data from Slack to Microsoft Teams?
              </button>
              <button className="suggested-question-btn" data-question="What are the best practices for cloud migration?">
                What are the best practices for cloud migration?
              </button>
              <button className="suggested-question-btn" data-question="How can I track migration progress?">
                How can I track migration progress?
              </button>
              <button className="suggested-question-btn" data-question="What are the key features of CloudFuze?">
                What are the key features of CloudFuze?
              </button>
            </div>
            <p className="input-disclaimer">CloudFuze AI can make mistakes. Check important info.</p>
          </div>
        </div>
      </main>
    </div>
  );
}

function initializeChatApp() {
  // API Base URL configuration
  function getApiBase() {
    const hostname = window.location.hostname;
    
    // Development environment
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8002';
    }
    
    // Production environments
    if (hostname === 'ai.cloudfuze.com') {
      return 'https://ai.cloudfuze.com';
    }
    
    // Default fallback - use current origin
    return window.location.origin;
  }

  const messagesDiv = document.getElementById("messages");
  const input = document.getElementById("user-input") as HTMLTextAreaElement;
  const sendBtn = document.getElementById("send-btn");
  const emptyState = document.getElementById("empty-state");
  const inputEmptyState = document.getElementById("user-input-empty") as HTMLTextAreaElement;
  const sendBtnEmptyState = document.getElementById("send-btn-empty");
  const inputSection = document.querySelector(".chatgpt-input-section") as HTMLElement;

  // Hide empty state when messages exist
  function updateEmptyState() {
    if (messagesDiv && emptyState && inputSection) {
      const hasMessages = messagesDiv.children.length > 0;
      emptyState.style.display = hasMessages ? 'none' : 'flex';
      messagesDiv.style.display = hasMessages ? 'block' : 'none';
      
      // Show/hide suggested questions based on message state
      const emptyStateQuestions = emptyState.querySelector('.suggested-questions-container') as HTMLElement;
      const inputSectionQuestions = inputSection.querySelector('.suggested-questions-container') as HTMLElement;
      
      if (emptyStateQuestions) {
        emptyStateQuestions.style.display = hasMessages ? 'none' : 'grid';
      }
      // Always hide suggested questions in bottom input section - only show in empty state
      if (inputSectionQuestions) {
        inputSectionQuestions.style.display = 'none';
      }
      
      // Show bottom input only when there are messages
      if (hasMessages) {
        inputSection.classList.add('show');
      } else {
        inputSection.classList.remove('show');
      }
    }
  }
  
  // Session management
  let sessionId = localStorage.getItem('chatbot_session_id');
  let currentSessionTitle = '';
  
  interface ChatSession {
    id: string;
    title: string;
    timestamp: number;
    messages: Array<{role: string, content: string, recommendedQuestions?: string[]}>;
  }
  
  function createNewSession(): string {
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const randomId = Math.random().toString(36).substr(2, 9);
    return `cf.conversation.${date}.${randomId}`;
  }
  
  // Initialize or create session
  if (!sessionId) {
    sessionId = createNewSession();
    localStorage.setItem('chatbot_session_id', sessionId);
    console.log('[SESSION] Created new session:', sessionId);
  }
  
  // Load all sessions from localStorage
  function getAllSessions(): ChatSession[] {
    try {
      const sessionsStr = localStorage.getItem('chat_sessions');
      return sessionsStr ? JSON.parse(sessionsStr) : [];
    } catch (e) {
      console.error('[SESSIONS] Failed to load sessions:', e);
      return [];
    }
  }
  
  // Save all sessions to localStorage
  function saveAllSessions(sessions: ChatSession[]) {
    try {
      localStorage.setItem('chat_sessions', JSON.stringify(sessions));
    } catch (e) {
      console.error('[SESSIONS] Failed to save sessions:', e);
    }
  }
  
  // Save current session
  function saveCurrentSession(title?: string) {
    const sessions = getAllSessions();
    const messages = Array.from(messagesDiv!.children).map((child, index) => {
      const isUser = child.classList.contains('user-message-wrapper') || 
                     child.querySelector('.message.user');
      
      if (isUser) {
        const content = (child.querySelector('.message.user') as HTMLElement)?.textContent || '';
        return {
          role: 'user',
          content: content
        };
      } else {
        // Bot message - capture content and recommended questions
        const messageContentDiv = child.querySelector('.message-content') as HTMLElement;
        const content = messageContentDiv?.innerHTML || '';
        const recommendedQuestionsDiv = child.querySelector('.recommended-questions');
        const recommendedQuestions: string[] = [];
        
        console.log(`[SESSION SAVE] Processing bot message ${index}, has .recommended-questions:`, !!recommendedQuestionsDiv);
        
        if (recommendedQuestionsDiv) {
          const questionBtns = recommendedQuestionsDiv.querySelectorAll('.recommended-question-btn');
          console.log(`[SESSION SAVE] Found ${questionBtns.length} question buttons`);
          questionBtns.forEach(btn => {
            const question = btn.getAttribute('data-question');
            if (question) {
              recommendedQuestions.push(question);
              console.log(`[SESSION SAVE] Captured question: "${question}"`);
            }
          });
        }
        
        const result = {
          role: 'assistant',
          content: content,
          recommendedQuestions: recommendedQuestions.length > 0 ? recommendedQuestions : undefined
        };
        
        if (result.recommendedQuestions) {
          console.log('[SESSION SAVE] Saving', result.recommendedQuestions.length, 'recommended questions with message');
        }
        
        return result;
      }
    });
    
    if (messages.length === 0) return;
    
    // Generate title from first user message if not provided
    const sessionTitle = title || currentSessionTitle || messages[0]?.content.substring(0, 50) || 'New Chat';
    currentSessionTitle = sessionTitle;
    
    const existingIndex = sessions.findIndex(s => s.id === sessionId);
    const sessionData: ChatSession = {
      id: sessionId!,
      title: sessionTitle,
      timestamp: Date.now(),
      messages: messages
    };
    
    // Log what we're about to save
    const questionsCount = messages.filter(m => m.role === 'assistant' && 'recommendedQuestions' in m && m.recommendedQuestions).length;
    console.log(`[SESSION SAVE] Saving session with ${messages.length} messages, ${questionsCount} have recommended questions`);
    
    if (existingIndex >= 0) {
      sessions[existingIndex] = sessionData;
    } else {
      sessions.unshift(sessionData);
    }
    
    // Keep only last 50 sessions
    if (sessions.length > 50) {
      sessions.splice(50);
    }
    
    saveAllSessions(sessions);
    renderSessionHistory();
  }
  
  // Load a specific session
  function loadSession(sessionData: ChatSession) {
    console.log('[SESSION] Loading session:', sessionData.id, 'with', sessionData.messages.length, 'messages');
    sessionId = sessionData.id;
    currentSessionTitle = sessionData.title;
    localStorage.setItem('chatbot_session_id', sessionId);
    
    // Clear current messages
    messagesDiv!.innerHTML = '';
    
    // Load session messages
    sessionData.messages.forEach((msg, index) => {
      if (msg.role === 'user') {
        addMessage(msg.content, 'user');
      } else {
        // Bot message with optional recommended questions
        const isLastMessage = index === sessionData.messages.length - 1;
        const hasRecommendations = msg.recommendedQuestions && msg.recommendedQuestions.length > 0;
        const showRecommendations = isLastMessage && hasRecommendations;
        
        if (showRecommendations) {
          console.log('[SESSION] Restoring', msg.recommendedQuestions!.length, 'recommended questions for last message');
        }
        
        const recommendedQuestionsHTML = showRecommendations 
          ? buildRecommendedQuestionsHTML(msg.recommendedQuestions!) 
          : '';
        
        const div = document.createElement("div");
        div.className = "message bot";
        div.innerHTML = `
          <div class="message-content">${msg.content}</div>
          <div class="feedback-buttons">
            <button class="copy-button" onclick="window.copyMessage(this)" title="Copy message">
              <img src="/images/copy-icon.svg?v=2" alt="Copy" width="16" height="16">
            </button>
            <button class="feedback-btn thumbs-up" onclick="window.submitFeedback(this, 'thumbs_up')" title="Good response">
              <img src="/images/thumbs-up-icon.svg?v=2" alt="Thumbs up" width="16" height="16">
            </button>
            <button class="feedback-btn thumbs-down" onclick="window.submitFeedback(this, 'thumbs_down')" title="Bad response">
              <img src="/images/thumbs-down-icon.svg?v=2" alt="Thumbs down" width="16" height="16">
            </button>
            <span class="feedback-text"></span>
          </div>
          ${recommendedQuestionsHTML}
        `;
        messagesDiv!.appendChild(div);
      }
    });
    
    updateEmptyState();
    scrollToBottom();
  }
  
  // Render session history in sidebar
  function renderSessionHistory() {
    const sidebarHistory = document.getElementById('sidebar-history');
    if (!sidebarHistory) return;
    
    const sessions = getAllSessions();
    
    if (sessions.length === 0) {
      sidebarHistory.innerHTML = '<div class="no-history">No chat history yet</div>';
      return;
    }
    
    const now = Date.now();
    const oneDay = 24 * 60 * 60 * 1000;
    const sevenDays = 7 * oneDay;
    const thirtyDays = 30 * oneDay;
    
    const today: ChatSession[] = [];
    const yesterday: ChatSession[] = [];
    const lastWeek: ChatSession[] = [];
    const lastMonth: ChatSession[] = [];
    const older: ChatSession[] = [];
    
    sessions.forEach(session => {
      const age = now - session.timestamp;
      if (age < oneDay) today.push(session);
      else if (age < 2 * oneDay) yesterday.push(session);
      else if (age < sevenDays) lastWeek.push(session);
      else if (age < thirtyDays) lastMonth.push(session);
      else older.push(session);
    });
    
    let html = '';
    
    function renderSection(title: string, sessions: ChatSession[]) {
      if (sessions.length === 0) return '';
      let section = `<div class="history-section-title">${title}</div>`;
      sessions.forEach(session => {
        const isActive = session.id === sessionId;
        section += `
          <div class="history-item ${isActive ? 'active' : ''}" data-session-id="${session.id}">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span class="history-item-title">${session.title}</span>
            <button class="history-item-delete" data-session-id="${session.id}" title="Delete chat">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>
          </div>
        `;
      });
      return section;
    }
    
    html += renderSection('Today', today);
    html += renderSection('Yesterday', yesterday);
    html += renderSection('Previous 7 Days', lastWeek);
    html += renderSection('Previous 30 Days', lastMonth);
    html += renderSection('Older', older);
    
    sidebarHistory.innerHTML = html;
    
    // Add click handlers
    sidebarHistory.querySelectorAll('.history-item').forEach(item => {
      const sessionEl = item as HTMLElement;
      const sid = sessionEl.dataset.sessionId;
      
      sessionEl.addEventListener('click', (e) => {
        const target = e.target as HTMLElement;
        if (target.closest('.history-item-delete')) return;
        
        const session = sessions.find(s => s.id === sid);
        if (session) {
          loadSession(session);
        }
      });
    });
    
    // Add delete handlers
    sidebarHistory.querySelectorAll('.history-item-delete').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const sid = (btn as HTMLElement).dataset.sessionId;
        deleteSession(sid!);
      });
    });
  }
  
  // Delete a session
  function deleteSession(sid: string) {
    if (!confirm('Delete this chat?')) return;
    
    let sessions = getAllSessions();
    sessions = sessions.filter(s => s.id !== sid);
    saveAllSessions(sessions);
    
    // If deleted current session, create new one
    if (sid === sessionId) {
      handleNewChat();
    } else {
      renderSessionHistory();
    }
  }

  // Helper functions for persisting recommended questions
  function saveRecommendedQuestions(messageIndex: number, questions: string[]) {
    try {
      const storageKey = `recommended_questions_${sessionId}`;
      const stored = localStorage.getItem(storageKey);
      const recommendations = stored ? JSON.parse(stored) : {};
      recommendations[messageIndex] = questions;
      localStorage.setItem(storageKey, JSON.stringify(recommendations));
    } catch (e) {
      console.error('[STORAGE] Failed to save recommendations:', e);
    }
  }

  function loadRecommendedQuestions(messageIndex: number): string[] {
    try {
      const storageKey = `recommended_questions_${sessionId}`;
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        const recommendations = JSON.parse(stored);
        return recommendations[messageIndex] || [];
      }
    } catch (e) {
      console.error('[STORAGE] Failed to load recommendations:', e);
    }
    return [];
  }

  function clearRecommendedQuestions() {
    try {
      const storageKey = `recommended_questions_${sessionId}`;
      localStorage.removeItem(storageKey);
    } catch (e) {
      console.error('[STORAGE] Failed to clear recommendations:', e);
    }
  }

  function buildRecommendedQuestionsHTML(questions: string[]): string {
    if (!questions || questions.length === 0) {
      return '';
    }
    
    const questionsHTML = questions
      .map((q: string) => `
        <button class="recommended-question-btn" onclick="window.askRecommendedQuestion(this)" data-question="${q.replace(/"/g, '&quot;')}">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 10 L12 10 M10 7 L13 10 L10 13" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>${q}</span>
        </button>
      `)
      .join('');
    
    return `
      <div class="recommended-questions">
        <div class="recommended-questions-label">Related</div>
        <div class="recommended-questions-list">
          ${questionsHTML}
        </div>
      </div>
    `;
  }

  // Helper function to remove edit button from previous user messages
  function removeAllEditButtons() {
    const allWrappers = messagesDiv!.querySelectorAll('.user-message-wrapper');
    allWrappers.forEach(wrapper => {
      const editContainer = wrapper.querySelector('.edit-button-container');
      if (editContainer) {
        editContainer.remove();
      }
    });
  }

  // Toast notification function
  function showToast(message: string) {
    // Remove existing toast if any
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
      existingToast.remove();
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => {
      toast.classList.add('show');
    }, 10);
    
    // Remove after 2 seconds
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => {
        toast.remove();
      }, 300);
    }, 2000);
  }

  function addMessage(content: string, sender: string) {
    if (sender === "user") {
      // Remove edit button from any previous user messages
      removeAllEditButtons();
      
      // For user messages, create wrapper with message and edit button below
      const wrapper = document.createElement("div");
      wrapper.className = "user-message-wrapper";
      wrapper.innerHTML = `
        <div class="message user">${content}</div>
        <div class="edit-button-container">
          <button class="copy-button-user" onclick="window.copyUserMessage(this)" title="Copy message">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
          <button class="edit-btn" onclick="window.editMessage(this)" title="Edit message">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path>
            </svg>
          </button>
        </div>
      `;
      messagesDiv!.appendChild(wrapper);
      console.log(`[UI] Added ${sender} message. Total messages now: ${messagesDiv!.children.length}`);
      updateEmptyState();
      autoScrollToBottom();
      return wrapper;
    } else {
      // For bot messages, keep simple structure
      const div = document.createElement("div");
      div.className = "message " + sender;
      div.innerText = content;
      messagesDiv!.appendChild(div);
      console.log(`[UI] Added ${sender} message. Total messages now: ${messagesDiv!.children.length}`);
      updateEmptyState();
      autoScrollToBottom();
      return div;
    }
  }

  function addMessageHTML(content: string, sender: string, traceId: string | null = null) {
    const div = document.createElement("div");
    div.className = "message " + sender;
    
    if (sender === "bot") {
      // For bot messages, wrap content and add copy button + feedback buttons
      div.innerHTML = `
        <div class="message-content">${content}</div>
        <div class="feedback-buttons">
          <button class="copy-button" onclick="window.copyMessage(this)" title="Copy message">
            <img src="/images/copy-icon.svg?v=2" alt="Copy" width="16" height="16">
          </button>
          <button class="feedback-btn thumbs-up" onclick="window.submitFeedback(this, 'thumbs_up')" title="Good response">
            <img src="/images/thumbs-up-icon.svg?v=2" alt="Thumbs up" width="16" height="16">
          </button>
          <button class="feedback-btn thumbs-down" onclick="window.submitFeedback(this, 'thumbs_down')" title="Bad response">
            <img src="/images/thumbs-down-icon.svg?v=2" alt="Thumbs down" width="16" height="16">
          </button>
          <span class="feedback-text"></span>
        </div>
      `;
      
      // Store trace_id if provided
      if (traceId) {
        div.dataset.traceId = traceId;
      }
    } else {
      // For user messages, keep as is
      div.innerHTML = content;
    }
    
    messagesDiv!.appendChild(div);
    console.log(`[UI] Added ${sender} message HTML. Total messages now: ${messagesDiv!.children.length}`);
    updateEmptyState();
    autoScrollToBottom();
    return div;
  }

  function renderMarkdown(text: string) {
    let html = '';
    if (typeof window.marked !== 'undefined') {
      html = window.marked.parse(text);
    } else {
      // Fallback: basic markdown-like formatting
      html = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/^\* (.*$)/gim, '<li>$1</li>')
        .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
        .replace(/\n/g, '<br>');
    }
    
    // Add target="_blank" and rel="noopener noreferrer" to all links
    html = html.replace(/<a href=/g, '<a target="_blank" rel="noopener noreferrer" href=');
    
    return html;
  }

  // [REST OF THE JAVASCRIPT CODE WILL CONTINUE IN NEXT MESSAGE DUE TO LENGTH]
  // For now, let me create a simplified version that makes it work

  // Check if user is near bottom of messages
  function isUserNearBottom(): boolean {
    const messagesContainer = document.querySelector('.messages-container') as HTMLElement;
    if (!messagesContainer) return true;
    
    const threshold = 150;
    const isNearBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < threshold;
    return isNearBottom;
  }

  // Scroll to bottom (forced - used when user clicks button)
  function scrollToBottom() {
    requestAnimationFrame(() => {
      const messagesContainer = document.querySelector('.messages-container') as HTMLElement;
      if (messagesContainer) {
        messagesContainer.scrollTo({
          top: messagesContainer.scrollHeight,
        behavior: 'smooth'
      });
      }
    });
  }

  // Auto-scroll only if user is already near bottom (ChatGPT behavior)
  function autoScrollToBottom() {
    if (isUserNearBottom()) {
      scrollToBottom();
    }
  }

  async function sendMessage() {
    const question = input.value.trim();
    if (!question) return;

    // Remove all previous recommended questions when user types a new query
    const allRecommendations = messagesDiv!.querySelectorAll('.recommended-questions');
    allRecommendations.forEach(rec => rec.remove());

    addMessage(question, "user");
    input.value = "";
    // Reset textarea height after sending
    input.style.height = '24px';
    
    // Save session after user message
    saveCurrentSession();
    
    await sendMessageText(question);
  }

  async function sendMessageText(question: string) {
    if (!question) return;

    const botDiv = addMessageHTML("", "bot", null);
    
    // Create status streaming matching the existing "Thinking..." style
    let currentStatusText = '';
    let isStreamingStatus = false;
    
    const streamStatusText = async (text: string) => {
      isStreamingStatus = true;
      currentStatusText = '';
      
      // Stream word by word
      const words = text.split(' ');
      for (let i = 0; i < words.length; i++) {
        currentStatusText += (i > 0 ? ' ' : '') + words[i];
        botDiv.innerHTML = `
          <div class="thinking">
            ${currentStatusText}
            <span class="thinking-dots">
              <span></span>
              <span></span>
              <span></span>
            </span>
          </div>
        `;
        
        // Small delay for streaming effect
        await new Promise(resolve => setTimeout(resolve, 30));
        autoScrollToBottom();
      }
      
      // Hold the completed message briefly before next one
      await new Promise(resolve => setTimeout(resolve, 300));
      isStreamingStatus = false;
    };
    
    const updateThinkingStatus = async (status: string, message: string) => {
      // Wait if currently streaming
      while (isStreamingStatus) {
        await new Promise(resolve => setTimeout(resolve, 50));
      }
      
      await streamStatusText(message);
    };
    
    // Initial "Thinking" state - wait for first status from backend
    botDiv.innerHTML = `
      <div class="thinking">
        Thinking
        <span class="thinking-dots">
          <span></span>
          <span></span>
          <span></span>
        </span>
      </div>
    `;
    
    setTimeout(() => autoScrollToBottom(), 50);

    try {
      const currentUser = JSON.parse(localStorage.getItem('user') || 'null');
      if (!currentUser || !currentUser.access_token) {
        console.error("[CHAT] User not authenticated, redirecting to login");
        localStorage.removeItem('user');
        window.location.href = "/login";
        return;
      }
      
      const requestBody = { 
        question,
        session_id: sessionId
      };
      
      const response = await fetch(`${getApiBase()}/chat/stream`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${currentUser.access_token}`
        },
        body: JSON.stringify(requestBody),
      });

      if (response.status === 401 || response.status === 403) {
        console.error("[CHAT] Authentication failed, redirecting to login");
        localStorage.removeItem('user');
        window.location.href = "/login";
        return;
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let fullResponse = "";
      let lastRenderTime = 0;
      const renderThrottle = 16;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'status') {
                // Update thinking status with backend progress (don't await, let it stream async)
                updateThinkingStatus(data.status, data.message).catch(e => console.error('Status update error:', e));
              } else if (data.type === 'thinking_complete') {
                botDiv.innerHTML = `<div class="message-content"></div>`;
              } else if (data.type === 'sources') {
                console.log("[CONSOLE]", data.sources);
              } else if (data.type === 'token') {
                const token = data.token;
                fullResponse += token;
                
                const now = Date.now();
                if (now - lastRenderTime > renderThrottle) {
                  const contentDiv = botDiv.querySelector('.message-content');
                  if (contentDiv) {
                    contentDiv.innerHTML = renderMarkdown(fullResponse);
                  } else {
                    botDiv.innerHTML = `<div class="message-content">${renderMarkdown(fullResponse)}</div>`;
                  }
                  autoScrollToBottom();
                  lastRenderTime = now;
                }
              } else if (data.type === 'done') {
                fullResponse = data.full_response || fullResponse;
                const traceId = data.trace_id;
                const recommendedQuestions = data.recommended_questions || [];
                
                if (!fullResponse || fullResponse.trim() === '') {
                  fullResponse = "I apologize, but I wasn't able to generate a response. Please try again.";
                }
                
                // Save recommended questions to localStorage for persistence
                if (recommendedQuestions && recommendedQuestions.length > 0) {
                  const messageIndex = messagesDiv!.children.length - 1; // Current bot message index
                  saveRecommendedQuestions(messageIndex, recommendedQuestions);
                }
                
                // Build recommended questions HTML
                const recommendedQuestionsHTML = buildRecommendedQuestionsHTML(recommendedQuestions);
                
                botDiv.innerHTML = `
                  <div class="message-content">${renderMarkdown(fullResponse)}</div>
                  <div class="feedback-buttons">
                    <button class="copy-button" onclick="window.copyMessage(this)" title="Copy message">
                      <img src="/images/copy-icon.svg?v=2" alt="Copy" width="16" height="16">
                    </button>
                    <button class="feedback-btn thumbs-up" onclick="window.submitFeedback(this, 'thumbs_up')" title="Good response">
                      <img src="/images/thumbs-up-icon.svg?v=2" alt="Thumbs up" width="16" height="16">
                    </button>
                    <button class="feedback-btn thumbs-down" onclick="window.submitFeedback(this, 'thumbs_down')" title="Bad response">
                      <img src="/images/thumbs-down-icon.svg?v=2" alt="Thumbs down" width="16" height="16">
                    </button>
                    <span class="feedback-text"></span>
                  </div>
                  ${recommendedQuestionsHTML}
                `;
                
                if (traceId) {
                  botDiv.dataset.traceId = traceId;
                }
                
                // Save session after bot response
                saveCurrentSession();
                
                return;
              } else if (data.type === 'error') {
                throw new Error(data.error);
              }
            } catch (e) {
              console.error("Error parsing streaming data:", e);
            }
          }
        }
      }
      
    } catch (error) {
      console.error("Error sending message:", error);
      botDiv.innerHTML = "Sorry, there was an error. Please try again.";
    }
  }

  function copyMessage(button: HTMLElement) {
    const messageDiv = button.closest('.message.bot');
    const contentDiv = messageDiv!.querySelector('.message-content');
    const textContent = contentDiv!.textContent || contentDiv!.innerHTML || '';
    
    navigator.clipboard.writeText(textContent).then(() => {
      console.log('[COPY] Message copied successfully');
      const originalHTML = button.innerHTML;
      
      // Change to checkmark icon
      button.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10a37f" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
      `;
      button.classList.add('copied');
      button.title = 'Copied!';
      
      // Show toast notification
      try {
        showToast('Copied to clipboard');
      } catch (e) {
        console.error('[TOAST] Error showing toast:', e);
      }
      
      setTimeout(() => {
        button.innerHTML = originalHTML;
        button.classList.remove('copied');
        button.title = 'Copy message';
      }, 2000);
    }).catch(err => {
      console.error('[COPY] Failed to copy text:', err);
    });
  }

  function askRecommendedQuestion(button: HTMLElement) {
    const question = button.getAttribute('data-question');
    if (question) {
      // Remove ALL previous recommended questions from the DOM
      const allRecommendations = messagesDiv!.querySelectorAll('.recommended-questions');
      allRecommendations.forEach(rec => rec.remove());
      
      // Add user message to chat FIRST (so it displays immediately)
      addMessage(question, "user");
      
      // Then send the question to get bot response
      sendMessageText(question);
    }
  }

  async function submitFeedback(button: HTMLElement, rating: string) {
    try {
      const messageDiv = button.closest('.message.bot') as HTMLElement;
      if (!messageDiv) return;
      
      const traceId = messageDiv.dataset.traceId || messageDiv.dataset.traceid;
      
      if (messageDiv.dataset.feedbackSubmitted === 'true') {
        return;
      }
      
      // If thumbs down, show detailed feedback modal
      if (rating === 'thumbs_down') {
        showFeedbackModal(messageDiv, traceId || '');
        return;
      }
      
      // For thumbs up, submit immediately
      const feedbackButtons = messageDiv.querySelectorAll('.feedback-btn');
      feedbackButtons.forEach((btn) => {
        const buttonEl = btn as HTMLButtonElement;
        buttonEl.disabled = true;
        buttonEl.style.cursor = 'not-allowed';
        buttonEl.style.opacity = '0.5';
      });
      
      let finalTraceId = traceId;
      if (!traceId) {
        const fallbackTraceId = 'feedback_fallback_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        messageDiv.dataset.traceId = fallbackTraceId;
        finalTraceId = fallbackTraceId;
      }
      
      const apiBase = getApiBase();
      const currentUser = JSON.parse(localStorage.getItem('user') || 'null');
      
      if (!currentUser || !currentUser.access_token) {
        console.error('[FEEDBACK] User not authenticated');
        return;
      }
      
      const response = await fetch(`${apiBase}/feedback`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${currentUser.access_token}`
        },
        body: JSON.stringify({
          trace_id: finalTraceId,
          rating: rating,
          comment: "",
          categories: []
        }),
      });
      
      if (response.ok) {
        messageDiv.dataset.feedbackSubmitted = 'true';
        feedbackButtons.forEach((btn) => btn.classList.remove('selected'));
        button.classList.add('selected');
        
        const feedbackText = messageDiv.querySelector('.feedback-text')!;
        feedbackText.textContent = 'Thanks for your feedback!';
        
        setTimeout(() => {
          feedbackText.textContent = '';
        }, 3000);
      }
    } catch (error) {
      console.error("Error submitting feedback:", error);
    }
  }

  function showFeedbackModal(messageDiv: HTMLElement, traceId: string) {
    const modal = document.getElementById('feedback-modal');
    if (!modal) return;
    
    // Store reference to message for later submission
    modal.dataset.messageId = messageDiv.dataset.traceId || traceId;
    modal.dataset.traceId = traceId;
    
    // Reset modal state - clear all category selections
    const categoryBtns = modal.querySelectorAll('.feedback-category-btn');
    categoryBtns.forEach(btn => btn.classList.remove('active'));
    
    // Clear comment textarea
    const commentTextarea = document.getElementById('feedback-comment') as HTMLTextAreaElement;
    if (commentTextarea) {
      commentTextarea.value = '';
    }
    
    // Show modal
    modal.style.display = 'flex';
  }

  async function submitDetailedFeedback() {
    const modal = document.getElementById('feedback-modal');
    if (!modal) return;
    
    const traceId = modal.dataset.traceId || '';
    const messageDiv = document.querySelector(`[data-trace-id="${traceId}"]`) as HTMLElement;
    
    // Get selected categories
    const selectedCategories: string[] = [];
    const categoryBtns = modal.querySelectorAll('.feedback-category-btn.active');
    categoryBtns.forEach(btn => {
      const category = btn.getAttribute('data-category');
      if (category) {
        selectedCategories.push(category);
      }
    });
    
    // Get comment
    const commentTextarea = document.getElementById('feedback-comment') as HTMLTextAreaElement;
    const comment = commentTextarea ? commentTextarea.value.trim() : '';
    
    // Close modal
    modal.style.display = 'none';
    
    // Submit feedback
    try {
      let finalTraceId = traceId;
      if (!traceId) {
        const fallbackTraceId = 'feedback_fallback_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        if (messageDiv) {
          messageDiv.dataset.traceId = fallbackTraceId;
        }
        finalTraceId = fallbackTraceId;
      }
      
      const apiBase = getApiBase();
      const currentUser = JSON.parse(localStorage.getItem('user') || 'null');
      
      if (!currentUser || !currentUser.access_token) {
        console.error('[FEEDBACK] User not authenticated');
        return;
      }
      
      const response = await fetch(`${apiBase}/feedback`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${currentUser.access_token}`
        },
        body: JSON.stringify({
          trace_id: finalTraceId,
          rating: 'thumbs_down',
          comment: comment,
          categories: selectedCategories
        }),
      });
      
      if (response.ok && messageDiv) {
        const feedbackButtons = messageDiv.querySelectorAll('.feedback-btn');
        feedbackButtons.forEach((btn) => {
          const buttonEl = btn as HTMLButtonElement;
          buttonEl.disabled = true;
          buttonEl.style.cursor = 'not-allowed';
          buttonEl.style.opacity = '0.5';
          btn.classList.remove('selected');
        });
        
        const thumbsDownBtn = messageDiv.querySelector('.feedback-btn.thumbs-down');
        if (thumbsDownBtn) {
          thumbsDownBtn.classList.add('selected');
        }
        
        messageDiv.dataset.feedbackSubmitted = 'true';
        
        const feedbackText = messageDiv.querySelector('.feedback-text')!;
        feedbackText.textContent = 'Thanks! We\'ll improve.';
        
        setTimeout(() => {
          feedbackText.textContent = '';
        }, 3000);
      }
    } catch (error) {
      console.error("Error submitting detailed feedback:", error);
    }
  }

  function copyUserMessage(button: HTMLElement) {
    const wrapper = button.closest('.user-message-wrapper');
    if (!wrapper) return;
    
    const messageDiv = wrapper.querySelector('.message.user') as HTMLElement;
    if (!messageDiv) return;
    
    const text = messageDiv.textContent || '';
    navigator.clipboard.writeText(text).then(() => {
      console.log('[COPY USER] User message copied successfully');
      const originalHTML = button.innerHTML;
      
      // Change to checkmark icon
      button.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10a37f" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
      `;
      button.title = 'Copied!';
      
      // Show toast notification
      try {
        showToast('Copied to clipboard');
      } catch (e) {
        console.error('[TOAST] Error showing toast:', e);
      }
      
      setTimeout(() => {
        button.innerHTML = originalHTML;
        button.title = 'Copy message';
      }, 2000);
    }).catch(err => {
      console.error('[COPY USER] Failed to copy text:', err);
    });
  }

  function editMessage(button: HTMLElement) {
    const wrapper = button.closest('.user-message-wrapper');
    if (!wrapper) return;
    
    const messageDiv = wrapper.querySelector('.message.user') as HTMLElement;
    const editContainer = wrapper.querySelector('.edit-button-container');
    
    if (!messageDiv || !editContainer) return;
    
    const originalText = messageDiv.textContent || '';
    
    // Add editing class to wrapper
    wrapper.classList.add('editing');
    
    // Replace message with textarea
    messageDiv.innerHTML = `
      <textarea class="edit-textarea" rows="1">${originalText}</textarea>
      <div class="edit-actions">
        <button class="edit-action-btn edit-cancel-btn" onclick="window.cancelEdit(this)">Cancel</button>
        <button class="edit-action-btn edit-save-btn" onclick="window.saveEdit(this)" title="Send">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 1a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L7 12.586V2a1 1 0 011-1z" transform="rotate(180 8 8)"/>
          </svg>
        </button>
      </div>
    `;
    
    // Clear the edit container since we moved buttons inside messageDiv
    editContainer.innerHTML = ``;
    
    // Store original text for cancel
    wrapper.setAttribute('data-original-text', originalText);
    
    // Focus the textarea and set up auto-resize
    const textarea = messageDiv.querySelector('.edit-textarea') as HTMLTextAreaElement;
    if (textarea) {
      // Auto-resize functionality
      const autoResize = () => {
        textarea.style.height = '24px';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
      };
      
      textarea.addEventListener('input', autoResize);
      
      // Enter key to save (without Shift)
      textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          const saveBtn = messageDiv.querySelector('.edit-save-btn') as HTMLButtonElement;
          if (saveBtn) saveBtn.click();
        }
      });
      
      autoResize(); // Initial resize
      
      textarea.focus();
      textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    }
  }

  function cancelEdit(button: HTMLElement) {
    const wrapper = button.closest('.user-message-wrapper');
    if (!wrapper) return;
    
    const messageDiv = wrapper.querySelector('.message.user') as HTMLElement;
    const editContainer = wrapper.querySelector('.edit-button-container');
    const originalText = wrapper.getAttribute('data-original-text') || '';
    
    if (!messageDiv || !editContainer) return;
    
    // Remove editing class from wrapper
    wrapper.classList.remove('editing');
    
    // Restore original message
    messageDiv.innerHTML = originalText;
    
    // Restore original buttons
    editContainer.innerHTML = `
      <button class="copy-button-user" onclick="window.copyUserMessage(this)" title="Copy message">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
      </button>
      <button class="edit-btn" onclick="window.editMessage(this)" title="Edit message">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path>
        </svg>
      </button>
    `;
    
    wrapper.removeAttribute('data-original-text');
  }

  function saveEdit(button: HTMLElement) {
    const wrapper = button.closest('.user-message-wrapper');
    if (!wrapper) return;
    
    const messageDiv = wrapper.querySelector('.message.user') as HTMLElement;
    const editContainer = wrapper.querySelector('.edit-button-container');
    const textarea = messageDiv?.querySelector('.edit-textarea') as HTMLTextAreaElement;
    
    if (!textarea || !messageDiv || !editContainer) return;
    
    const newText = textarea.value.trim();
    
    if (!newText) {
      alert('Message cannot be empty');
      return;
    }
    
    // Remove editing class from wrapper
    wrapper.classList.remove('editing');
    
    // Find all messages after this one and remove them
    let nextElement = wrapper.nextElementSibling;
    while (nextElement) {
      const toRemove = nextElement;
      nextElement = nextElement.nextElementSibling;
      toRemove.remove();
    }
    
    // Update the message
    messageDiv.innerHTML = newText;
    
    // Restore original buttons
    editContainer.innerHTML = `
      <button class="copy-button-user" onclick="window.copyUserMessage(this)" title="Copy message">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
      </button>
      <button class="edit-btn" onclick="window.editMessage(this)" title="Edit message">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path>
        </svg>
      </button>
    `;
    
    wrapper.removeAttribute('data-original-text');
    
    // Send the edited message to get a new response
    sendMessageText(newText);
  }

  // Expose ALL functions to window for onclick handlers
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).copyMessage = copyMessage;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).copyUserMessage = copyUserMessage;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).submitFeedback = submitFeedback;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).editMessage = editMessage;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).cancelEdit = cancelEdit;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).saveEdit = saveEdit;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).askRecommendedQuestion = askRecommendedQuestion;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).showFeedbackModal = showFeedbackModal;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).submitDetailedFeedback = submitDetailedFeedback;

  // Initialize auth - simplified since auth check is done at component level
  function initAuth() {
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    
    // User is already authenticated at this point (checked in component)
    // Just load user info and chat history
    if (user && user.access_token) {
    updateUserInfo(user);
      
      // Load session history in sidebar
      renderSessionHistory();
      
      // Load current session if it exists in localStorage
      const sessions = getAllSessions();
      const currentSession = sessions.find(s => s.id === sessionId);
      if (currentSession && messagesDiv!.children.length === 0) {
        loadSession(currentSession);
      }
    }
  }

  interface User {
    id: string;
    name: string;
    email: string;
    access_token: string;
    refresh_token: string;
  }

  function updateUserInfo(user: User) {
    const userName = document.getElementById('userName');
    const userAvatar = document.getElementById('userAvatar');
    const userEmail = document.getElementById('userEmail');
    const userEmailSidebar = document.getElementById('userEmailSidebar');
    
    if (user) {
      userName!.textContent = user.name || 'User';
      userAvatar!.textContent = (user.name || 'U').charAt(0).toUpperCase();
      userEmail!.textContent = user.email || '';
      if (userEmailSidebar) {
        userEmailSidebar.textContent = user.email || '';
      }
    }
  }

  // Legacy function - keeping for potential future backend integration
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async function loadUserChatHistory(userId: string, accessToken: string) {
    try {
      const response = await fetch(`${getApiBase()}/chat/history/${userId}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const history = data.history || [];
        
        if (history.length > 0) {
          messagesDiv!.innerHTML = '';
          
          for (let i = 0; i < history.length; i++) {
            const message = history[i];
            const sender = message.role === 'user' ? 'user' : 'bot';
            
            if (sender === 'bot') {
              // For bot messages, check if we have saved recommendations
              const savedRecommendations = loadRecommendedQuestions(i);
              const recommendedQuestionsHTML = buildRecommendedQuestionsHTML(savedRecommendations);
              
              // Create bot message with recommendations
              const div = document.createElement("div");
              div.className = "message bot";
              div.innerHTML = `
                <div class="message-content">${renderMarkdown(message.content)}</div>
                <div class="feedback-buttons">
                  <button class="copy-button" onclick="window.copyMessage(this)" title="Copy message">
                    <img src="/images/copy-icon.svg?v=2" alt="Copy" width="16" height="16">
                  </button>
                  <button class="feedback-btn thumbs-up" onclick="window.submitFeedback(this, 'thumbs_up')" title="Good response">
                    <img src="/images/thumbs-up-icon.svg?v=2" alt="Thumbs up" width="16" height="16">
                  </button>
                  <button class="feedback-btn thumbs-down" onclick="window.submitFeedback(this, 'thumbs_down')" title="Bad response">
                    <img src="/images/thumbs-down-icon.svg?v=2" alt="Thumbs down" width="16" height="16">
                  </button>
                  <span class="feedback-text"></span>
                </div>
                ${recommendedQuestionsHTML}
              `;
              messagesDiv!.appendChild(div);
            } else {
              addMessage(message.content, sender);
            }
          }
          
          scrollToBottom();
        }
      }
    } catch (error) {
      console.error('[HISTORY] Failed to load chat history:', error);
    }
  }

  async function handleNewChat() {
    console.log('[NEW CHAT] Starting new chat...');
    const newChatBtn = document.getElementById('newChatBtn') as HTMLElement;
    
    // Show loading state
    if (newChatBtn) {
      console.log('[NEW CHAT] Showing loading state');
      newChatBtn.innerHTML = `
        <svg class="loading-spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" opacity="0.25"/>
          <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
        </svg>
        <span class="btn-text">Loading...</span>
      `;
      newChatBtn.style.pointerEvents = 'none';
    }
    
    // Save current session before creating new one
    if (messagesDiv!.children.length > 0) {
      saveCurrentSession();
    }
    
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (user && user.id && user.access_token) {
      try {
        await fetch(`${getApiBase()}/chat/history/${user.id}`, {
          method: "DELETE",
          headers: {
            'Authorization': `Bearer ${user.access_token}`
          }
        });
      } catch (error) {
        console.error('Failed to clear chat history:', error);
      }
    }
    
    // Clear old recommended questions
    clearRecommendedQuestions();
    
    // Create new session
    sessionId = createNewSession();
    currentSessionTitle = '';
    localStorage.setItem('chatbot_session_id', sessionId);
    
    // Clear messages
    messagesDiv!.innerHTML = '';
    updateEmptyState();
    
    // Update sidebar to show new session is active
    renderSessionHistory();
    
    // Show success state briefly
    if (newChatBtn) {
      console.log('[NEW CHAT] Showing success state');
      newChatBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10a37f" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <span class="btn-text">New chat</span>
      `;
      
      // Show toast notification
      try {
        showToast('Started new chat');
      } catch (e) {
        console.error('[TOAST] Error showing toast:', e);
      }
      
      setTimeout(() => {
        console.log('[NEW CHAT] Resetting to normal state');
        newChatBtn.innerHTML = `
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          <span class="btn-text">New chat</span>
        `;
        newChatBtn.style.pointerEvents = 'auto';
      }, 800);
    }
  }

  function handleLogout() {
    localStorage.removeItem('user');
    window.location.href = "/login";
  }

  function toggleDropdown() {
    const dropdown = document.getElementById('userDropdown');
    dropdown!.classList.toggle('show');
  }

  // Event listeners for regular input (bottom)
  if (sendBtn) {
    sendBtn.addEventListener("click", sendMessage);
  }
  
  if (input) {
    // Note: Enter key is already handled by React's onKeyDown in the JSX
    // This is just a fallback
    input.addEventListener("keydown", (e) => { 
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  // Event listeners for empty state input (center)
  if (sendBtnEmptyState) {
    sendBtnEmptyState.addEventListener("click", () => {
      if (inputEmptyState) {
        const question = inputEmptyState.value.trim();
        if (question) {
          addMessage(question, "user");
          inputEmptyState.value = "";
          inputEmptyState.style.height = '24px';
          sendMessageText(question);
        }
      }
    });
  }
  
  if (inputEmptyState) {
    // Auto-expand textarea
    inputEmptyState.addEventListener("input", (e) => {
      const target = e.target as HTMLTextAreaElement;
      target.style.height = '24px';
      target.style.height = Math.min(target.scrollHeight, 200) + 'px';
    });
    
    // Handle Enter key
    inputEmptyState.addEventListener("keydown", (e) => { 
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (sendBtnEmptyState) {
          sendBtnEmptyState.click();
        }
      }
    });
  }
  
  // Event listeners for suggested question buttons
  const suggestedQuestionBtns = document.querySelectorAll('.suggested-question-btn');
  suggestedQuestionBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const button = e.target as HTMLButtonElement;
      const question = button.getAttribute('data-question');
      if (question) {
        // Remove all previous recommended questions when user clicks a suggested question
        const allRecommendations = messagesDiv!.querySelectorAll('.recommended-questions');
        allRecommendations.forEach(rec => rec.remove());
        
        // Add user message to chat
        addMessage(question, "user");
        
        // Clear input fields
        if (input) {
          input.value = "";
          input.style.height = '24px';
        }
        if (inputEmptyState) {
          inputEmptyState.value = "";
          inputEmptyState.style.height = '24px';
        }
        
        // Send the question
        sendMessageText(question);
      }
    });
  });
  
  const newChatBtn = document.getElementById('newChatBtn');
  if (newChatBtn) {
    newChatBtn.addEventListener('click', handleNewChat);
  }
  
  const userMenu = document.getElementById('userMenu');
  if (userMenu) {
    userMenu.addEventListener('click', toggleDropdown);
  }
  
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
  }
  
  // Scroll to bottom button functionality
  const scrollToBottomBtn = document.getElementById('scroll-to-bottom-btn');
  const messagesContainer = document.querySelector('.messages-container') as HTMLElement;
  
  // Helper function to check if user is near bottom
  function checkScrollPosition() {
    if (!scrollToBottomBtn || !messagesContainer) return;
    
    const threshold = 150; // Show button when more than 150px from bottom
    const isNearBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < threshold;
    
    if (isNearBottom) {
      scrollToBottomBtn.classList.remove('show');
    } else {
      scrollToBottomBtn.classList.add('show');
    }
  }
  
  if (scrollToBottomBtn && messagesContainer) {
    scrollToBottomBtn.addEventListener('click', () => {
      scrollToBottom();
      // Hide button immediately after clicking
      scrollToBottomBtn.classList.remove('show');
    });
    
    // Show/hide scroll to bottom button based on scroll position
    messagesContainer.addEventListener('scroll', checkScrollPosition);
    
    // Also check when content changes (new messages added)
    const observer = new MutationObserver(checkScrollPosition);
    observer.observe(messagesDiv!, { childList: true, subtree: true });
    
    // Initially hide the button
    scrollToBottomBtn.classList.remove('show');
  }
  
  document.addEventListener('click', (event) => {
    const userMenu = document.getElementById('userMenu');
    const dropdown = document.getElementById('userDropdown');
    
    if (userMenu && !userMenu.contains(event.target as Node)) {
      if (dropdown) {
        dropdown.classList.remove('show');
      }
    }
  });

  // Feedback modal event listeners
  const feedbackModal = document.getElementById('feedback-modal');
  const feedbackModalClose = document.getElementById('feedback-modal-close');
  const feedbackSubmitBtn = document.getElementById('feedback-submit-btn');
  
  // Close modal when clicking X button
  if (feedbackModalClose) {
    feedbackModalClose.addEventListener('click', () => {
      if (feedbackModal) {
        feedbackModal.style.display = 'none';
      }
    });
  }
  
  // Close modal when clicking outside
  if (feedbackModal) {
    feedbackModal.addEventListener('click', (e) => {
      if (e.target === feedbackModal) {
        feedbackModal.style.display = 'none';
      }
    });
  }
  
  // Toggle category selection
  const categoryBtns = document.querySelectorAll('.feedback-category-btn');
  categoryBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      btn.classList.toggle('active');
    });
  });
  
  // Submit detailed feedback
  if (feedbackSubmitBtn) {
    feedbackSubmitBtn.addEventListener('click', submitDetailedFeedback);
  }

  initAuth();
}
