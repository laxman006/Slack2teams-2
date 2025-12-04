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

// Character limit constants
const MAX_PROMPT_LENGTH = 20000; // ~5K tokens (safe for RAG)
const WARN_PROMPT_LENGTH = 10000; // ~2.5K tokens - warning threshold

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
              {isSidebarOpen ? (
                <Image 
                  src="/images/CloudFuze Horizontal Logo.svg" 
                  alt="CloudFuze" 
                  width={200} 
                  height={52} 
                  priority 
                />
              ) : (
                <Image 
                  src="/images/CloudFuze-icon-64x64.png" 
                  alt="CloudFuze" 
                  width={42} 
                  height={42} 
                  priority 
                />
              )}
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
        
        <div className="sidebar-content-wrapper">
          <div className="my-chats-section">
            <div className="section-label">My Chats</div>
            <div id="sidebar-history" className="sidebar-history">
              {/* Chat history will be populated here */}
            </div>
          </div>
          
          <div className="others-chats-section">
            <div className="section-label">Others Chats</div>
            <div id="others-history" className="sidebar-history">
              {/* Others' chats will be populated here */}
            </div>
          </div>
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
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path d="M3.50171 12.6663V7.33333C3.50171 6.64424 3.50106 6.08728 3.53784 5.63704C3.57525 5.17925 3.65463 4.77342 3.84644 4.39681L3.96851 4.17806C4.2726 3.68235 4.70919 3.2785 5.23023 3.01302L5.3728 2.94661C5.7091 2.80238 6.06981 2.73717 6.47046 2.70443C6.9207 2.66764 7.47766 2.66829 8.16675 2.66829H9.16675L9.30054 2.68197C9.60367 2.7439 9.83179 3.0119 9.83179 3.33333C9.83179 3.65476 9.60367 3.92277 9.30054 3.9847L9.16675 3.99837H8.16675C7.45571 3.99837 6.96238 3.99926 6.57886 4.0306C6.297 4.05363 6.10737 4.09049 5.96362 4.14193L5.83374 4.19857C5.53148 4.35259 5.27861 4.58671 5.1023 4.87435L5.03198 5.00032C4.95147 5.15833 4.89472 5.36974 4.86401 5.74544C4.83268 6.12896 4.83179 6.6223 4.83179 7.33333V12.6663C4.83179 13.3772 4.8327 13.8707 4.86401 14.2542C4.8947 14.6298 4.95153 14.8414 5.03198 14.9993L5.1023 15.1263C5.27861 15.4137 5.53163 15.6482 5.83374 15.8021L5.96362 15.8577C6.1074 15.9092 6.29691 15.947 6.57886 15.9701C6.96238 16.0014 7.45571 16.0013 8.16675 16.0013H9.16675L9.30054 16.015C9.6036 16.0769 9.83163 16.345 9.83179 16.6663C9.83179 16.9877 9.60363 17.2558 9.30054 17.3177L9.16675 17.3314H8.16675C7.47766 17.3314 6.9207 17.332 6.47046 17.2952C6.06978 17.2625 5.70912 17.1973 5.3728 17.0531L5.23023 16.9867C4.70911 16.7211 4.27261 16.3174 3.96851 15.8216L3.84644 15.6038C3.65447 15.2271 3.57526 14.8206 3.53784 14.3626C3.50107 13.9124 3.50171 13.3553 3.50171 12.6663ZM13.8035 13.804C13.5438 14.0634 13.1226 14.0635 12.863 13.804C12.6033 13.5443 12.6033 13.1223 12.863 12.8626L13.8035 13.804ZM12.863 6.19661C13.0903 5.96939 13.4409 5.94126 13.699 6.11165L13.8035 6.19661L17.1375 9.52962C17.3969 9.78923 17.3968 10.2104 17.1375 10.4701L13.8035 13.804L13.3337 13.3333L12.863 12.8626L15.0603 10.6654H9.16675C8.79959 10.6654 8.50189 10.3674 8.50171 10.0003C8.50171 9.63306 8.79948 9.33529 9.16675 9.33529H15.0613L12.863 7.13704L12.7781 7.03255C12.6077 6.77449 12.6359 6.42386 12.863 6.19661Z"/>
                </svg>
                <span>Log out</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* ChatGPT-Style Main Content */}
      <main className="chatgpt-main">
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
                <div className="input-wrapper-chatgpt" style={{ position: 'relative' }}>
                  <textarea
                    id="user-input-empty"
                    className="chatgpt-textarea"
                    placeholder="Ask me anything about CloudFuze..."
                    rows={1}
                    maxLength={MAX_PROMPT_LENGTH}
                    style={{ paddingBottom: '28px' }}
                  />
                  <span id="char-counter-empty" style={{
                    fontSize: '12px',
                    color: '#6b7280',
                    position: 'absolute',
                    right: '55px',
                    bottom: '8px',
                    display: 'none',
                    fontWeight: '400',
                    pointerEvents: 'none'
                  }}></span>
                  <button id="send-btn-empty" className="chatgpt-send-btn">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M8 1a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L7 12.586V2a1 1 0 011-1z" transform="rotate(180 8 8)"/>
                    </svg>
                  </button>
                  <div id="tooltip-empty" style={{
                    display: 'none',
                    position: 'absolute',
                    bottom: 'calc(100% + 8px)',
                    right: '0',
                    padding: '8px 12px',
                    backgroundColor: '#1f2937',
                    color: 'white',
                    fontSize: '13px',
                    borderRadius: '8px',
                    whiteSpace: 'nowrap',
                    zIndex: 1000,
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                    pointerEvents: 'none'
                  }}>Message is too long</div>
                </div>
                {/* Suggested Questions - Loaded Dynamically */}
                <div className="suggested-questions-container" id="suggested-questions-empty">
                  {/* Questions loaded from API */}
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
            <div className="input-wrapper-chatgpt" style={{ position: 'relative' }}>
              <textarea
                ref={textareaRef}
                id="user-input"
                className="chatgpt-textarea"
                placeholder="Ask me anything about CloudFuze..."
                rows={1}
                maxLength={MAX_PROMPT_LENGTH}
                style={{ paddingBottom: '28px' }}
              />
              <span id="char-counter" style={{
                fontSize: '12px',
                color: '#6b7280',
                position: 'absolute',
                right: '55px',
                bottom: '8px',
                display: 'none',
                fontWeight: '400',
                pointerEvents: 'none'
              }}></span>
              <button id="send-btn" className="chatgpt-send-btn">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 1a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L7 12.586V2a1 1 0 011-1z" transform="rotate(180 8 8)"/>
                </svg>
              </button>
              <div id="tooltip-main" style={{
                display: 'none',
                position: 'absolute',
                bottom: 'calc(100% + 8px)',
                right: '0',
                padding: '8px 12px',
                backgroundColor: '#1f2937',
                color: 'white',
                fontSize: '13px',
                borderRadius: '8px',
                whiteSpace: 'nowrap',
                zIndex: 1000,
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                pointerEvents: 'none'
              }}>Message is too long</div>
            </div>
            {/* Suggested Questions - Loaded Dynamically */}
            <div className="suggested-questions-container" id="suggested-questions-main">
              {/* Questions loaded from API */}
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
  const sendBtn = document.getElementById("send-btn") as HTMLButtonElement;
  const emptyState = document.getElementById("empty-state");
  const inputEmptyState = document.getElementById("user-input-empty") as HTMLTextAreaElement;
  const sendBtnEmptyState = document.getElementById("send-btn-empty") as HTMLButtonElement;
  const inputSection = document.querySelector(".chatgpt-input-section") as HTMLElement;

  // Flag to prevent multiple simultaneous requests
  let isGenerating = false;

  // Helper function to disable/enable send buttons during generation
  function setGeneratingState(generating: boolean) {
    isGenerating = generating;
    const buttons = [sendBtn, sendBtnEmptyState];
    const inputs = [input, inputEmptyState];
    
    buttons.forEach(btn => {
      if (btn) {
        btn.disabled = generating;
        btn.style.opacity = generating ? '0.5' : '1';
        btn.style.cursor = generating ? 'not-allowed' : 'pointer';
        btn.title = generating ? 'Response is generating...' : 'Send message';
      }
    });
    
    inputs.forEach(inp => {
      if (inp) {
        inp.disabled = generating;
        inp.style.opacity = generating ? '0.7' : '1';
      }
    });
  }

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
  
  // Get user-specific localStorage key
  function getUserStorageKey(key: string): string {
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    const userId = user?.id || 'anonymous';
    return `${key}_${userId}`;
  }
  
  // Session management
  let sessionId = localStorage.getItem(getUserStorageKey('chatbot_session_id'));
  let currentSessionTitle = '';
  
  interface ChatSession {
    id: string;
    title: string;
    timestamp: number;
    createdAt: number;
    messages: Array<{role: string, content: string, recommendedQuestions?: string[]}>;
    deletedAt?: number; // Timestamp when session was deleted (for soft delete)
  }
  
  function createNewSession(): string {
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const randomId = Math.random().toString(36).substr(2, 9);
    return `cf.conversation.${date}.${randomId}`;
  }
  
  // Initialize or create session
  if (!sessionId) {
    sessionId = createNewSession();
    localStorage.setItem(getUserStorageKey('chatbot_session_id'), sessionId);
    console.log('[SESSION] Created new session:', sessionId);
  }
  
  // Track the currently active session (for UI highlighting)
  let activeSessionId = sessionId;
  
  // Load all sessions from localStorage (filter out empty sessions)
  function getAllSessions(): ChatSession[] {
    try {
      const storageKey = getUserStorageKey('chat_sessions');
      const sessionsStr = localStorage.getItem(storageKey);
      const sessions = sessionsStr ? JSON.parse(sessionsStr) : [];
      // Filter out sessions with no messages (empty chats)
      return sessions.filter((s: ChatSession) => s.messages && s.messages.length > 0);
    } catch (e) {
      console.error('[SESSIONS] Failed to load sessions:', e);
      return [];
    }
  }
  
  // Save all sessions to localStorage
  function saveAllSessions(sessions: ChatSession[]) {
    try {
      const storageKey = getUserStorageKey('chat_sessions');
      localStorage.setItem(storageKey, JSON.stringify(sessions));
    } catch (e) {
      console.error('[SESSIONS] Failed to save sessions:', e);
    }
  }
  
  // Get all deleted sessions from localStorage
  function getDeletedSessions(): ChatSession[] {
    try {
      const storageKey = getUserStorageKey('deleted_chat_sessions');
      const deletedStr = localStorage.getItem(storageKey);
      return deletedStr ? JSON.parse(deletedStr) : [];
    } catch (e) {
      console.error('[DELETED_SESSIONS] Failed to load deleted sessions:', e);
      return [];
    }
  }
  
  // Save deleted sessions to localStorage
  function saveDeletedSessions(sessions: ChatSession[]) {
    try {
      const storageKey = getUserStorageKey('deleted_chat_sessions');
      localStorage.setItem(storageKey, JSON.stringify(sessions));
      console.log('[DELETED_SESSIONS] Saved', sessions.length, 'deleted sessions');
    } catch (e) {
      console.error('[DELETED_SESSIONS] Failed to save deleted sessions:', e);
    }
  }
  
  // Add test data for all time periods (for UI testing)
  function addTestSessions() {
    const now = Date.now();
    const oneDay = 24 * 60 * 60 * 1000;
    
    const testSessions: ChatSession[] = [
      // Today
      {
        id: 'test-today-1',
        title: 'Test chat from Today - Morning',
        timestamp: now - (2 * 60 * 60 * 1000), // 2 hours ago
        createdAt: now - (2 * 60 * 60 * 1000),
        messages: [
          { role: 'user', content: 'Test message from today' },
          { role: 'assistant', content: 'Test response from today' }
        ]
      },
      {
        id: 'test-today-2',
        title: 'Another test chat from Today',
        timestamp: now - (5 * 60 * 60 * 1000), // 5 hours ago
        createdAt: now - (5 * 60 * 60 * 1000),
        messages: [
          { role: 'user', content: 'Another test from today' },
          { role: 'assistant', content: 'Another response from today' }
        ]
      },
      // Yesterday
      {
        id: 'test-yesterday-1',
        title: 'Test chat from Yesterday - Morning',
        timestamp: now - (1.2 * oneDay), // 1.2 days ago
        createdAt: now - (1.2 * oneDay),
        messages: [
          { role: 'user', content: 'Test message from yesterday morning' },
          { role: 'assistant', content: 'Test response from yesterday morning' }
        ]
      },
      {
        id: 'test-yesterday-2',
        title: 'Test chat from Yesterday - Evening',
        timestamp: now - (1.8 * oneDay), // 1.8 days ago
        createdAt: now - (1.8 * oneDay),
        messages: [
          { role: 'user', content: 'Test message from yesterday evening' },
          { role: 'assistant', content: 'Test response from yesterday evening' }
        ]
      },
      // Older
      {
        id: 'test-older-1',
        title: 'Test chat from 3 days ago',
        timestamp: now - (3 * oneDay),
        createdAt: now - (3 * oneDay),
        messages: [
          { role: 'user', content: 'Test message from 3 days ago' },
          { role: 'assistant', content: 'Test response from 3 days ago' }
        ]
      },
      {
        id: 'test-older-2',
        title: 'Test chat from 1 week ago',
        timestamp: now - (7 * oneDay),
        createdAt: now - (7 * oneDay),
        messages: [
          { role: 'user', content: 'Test message from 1 week ago' },
          { role: 'assistant', content: 'Test response from 1 week ago' }
        ]
      },
      {
        id: 'test-older-3',
        title: 'Test chat from 2 weeks ago',
        timestamp: now - (14 * oneDay),
        createdAt: now - (14 * oneDay),
        messages: [
          { role: 'user', content: 'Test message from 2 weeks ago' },
          { role: 'assistant', content: 'Test response from 2 weeks ago' }
        ]
      },
      {
        id: 'test-older-4',
        title: 'Test chat from 1 month ago',
        timestamp: now - (30 * oneDay),
        createdAt: now - (30 * oneDay),
        messages: [
          { role: 'user', content: 'Test message from 1 month ago' },
          { role: 'assistant', content: 'Test response from 1 month ago' }
        ]
      }
    ];
    
    const existingSessions = getAllSessions();
    
    // Filter out test sessions that already exist
    const newTestSessions = testSessions.filter(test => 
      !existingSessions.some(existing => existing.id === test.id)
    );
    
    if (newTestSessions.length > 0) {
      const updatedSessions = [...existingSessions, ...newTestSessions];
      saveAllSessions(updatedSessions);
      console.log('[TEST DATA] Added', newTestSessions.length, 'test sessions');
    }
  }
  
  // Remove test sessions (for cleanup)
  function removeTestSessions() {
    const sessions = getAllSessions();
    const filteredSessions = sessions.filter(s => !s.id.startsWith('test-'));
    saveAllSessions(filteredSessions);
    console.log('[TEST DATA] Removed all test sessions');
    renderSessionHistory().catch(err => console.error('[SESSION] Failed to render history:', err));
  }
  
  // View deleted sessions (for debugging)
  function viewDeletedSessions() {
    const deleted = getDeletedSessions();
    console.log('[DELETED_SESSIONS] Total deleted sessions:', deleted.length);
    console.table(deleted.map(s => ({
      id: s.id,
      title: s.title,
      deletedAt: s.deletedAt ? new Date(s.deletedAt).toLocaleString() : 'N/A',
      messageCount: s.messages?.length || 0
    })));
    return deleted;
  }
  
  // Clear all deleted sessions (permanent delete)
  function clearDeletedSessions() {
    if (!confirm('Permanently delete all sessions in trash? This cannot be undone.')) return;
    const storageKey = getUserStorageKey('deleted_chat_sessions');
    localStorage.removeItem(storageKey);
    console.log('[DELETED_SESSIONS] Cleared all deleted sessions');
  }
  
  // View current user's storage data (for debugging)
  function viewUserData() {
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    console.log('=== Current User Data ===');
    console.log('User:', user ? `${user.name} (${user.email})` : 'Not logged in');
    console.log('User ID:', user?.id || 'N/A');
    console.log('\n=== Storage Keys ===');
    console.log('Active Sessions Key:', getUserStorageKey('chat_sessions'));
    console.log('Deleted Sessions Key:', getUserStorageKey('deleted_chat_sessions'));
    console.log('Session ID Key:', getUserStorageKey('chatbot_session_id'));
    console.log('\n=== Data Counts ===');
    const sessions = getAllSessions();
    const deleted = getDeletedSessions();
    console.log('Active Chats:', sessions.length);
    console.log('Deleted Chats:', deleted.length);
    console.log('Current Session ID:', sessionId);
    
    // Show all localStorage keys for this user
    console.log('\n=== All LocalStorage Keys ===');
    const userId = user?.id || 'anonymous';
    Object.keys(localStorage).forEach(key => {
      if (key.includes(userId)) {
        console.log(`- ${key}`);
      }
    });
  }
  
  // Expose to window for easy access in console
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).removeTestSessions = removeTestSessions;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).viewDeletedSessions = viewDeletedSessions;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).clearDeletedSessions = clearDeletedSessions;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).viewUserData = viewUserData;
  
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
    const now = Date.now();
    const sessionData: ChatSession = {
      id: sessionId!,
      title: sessionTitle,
      timestamp: now,
      createdAt: existingIndex >= 0 ? sessions[existingIndex].createdAt : now,
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
    
    // Render session history (async)
    renderSessionHistory().catch(err => console.error('[SESSION] Failed to render history:', err));
    
    // Sync session metadata to backend
    syncSessionToBackend(sessionData);
  }
  
  // Sync session metadata to backend
  async function syncSessionToBackend(sessionData: ChatSession) {
    try {
      const user = JSON.parse(localStorage.getItem('user') || 'null');
      if (!user || !user.access_token) return;
      
      await fetch(`${getApiBase()}/chat/sessions/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.access_token}`
        },
        body: JSON.stringify({
          session_id: sessionData.id,
          title: sessionData.title,
          created_at: sessionData.createdAt,
          updated_at: sessionData.timestamp,
          message_count: sessionData.messages.length
        })
      });
    } catch (error) {
      console.error('[SESSION] Failed to sync session to backend:', error);
    }
  }
  
  // Fetch all users' chats (one recent chat per user)
  async function fetchAllUsersChats() {
    try {
      const user = JSON.parse(localStorage.getItem('user') || 'null');
      if (!user || !user.access_token) return [];
      
      const response = await fetch(`${getApiBase()}/chat/sessions/all?limit=15`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.access_token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        // Already filtered on backend, return all sessions
        return data.sessions || [];
      }
      
      return [];
    } catch (error) {
      console.error('[SESSION] Failed to fetch all users chats:', error);
      return [];
    }
  }
  
  // Load another user's chat session (read-only)
  async function loadOthersSession(otherSessionId: string) {
    try {
      const user = JSON.parse(localStorage.getItem('user') || 'null');
      if (!user || !user.access_token) return;
      
      // Extract user_id from session_id (format: "user_chat_{user_id}")
      const userId = otherSessionId.replace('user_chat_', '');
      
      // Fetch actual messages from backend
      const response = await fetch(`${getApiBase()}/chat/sessions/messages/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.access_token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch messages');
      }
      
      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      // Create a temporary session object that won't be saved
      const sessionData: ChatSession = {
        id: otherSessionId,
        title: data.title,
        timestamp: Date.now(),
        createdAt: Date.now(),
        messages: data.messages
      };
      
      // Don't update sessionId to prevent this from being saved to user's history
      // Just display the messages
      loadSession(sessionData, true);
    } catch (error) {
      console.error('[SESSION] Failed to load others session:', error);
      alert('Failed to load this chat session.');
    }
  }
  
  
  // Convert plain text URLs and markdown links to clickable links, preserving HTML
  function linkifyText(text: string): string {
    // Check if the text already contains HTML tags (from formatted responses)
    const hasHtmlTags = /<[^>]+>/.test(text);
    
    if (hasHtmlTags) {
      // Text already has HTML formatting, just ensure links open in new tab
      let processed = text.replace(/<a\s+href="([^"]+)"(?![^>]*target=)/gi, '<a href="$1" target="_blank" rel="noopener noreferrer"');
      return processed;
    }
    
    // Plain text - convert markdown and URLs to links
    // First handle markdown links [text](url)
    let processed = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, linkText, url) => {
      return `<a href="${url}" target="_blank" rel="noopener noreferrer" style="color: #0033CC; text-decoration: underline;">${linkText}</a>`;
    });
    
    // Then handle plain URLs (that aren't already in anchor tags)
    const urlPattern = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    processed = processed.replace(urlPattern, (url) => {
      // Avoid double-linking by checking if URL is already in a href attribute
      const beforeUrl = processed.substring(Math.max(0, processed.indexOf(url) - 10), processed.indexOf(url));
      if (beforeUrl.includes('href=')) {
        return url; // Already linked, don't modify
      }
      return `<a href="${url}" target="_blank" rel="noopener noreferrer" style="color: #0033CC; text-decoration: underline;">${url}</a>`;
    });
    
    return processed;
  }
  
  // Load a specific session
  function loadSession(sessionData: ChatSession, isReadOnly = false) {
    console.log('[SESSION] Loading session:', sessionData.id, 'with', sessionData.messages.length, 'messages', isReadOnly ? '(read-only)' : '');
    
    // Always update activeSessionId for UI highlighting
    activeSessionId = sessionData.id;
    
    // Only update sessionId if not read-only (to prevent others' chats from being saved)
    if (!isReadOnly) {
      sessionId = sessionData.id;
      currentSessionTitle = sessionData.title;
      localStorage.setItem(getUserStorageKey('chatbot_session_id'), sessionId);
    }
    
    // Clear current messages
    messagesDiv!.innerHTML = '';
    
    // Show read-only banner if viewing others' chat
    if (isReadOnly) {
      const banner = document.createElement("div");
      banner.className = "read-only-banner";
      banner.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
        </svg>
        <span>Viewing read-only chat</span>
      `;
      messagesDiv!.appendChild(banner);
    }
    
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
        
        // Render markdown to HTML first, then make links clickable
        let formattedContent = msg.content;
        
        // Check if content needs markdown rendering (doesn't already have HTML tags)
        const hasHtmlTags = /<[^>]+>/.test(msg.content);
        if (!hasHtmlTags) {
          // Content is markdown or plain text, render it
          formattedContent = renderMarkdown(msg.content);
        }
        
        // Make sure links are clickable
        const contentWithLinks = linkifyText(formattedContent);
        
        div.innerHTML = `
          <div class="message-content">${contentWithLinks}</div>
          <div class="feedback-buttons">
            <button class="copy-button" onclick="window.copyMessage(this)" title="Copy message">
              <img src="/images/copy-icon.svg?v=2" alt="Copy" width="16" height="16">
            </button>
            ${!isReadOnly ? `
            <button class="feedback-btn thumbs-up" onclick="window.submitFeedback(this, 'thumbs_up')" title="Good response">
              <img src="/images/thumbs-up-icon.svg?v=2" alt="Thumbs up" width="16" height="16">
            </button>
            <button class="feedback-btn thumbs-down" onclick="window.submitFeedback(this, 'thumbs_down')" title="Bad response">
              <img src="/images/thumbs-down-icon.svg?v=2" alt="Thumbs down" width="16" height="16">
            </button>
            ` : ''}
            <span class="feedback-text"></span>
          </div>
          ${recommendedQuestionsHTML}
        `;
        messagesDiv!.appendChild(div);
      }
    });
    
    // Disable input for read-only mode
    if (isReadOnly) {
      const inputEl = document.getElementById('user-input') as HTMLTextAreaElement;
      const sendBtn = document.getElementById('send-btn') as HTMLButtonElement;
      if (inputEl) {
        inputEl.disabled = true;
        inputEl.placeholder = "Read-only mode - You cannot send messages";
      }
      if (sendBtn) sendBtn.disabled = true;
    } else {
      const inputEl = document.getElementById('user-input') as HTMLTextAreaElement;
      const sendBtn = document.getElementById('send-btn') as HTMLButtonElement;
      if (inputEl) {
        inputEl.disabled = false;
        inputEl.placeholder = "Type your message here...";
      }
      if (sendBtn) sendBtn.disabled = false;
    }
    
    updateEmptyState();
    scrollToBottom();
  }
  
  // Render session history in sidebar
  async function renderSessionHistory() {
    const sidebarHistory = document.getElementById('sidebar-history');
    if (!sidebarHistory) return;
    
    const sessions = getAllSessions();
    
    const now = Date.now();
    const oneDay = 24 * 60 * 60 * 1000;
    
    const today: ChatSession[] = [];
    const yesterday: ChatSession[] = [];
    const older: ChatSession[] = [];
    
    sessions.forEach(session => {
      const age = now - (session.createdAt || session.timestamp);
      if (age < oneDay) today.push(session);
      else if (age < 2 * oneDay) yesterday.push(session);
      else older.push(session);
    });
    
    let html = '';
    
    function renderSection(title: string, sessions: ChatSession[], sectionId: string, isOthersSection = false, defaultCollapsed = false) {
      if (sessions.length === 0) return '';
      
      // Check if section is collapsed (stored in localStorage, otherwise use default)
      const storedCollapsed = localStorage.getItem(`section_collapsed_${sectionId}`);
      const isCollapsed = storedCollapsed !== null ? storedCollapsed === 'true' : defaultCollapsed;
      
      let section = `
        <div class="history-section-title${isOthersSection ? ' others-section' : ''}" data-section-id="${sectionId}">
          <span>${title}</span>
          <button class="section-toggle-btn" data-section-id="${sectionId}" title="${isCollapsed ? 'Expand' : 'Collapse'}">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="toggle-icon ${isCollapsed ? 'collapsed' : ''}">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
        </div>
        <div class="history-section-content ${isCollapsed ? 'collapsed' : ''}" data-section-id="${sectionId}">
      `;
      
      sessions.forEach(session => {
        const isActive = session.id === activeSessionId;
        section += `
          <div class="history-item ${isActive ? 'active' : ''}${isOthersSection ? ' others-item' : ''}" data-session-id="${session.id}"${isOthersSection ? ' data-is-others="true"' : ''}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span class="history-item-title">${session.title}</span>
            ${!isOthersSection ? `
            <button class="history-item-delete" data-session-id="${session.id}" title="Delete chat">×</button>` : ''}
          </div>
        `;
      });
      
      section += '</div>';
      return section;
    }
    
    if (sessions.length === 0) {
      html = '<div class="no-history">No chat history yet</div>';
    } else {
      html += renderSection('Today', today, 'today', false, false);
      html += renderSection('Yesterday', yesterday, 'yesterday', false, true);
      html += renderSection('Older', older, 'older', false, true);
    }
    
    sidebarHistory.innerHTML = html;
    
    // Fetch and render others' chats in separate section
    const othersHistory = document.getElementById('others-history');
    let othersHtml = '';
    
    const othersChats = await fetchAllUsersChats();
    if (othersChats.length > 0) {
      // Render all others' chats without date grouping
      othersChats.forEach(chat => {
        const displayTitle = chat.title.length > 40 ? chat.title.substring(0, 40) + '...' : chat.title;
        const isActive = chat.session_id === activeSessionId;
        othersHtml += `
          <div class="history-item others-item ${isActive ? 'active' : ''}" data-session-id="${chat.session_id}" data-is-others="true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span class="history-item-title">${displayTitle}</span>
          </div>
        `;
      });
    } else {
      othersHtml = '<div class="no-history">No others\' chats yet</div>';
    }
    
    if (othersHistory) {
      othersHistory.innerHTML = othersHtml;
    }
    
    // Add click handlers for both my chats and others' chats
    const allHistoryItems = [...Array.from(sidebarHistory.querySelectorAll('.history-item')), 
                             ...(othersHistory ? Array.from(othersHistory.querySelectorAll('.history-item')) : [])];
    
    allHistoryItems.forEach(item => {
      const sessionEl = item as HTMLElement;
      const sid = sessionEl.dataset.sessionId;
      const isOthers = sessionEl.dataset.isOthers === 'true';
      
      sessionEl.addEventListener('click', (e) => {
        const target = e.target as HTMLElement;
        if (target.closest('.history-item-delete')) return;
        
        // Update active state immediately for visual feedback
        allHistoryItems.forEach(item => {
          (item as HTMLElement).classList.remove('active');
        });
        sessionEl.classList.add('active');
        
        if (isOthers) {
          // For others' chats, load in read-only mode
          loadOthersSession(sid!);
        } else {
          const session = sessions.find(s => s.id === sid);
          if (session) {
            loadSession(session, false);
          }
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
    
    // Add toggle handlers for section collapse/expand
    sidebarHistory.querySelectorAll('.section-toggle-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const sectionId = (btn as HTMLElement).dataset.sectionId;
        if (!sectionId) return;
        
        const content = sidebarHistory.querySelector(`.history-section-content[data-section-id="${sectionId}"]`);
        const icon = btn.querySelector('.toggle-icon');
        
        if (content && icon) {
          const isCollapsed = content.classList.contains('collapsed');
          
          if (isCollapsed) {
            content.classList.remove('collapsed');
            icon.classList.remove('collapsed');
            localStorage.removeItem(`section_collapsed_${sectionId}`);
            btn.setAttribute('title', 'Collapse');
          } else {
            content.classList.add('collapsed');
            icon.classList.add('collapsed');
            localStorage.setItem(`section_collapsed_${sectionId}`, 'true');
            btn.setAttribute('title', 'Expand');
          }
        }
      });
    });
  }
  
  // Delete a session (soft delete - moves to deleted collection)
  function deleteSession(sid: string) {
    if (!confirm('Delete this chat?')) return;
    
    let sessions = getAllSessions();
    const sessionToDelete = sessions.find(s => s.id === sid);
    
    if (sessionToDelete) {
      // Add deleted timestamp to the session
      const deletedSession = {
        ...sessionToDelete,
        deletedAt: Date.now()
      };
      
      // Move to deleted collection
      const deletedSessions = getDeletedSessions();
      deletedSessions.push(deletedSession);
      saveDeletedSessions(deletedSessions);
      
      console.log('[DELETED_SESSIONS] Moved session to deleted collection:', sid);
    }
    
    // Remove from active sessions
    sessions = sessions.filter(s => s.id !== sid);
    saveAllSessions(sessions);
    
    // If deleted current session, create new one
    if (sid === sessionId) {
      handleNewChat();
    } else {
      renderSessionHistory().catch(err => console.error('[SESSION] Failed to render history:', err));
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
      const lines = text.split('\n');
      let inList = false;
      let inOrderedList = false;
      let result = [];
      
      for (let line of lines) {
        // Check for unordered list item
        if (line.match(/^\* /)) {
          if (!inList) {
            result.push('<ul>');
            inList = true;
          }
          result.push(line.replace(/^\* (.*)$/, '<li>$1</li>'));
        }
        // Check for ordered list item
        else if (line.match(/^\d+\. /)) {
          if (!inOrderedList) {
            result.push('<ol>');
            inOrderedList = true;
          }
          result.push(line.replace(/^\d+\. (.*)$/, '<li>$1</li>'));
        }
        // Not a list item
        else {
          // Close any open lists
          if (inList) {
            result.push('</ul>');
            inList = false;
          }
          if (inOrderedList) {
            result.push('</ol>');
            inOrderedList = false;
          }
          
          // Format the line
          let formattedLine = line
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
          
          // Handle headings
          if (line.match(/^### /)) {
            formattedLine = line.replace(/^### (.*)$/, '<h3>$1</h3>');
          } else if (line.match(/^## /)) {
            formattedLine = line.replace(/^## (.*)$/, '<h2>$1</h2>');
          } else if (line.match(/^# /)) {
            formattedLine = line.replace(/^# (.*)$/, '<h1>$1</h1>');
          } else if (line.trim() !== '') {
            formattedLine = '<p>' + formattedLine + '</p>';
          } else {
            formattedLine = '';
          }
          
          if (formattedLine) result.push(formattedLine);
        }
      }
      
      // Close any remaining open lists
      if (inList) result.push('</ul>');
      if (inOrderedList) result.push('</ol>');
      
      html = result.join('\n');
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
    // Prevent multiple simultaneous requests
    if (isGenerating) return;
    
    const question = input.value.trim();
    if (!question) return;

    // Validate prompt length
    if (question.length > MAX_PROMPT_LENGTH) {
      const tokens = Math.round(question.length / 4);
      alert(`⚠️ Message is too long!\n\nYour message: ~${tokens.toLocaleString()} tokens (${question.length.toLocaleString()} characters)\nMaximum allowed: 5,000 tokens (20,000 characters)\n\nPlease shorten your message or split it into multiple parts.`);
      return;
    }
    
    // Show warning for large prompts
    if (question.length > WARN_PROMPT_LENGTH) {
      const tokens = Math.round(question.length / 4);
      const proceed = confirm(`⚠️ Large Message Warning\n\nYour message is approximately ${tokens.toLocaleString()} tokens (${question.length.toLocaleString()} characters).\n\nLarge messages may:\n• Take longer to process\n• Produce less focused responses\n\nDo you want to continue?`);
      if (!proceed) return;
    }

    // Remove all previous recommended questions when user types a new query
    const allRecommendations = messagesDiv!.querySelectorAll('.recommended-questions');
    allRecommendations.forEach(rec => rec.remove());

    addMessage(question, "user");
    input.value = "";
    // Reset textarea height after sending
    input.style.height = '24px';
    
    // Hide character counter after sending
    const counter = document.getElementById('char-counter');
    if (counter) counter.style.display = 'none';
    
    // Save session after user message
    saveCurrentSession();
    
    await sendMessageText(question);
  }

  async function sendMessageText(question: string) {
    if (!question) return;
    
    // Prevent multiple simultaneous requests
    if (isGenerating) return;
    
    // Disable send buttons while generating
    setGeneratingState(true);

    const botDiv = addMessageHTML("", "bot", null);
    
    // Status update function - simplified for better performance
    let isStreamingStatus = false;
    
    const updateThinkingStatus = (status: string, message: string) => {
      // Skip if already showing content or if we're done with thinking phase
      if (isStreamingStatus) return;
      
      // Update status immediately without word-by-word animation
      botDiv.innerHTML = `
        <div class="thinking">
          ${message}
          <span class="thinking-dots">
            <span></span>
            <span></span>
            <span></span>
          </span>
        </div>
      `;
      autoScrollToBottom();
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
                // Update thinking status with backend progress
                updateThinkingStatus(data.status, data.message);
              } else if (data.type === 'thinking_complete') {
                // Mark that we're done with thinking phase and starting content
                isStreamingStatus = true;
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
                
                // Re-enable send buttons after response complete
                setGeneratingState(false);
                
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
      // Re-enable send buttons after error
      setGeneratingState(false);
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
    // Prevent multiple simultaneous requests
    if (isGenerating) return;
    
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
    // Prevent multiple simultaneous requests
    if (isGenerating) return;
    
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

  // ============================================================================
  // DYNAMIC SUGGESTED QUESTIONS SYSTEM
  // ============================================================================
  
  // Fetch suggested questions from API
  async function loadSuggestedQuestions() {
    try {
      console.log('[QUESTIONS] Loading dynamic suggested questions...');
      const response = await fetch(`${getApiBase()}/api/suggested-questions?limit=4`);
      
      if (!response.ok) {
        console.error('[QUESTIONS] Failed to load questions:', response.status);
        return;
      }
      
      const questions = await response.json();
      console.log('[QUESTIONS] Loaded', questions.length, 'questions');
      updateSuggestedQuestions(questions);
    } catch (error) {
      console.error('[QUESTIONS] Error loading questions:', error);
    }
  }
  
  // Update both suggested questions containers
  function updateSuggestedQuestions(questions: any[]) {
    const containers = [
      document.getElementById('suggested-questions-empty'),
      document.getElementById('suggested-questions-main')
    ];
    
    containers.forEach(container => {
      if (!container || !questions || questions.length === 0) return;
      
      const html = questions.map((q: any) => `
        <button class="suggested-question-btn" 
                data-question="${q.question_text.replace(/"/g, '&quot;')}"
                data-question-id="${q.id}">
          ${q.question_text}
        </button>
      `).join('');
      
      container.innerHTML = html;
    });
    
    // Re-attach event listeners for new buttons
    attachSuggestedQuestionListeners();
  }
  
  // Attach click handlers to suggested question buttons
  function attachSuggestedQuestionListeners() {
    const buttons = document.querySelectorAll('.suggested-question-btn');
    
    buttons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const button = e.target as HTMLButtonElement;
        const question = button.getAttribute('data-question');
        const questionId = button.getAttribute('data-question-id');
        
        if (question) {
          // Track click for analytics
          if (questionId) {
            trackQuestionClick(questionId);
          }
          
          // Remove all previous recommended questions
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
  }
  
  // Track question click for analytics (optional - silently fails if endpoint not available)
  function trackQuestionClick(questionId: string) {
    // Disabled for now - analytics endpoint not implemented yet
    // fetch(`${getApiBase()}/api/suggested-questions/analytics`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     action: 'click',
    //     question_id: questionId
    //   })
    // }).catch(err => console.error('[ANALYTICS] Failed to track click:', err));
    console.log('[ANALYTICS] Question clicked:', questionId);
  }
  
  // ============================================================================
  // AUTHENTICATION & INITIALIZATION
  // ============================================================================
  
  // Initialize auth - simplified since auth check is done at component level
  function initAuth() {
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    
    // User is already authenticated at this point (checked in component)
    // Just load user info and chat history
    if (user && user.access_token) {
    updateUserInfo(user);
      
      // Add test data for UI testing (comment out in production)
      addTestSessions();
      
      // Load dynamic suggested questions
      loadSuggestedQuestions();
      
      // Load session history in sidebar (async)
      renderSessionHistory().catch(err => console.error('[SESSION] Failed to render history:', err));
      
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
    activeSessionId = sessionId;
    currentSessionTitle = '';
    localStorage.setItem(getUserStorageKey('chatbot_session_id'), sessionId);
    
    // Clear messages
    messagesDiv!.innerHTML = '';
    updateEmptyState();
    
    // Update sidebar to show new session is active (async with error handling)
    renderSessionHistory().catch(err => console.error('[SESSION] Failed to render history:', err));
    
    // Show success state briefly with visual feedback
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
    // Auto-expand textarea and handle character validation
    input.addEventListener("input", (e) => {
      const target = e.target as HTMLTextAreaElement;
      target.style.height = '24px';
      target.style.height = Math.min(target.scrollHeight, 200) + 'px';
      
      // Character counter and button validation
      const counter = document.getElementById('char-counter');
      const sendButton = document.getElementById('send-btn') as HTMLButtonElement;
      const tooltip = document.getElementById('tooltip-main');
      const length = target.value.length;
      const exceeded = length >= MAX_PROMPT_LENGTH;
      
      // Show counter when approaching limit
      if (counter && length >= WARN_PROMPT_LENGTH) {
        counter.textContent = `${length.toLocaleString()} / ${MAX_PROMPT_LENGTH.toLocaleString()}`;
        counter.style.display = 'block';
        // Color coding: red when exceeded, orange when close, gray otherwise
        counter.style.color = exceeded ? '#ef4444' : (length > 18000 ? '#f59e0b' : '#6b7280');
      } else if (counter) {
        counter.style.display = 'none';
      }
      
      // Disable button if limit exceeded
      if (sendButton) {
        sendButton.disabled = exceeded;
        sendButton.style.opacity = exceeded ? '0.5' : '1';
        sendButton.style.cursor = exceeded ? 'not-allowed' : 'pointer';
        sendButton.style.backgroundColor = exceeded ? '#9ca3af' : '';
        
        // Show tooltip on hover when disabled
        if (exceeded) {
          sendButton.onmouseenter = () => { if (tooltip) tooltip.style.display = 'block'; };
          sendButton.onmouseleave = () => { if (tooltip) tooltip.style.display = 'none'; };
        } else {
          sendButton.onmouseenter = null;
          sendButton.onmouseleave = null;
          if (tooltip) tooltip.style.display = 'none';
        }
      }
    });
    
    // Handle Enter key
    input.addEventListener("keydown", (e) => { 
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        const btn = document.getElementById('send-btn') as HTMLButtonElement;
        if (btn && !btn.disabled) {
          btn.click();
        }
      }
    });
  }

  // Event listeners for empty state input (center)
  if (sendBtnEmptyState) {
    sendBtnEmptyState.addEventListener("click", () => {
      // Prevent multiple simultaneous requests
      if (isGenerating) return;
      
      if (inputEmptyState) {
        const question = inputEmptyState.value.trim();
        if (question) {
          // Validate prompt length
          if (question.length > MAX_PROMPT_LENGTH) {
            const tokens = Math.round(question.length / 4);
            alert(`⚠️ Message is too long!\n\nYour message: ~${tokens.toLocaleString()} tokens (${question.length.toLocaleString()} characters)\nMaximum allowed: 5,000 tokens (20,000 characters)\n\nPlease shorten your message or split it into multiple parts.`);
            return;
          }
          
          // Show warning for large prompts
          if (question.length > WARN_PROMPT_LENGTH) {
            const tokens = Math.round(question.length / 4);
            const proceed = confirm(`⚠️ Large Message Warning\n\nYour message is approximately ${tokens.toLocaleString()} tokens (${question.length.toLocaleString()} characters).\n\nLarge messages may:\n• Take longer to process\n• Produce less focused responses\n\nDo you want to continue?`);
            if (!proceed) return;
          }
          
          addMessage(question, "user");
          inputEmptyState.value = "";
          inputEmptyState.style.height = '24px';
          
          // Hide character counter after sending
          const counter = document.getElementById('char-counter-empty');
          if (counter) counter.style.display = 'none';
          
          sendMessageText(question);
        }
      }
    });
  }
  
  if (inputEmptyState) {
    // Auto-expand textarea and handle character validation
    inputEmptyState.addEventListener("input", (e) => {
      const target = e.target as HTMLTextAreaElement;
      target.style.height = '24px';
      target.style.height = Math.min(target.scrollHeight, 200) + 'px';
      
      // Character counter and button validation
      const counter = document.getElementById('char-counter-empty');
      const sendButton = document.getElementById('send-btn-empty') as HTMLButtonElement;
      const tooltip = document.getElementById('tooltip-empty');
      const length = target.value.length;
      const exceeded = length >= MAX_PROMPT_LENGTH;
      
      // Show counter when approaching limit
      if (counter && length >= WARN_PROMPT_LENGTH) {
        counter.textContent = `${length.toLocaleString()} / ${MAX_PROMPT_LENGTH.toLocaleString()}`;
        counter.style.display = 'block';
        // Color coding: red when exceeded, orange when close, gray otherwise
        counter.style.color = exceeded ? '#ef4444' : (length > 18000 ? '#f59e0b' : '#6b7280');
      } else if (counter) {
        counter.style.display = 'none';
      }
      
      // Disable button if limit exceeded
      if (sendButton) {
        sendButton.disabled = exceeded;
        sendButton.style.opacity = exceeded ? '0.5' : '1';
        sendButton.style.cursor = exceeded ? 'not-allowed' : 'pointer';
        sendButton.style.backgroundColor = exceeded ? '#9ca3af' : '';
        
        // Show tooltip on hover when disabled
        if (exceeded) {
          sendButton.onmouseenter = () => { if (tooltip) tooltip.style.display = 'block'; };
          sendButton.onmouseleave = () => { if (tooltip) tooltip.style.display = 'none'; };
        } else {
          sendButton.onmouseenter = null;
          sendButton.onmouseleave = null;
          if (tooltip) tooltip.style.display = 'none';
        }
      }
    });
    
    // Handle Enter key
    inputEmptyState.addEventListener("keydown", (e) => { 
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        const btn = sendBtnEmptyState as HTMLButtonElement;
        if (btn && !btn.disabled) {
          btn.click();
        }
      }
    });
  }
  
  // Event listeners for suggested question buttons
  const suggestedQuestionBtns = document.querySelectorAll('.suggested-question-btn');
  suggestedQuestionBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      // Prevent multiple simultaneous requests
      if (isGenerating) return;
      
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
