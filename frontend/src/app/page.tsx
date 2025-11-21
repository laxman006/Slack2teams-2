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
  }
}

export default function ChatPage() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

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
    <>
      <header>
        <Image src="/images/CloudFuze Horizontal Logo.svg" alt="Logo" width={150} height={40} priority />
        <div className="header-controls">
          <button className="new-chat-btn" id="newChatBtn">
            <span>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg" className="icon" aria-hidden="true">
                <path d="M2.6687 11.333V8.66699C2.6687 7.74455 2.66841 7.01205 2.71655 6.42285C2.76533 5.82612 2.86699 5.31731 3.10425 4.85156L3.25854 4.57617C3.64272 3.94975 4.19392 3.43995 4.85229 3.10449L5.02905 3.02149C5.44666 2.84233 5.90133 2.75849 6.42358 2.71582C7.01272 2.66769 7.74445 2.66797 8.66675 2.66797H9.16675C9.53393 2.66797 9.83165 2.96586 9.83179 3.33301C9.83179 3.70028 9.53402 3.99805 9.16675 3.99805H8.66675C7.7226 3.99805 7.05438 3.99834 6.53198 4.04102C6.14611 4.07254 5.87277 4.12568 5.65601 4.20313L5.45581 4.28906C5.01645 4.51293 4.64872 4.85345 4.39233 5.27149L4.28979 5.45508C4.16388 5.7022 4.08381 6.01663 4.04175 6.53125C3.99906 7.05373 3.99878 7.7226 3.99878 8.66699V11.333C3.99878 12.2774 3.99906 12.9463 4.04175 13.4688C4.08381 13.9833 4.16389 14.2978 4.28979 14.5449L4.39233 14.7285C4.64871 15.1465 5.01648 15.4871 5.45581 15.7109L5.65601 15.7969C5.87276 15.8743 6.14614 15.9265 6.53198 15.958C7.05439 16.0007 7.72256 16.002 8.66675 16.002H11.3337C12.2779 16.002 12.9461 16.0007 13.4685 15.958C13.9829 15.916 14.2976 15.8367 14.5447 15.7109L14.7292 15.6074C15.147 15.3511 15.4879 14.9841 15.7117 14.5449L15.7976 14.3447C15.8751 14.128 15.9272 13.8546 15.9587 13.4688C16.0014 12.9463 16.0017 12.2774 16.0017 11.333V10.833C16.0018 10.466 16.2997 10.1681 16.6667 10.168C17.0339 10.168 17.3316 10.4659 17.3318 10.833V11.333C17.3318 12.2555 17.3331 12.9879 17.2849 13.5771C17.2422 14.0993 17.1584 14.5541 16.9792 14.9717L16.8962 15.1484C16.5609 15.8066 16.0507 16.3571 15.4246 16.7412L15.1492 16.8955C14.6833 17.1329 14.1739 17.2354 13.5769 17.2842C12.9878 17.3323 12.256 17.332 11.3337 17.332H8.66675C7.74446 17.332 7.01271 17.3323 6.42358 17.2842C5.90135 17.2415 5.44665 17.1577 5.02905 16.9785L4.85229 16.8955C4.19396 16.5601 3.64271 16.0502 3.25854 15.4238L3.10425 15.1484C2.86697 14.6827 2.76534 14.1739 2.71655 13.5771C2.66841 12.9879 2.6687 12.2555 2.6687 11.333ZM13.4646 3.11328C14.4201 2.334 15.8288 2.38969 16.7195 3.28027L16.8865 3.46485C17.6141 4.35685 17.6143 5.64423 16.8865 6.53613L16.7195 6.7207L11.6726 11.7686C11.1373 12.3039 10.4624 12.6746 9.72827 12.8408L9.41089 12.8994L7.59351 13.1582C7.38637 13.1877 7.17701 13.1187 7.02905 12.9707C6.88112 12.8227 6.81199 12.6134 6.84155 12.4063L7.10132 10.5898L7.15991 10.2715C7.3262 9.53749 7.69692 8.86241 8.23218 8.32715L13.2791 3.28027L13.4646 3.11328ZM15.7791 4.2207C15.3753 3.81702 14.7366 3.79124 14.3035 4.14453L14.2195 4.2207L9.17261 9.26856C8.81541 9.62578 8.56774 10.0756 8.45679 10.5654L8.41772 10.7773L8.28296 11.7158L9.22241 11.582L9.43433 11.543C9.92426 11.432 10.3749 11.1844 10.7322 10.8271L15.7791 5.78027L15.8552 5.69629C16.185 5.29194 16.1852 4.708 15.8552 4.30371L15.7791 4.2207Z"></path>
              </svg>
            </span>
            <span>New Chat</span>
          </button>
          <div className="user-menu" id="userMenu">
            <div className="user-info">
              <div className="user-avatar" id="userAvatar">U</div>
              <span className="user-name" id="userName">User</span>
              <div className="dropdown-arrow"></div>
            </div>
            <div className="user-dropdown" id="userDropdown">
              <div className="dropdown-item" id="userEmail"></div>
              <div className="dropdown-item logout" id="logoutBtn">
                <span>
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg" className="icon" aria-hidden="true">
                    <path d="M3.50171 12.6663V7.33333C3.50171 6.64424 3.50106 6.08728 3.53784 5.63704C3.57525 5.17925 3.65463 4.77342 3.84644 4.39681L3.96851 4.17806C4.2726 3.68235 4.70919 3.2785 5.23023 3.01302L5.3728 2.94661C5.7091 2.80238 6.06981 2.73717 6.47046 2.70443C6.9207 2.66764 7.47766 2.66829 8.16675 2.66829H9.16675L9.30054 2.68197C9.60367 2.7439 9.83179 3.0119 9.83179 3.33333C9.83179 3.65476 9.60367 3.92277 9.30054 3.9847L9.16675 3.99837H8.16675C7.45571 3.99837 6.96238 3.99926 6.57886 4.0306C6.297 4.05363 6.10737 4.09049 5.96362 4.14193L5.83374 4.19857C5.53148 4.35259 5.27861 4.58671 5.1023 4.87435L5.03198 5.00032C4.95147 5.15833 4.89472 5.36974 4.86401 5.74544C4.83268 6.12896 4.83179 6.6223 4.83179 7.33333V12.6663C4.83179 13.3772 4.8327 13.8707 4.86401 14.2542C4.8947 14.6298 4.95153 14.8414 5.03198 14.9993L5.1023 15.1263C5.27861 15.4137 5.53163 15.6482 5.83374 15.8021L5.96362 15.8577C6.1074 15.9092 6.29691 15.947 6.57886 15.9701C6.96238 16.0014 7.45571 16.0013 8.16675 16.0013H9.16675L9.30054 16.015C9.6036 16.0769 9.83163 16.345 9.83179 16.6663C9.83179 16.9877 9.60363 17.2558 9.30054 17.3177L9.16675 17.3314H8.16675C7.47766 17.3314 6.9207 17.332 6.47046 17.2952C6.06978 17.2625 5.70912 17.1973 5.3728 17.0531L5.23023 16.9867C4.70911 16.7211 4.27261 16.3174 3.96851 15.8216L3.84644 15.6038C3.65447 15.2271 3.57526 14.8206 3.53784 14.3626C3.50107 13.9124 3.50171 13.3553 3.50171 12.6663ZM13.8035 13.804C13.5438 14.0634 13.1226 14.0635 12.863 13.804C12.6033 13.5443 12.6033 13.1223 12.863 12.8626L13.8035 13.804ZM12.863 6.19661C13.0903 5.96939 13.4409 5.94126 13.699 6.11165L13.8035 6.19661L17.1375 9.52962C17.3969 9.78923 17.3968 10.2104 17.1375 10.4701L13.8035 13.804L13.3337 13.3333L12.863 12.8626L15.0603 10.6654H9.16675C8.79959 10.6654 8.50189 10.3674 8.50171 10.0003C8.50171 9.63306 8.79948 9.33529 9.16675 9.33529H15.0613L12.863 7.13704L12.7781 7.03255C12.6077 6.77449 12.6359 6.42386 12.863 6.19661Z"></path>
                  </svg>
                </span>
                <span>Logout</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="main-content">
        <div id="messages"></div>
      </div>

      <button id="scroll-to-bottom-btn" title="Scroll to bottom">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path d="M9.33468 3.33333C9.33468 2.96617 9.6326 2.66847 9.99972 2.66829C10.367 2.66829 10.6648 2.96606 10.6648 3.33333V15.0609L15.363 10.3626L15.4675 10.2777C15.7255 10.1074 16.0762 10.1357 16.3034 10.3626C16.5631 10.6223 16.5631 11.0443 16.3034 11.304L10.4704 17.137C10.2108 17.3967 9.7897 17.3966 9.52999 17.137L3.69601 11.304L3.61105 11.1995C3.44054 10.9414 3.46874 10.5899 3.69601 10.3626C3.92328 10.1354 4.27479 10.1072 4.53292 10.2777L4.63741 10.3626L9.33468 15.0599V3.33333Z"></path>
        </svg>
      </button>

        <div id="input-container">
          <div className="input-wrapper">
            <input type="text" id="user-input" placeholder="Ask me anything about CloudFuze..." />
          <button id="send-btn">
            <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 24 24" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg">
              <path fill="none" d="M0 0h24v24H0z"></path>
              <path d="M2.01 21 23 12 2.01 3 2 10l15 2-15 2z"></path>
            </svg>
          </button>
        </div>
    </div>
    </>
  );
}

function initializeChatApp() {
  // Make functions globally available
  window.copyMessage = copyMessage;
  window.submitFeedback = submitFeedback;
  window.editMessage = editMessage;
  window.cancelEdit = cancelEdit;
  window.saveEdit = saveEdit;
  window.askRecommendedQuestion = askRecommendedQuestion;

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
  const input = document.getElementById("user-input") as HTMLInputElement;
  const sendBtn = document.getElementById("send-btn");

  
  // Generate a session ID for conversation memory and Langfuse tracking
  let sessionId = localStorage.getItem('chatbot_session_id');
  if (!sessionId) {
    // Create readable session format: cf.conversation.YYYYMMDD.randomId
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const randomId = Math.random().toString(36).substr(2, 9);
    sessionId = `cf.conversation.${date}.${randomId}`;
    localStorage.setItem('chatbot_session_id', sessionId);
    console.log('[SESSION] Created new session:', sessionId);
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
          <button class="edit-btn" onclick="editMessage(this)" title="Edit message">
            <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
            </svg>
          </button>
        </div>
      `;
      messagesDiv!.appendChild(wrapper);
      console.log(`[UI] Added ${sender} message. Total messages now: ${messagesDiv!.children.length}`);
      scrollToBottom();
      return wrapper;
    } else {
      // For bot messages, keep simple structure
      const div = document.createElement("div");
      div.className = "message " + sender;
      div.innerText = content;
      messagesDiv!.appendChild(div);
      console.log(`[UI] Added ${sender} message. Total messages now: ${messagesDiv!.children.length}`);
      scrollToBottom();
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
          <button class="copy-button" onclick="copyMessage(this)" title="Copy message">
            <img src="/images/copy-icon.svg?v=2" alt="Copy" width="16" height="16">
          </button>
          <button class="feedback-btn thumbs-up" onclick="submitFeedback(this, 'thumbs_up')" title="Good response">
            <img src="/images/thumbs-up-icon.svg?v=2" alt="Thumbs up" width="16" height="16">
          </button>
          <button class="feedback-btn thumbs-down" onclick="submitFeedback(this, 'thumbs_down')" title="Bad response">
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
    scrollToBottom();
    return div;
  }

  function renderMarkdown(text: string) {
    if (typeof window.marked !== 'undefined') {
      return window.marked.parse(text);
    } else {
      // Fallback: basic markdown-like formatting
      return text
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
  }

  // [REST OF THE JAVASCRIPT CODE WILL CONTINUE IN NEXT MESSAGE DUE TO LENGTH]
  // For now, let me create a simplified version that makes it work

  function scrollToBottom() {
    requestAnimationFrame(() => {
      window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
      });
    });
  }

  async function sendMessage() {
    const question = input.value.trim();
    if (!question) return;

    // Remove all previous recommended questions when user types a new query
    const allRecommendations = messagesDiv!.querySelectorAll('.recommended-questions');
    allRecommendations.forEach(rec => rec.remove());

    addMessage(question, "user");
    input.value = "";
    
    await sendMessageText(question);
  }

  async function sendMessageText(question: string) {
    if (!question) return;

    const botDiv = addMessageHTML("", "bot", null);
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

    setTimeout(() => scrollToBottom(), 50);

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
              
              if (data.type === 'thinking_complete') {
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
                  scrollToBottom();
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
                    <button class="copy-button" onclick="copyMessage(this)" title="Copy message">
                      <img src="/images/copy-icon.svg?v=2" alt="Copy" width="16" height="16">
                    </button>
                    <button class="feedback-btn thumbs-up" onclick="submitFeedback(this, 'thumbs_up')" title="Good response">
                      <img src="/images/thumbs-up-icon.svg?v=2" alt="Thumbs up" width="16" height="16">
                    </button>
                    <button class="feedback-btn thumbs-down" onclick="submitFeedback(this, 'thumbs_down')" title="Bad response">
                      <img src="/images/thumbs-down-icon.svg?v=2" alt="Thumbs down" width="16" height="16">
                    </button>
                    <span class="feedback-text"></span>
                  </div>
                  ${recommendedQuestionsHTML}
                `;
                
                if (traceId) {
                  botDiv.dataset.traceId = traceId;
                }
                
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
      const originalHTML = button.innerHTML;
      button.innerHTML = '<span style="color: #10a37f;">✓</span>';
      button.classList.add('copied');
      
      setTimeout(() => {
        button.innerHTML = originalHTML;
        button.classList.remove('copied');
      }, 2000);
    }).catch(err => {
      console.error('Failed to copy text: ', err);
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
          comment: ""
        }),
      });
      
      if (response.ok) {
        messageDiv.dataset.feedbackSubmitted = 'true';
        feedbackButtons.forEach((btn) => btn.classList.remove('selected'));
        button.classList.add('selected');
        
        const feedbackText = messageDiv.querySelector('.feedback-text')!;
        feedbackText.textContent = rating === 'thumbs_up' ? 'Thanks for your feedback!' : 'Thanks! We\'ll improve.';
        
        setTimeout(() => {
          feedbackText.textContent = '';
        }, 3000);
      }
    } catch (error) {
      console.error("Error submitting feedback:", error);
    }
  }

  function editMessage(_button: HTMLElement) {
    // Simplified edit functionality - will be implemented later
    console.log('Edit message clicked');
  }

  function cancelEdit(_button: HTMLElement) {
    // Simplified cancel edit - will be implemented later
    console.log('Cancel edit clicked');
  }

  function saveEdit(_button: HTMLElement) {
    // Simplified save edit - will be implemented later
    console.log('Save edit clicked');
  }

  // Initialize auth - simplified since auth check is done at component level
  function initAuth() {
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    
    // User is already authenticated at this point (checked in component)
    // Just load user info and chat history
    if (user && user.access_token) {
      updateUserInfo(user);
      loadUserChatHistory(user.id, user.access_token);
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
    
    if (user) {
      userName!.textContent = user.name || 'User';
      userAvatar!.textContent = (user.name || 'U').charAt(0).toUpperCase();
      userEmail!.textContent = user.email || '';
    }
  }

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
                  <button class="copy-button" onclick="copyMessage(this)" title="Copy message">
                    <img src="/images/copy-icon.svg?v=2" alt="Copy" width="16" height="16">
                  </button>
                  <button class="feedback-btn thumbs-up" onclick="submitFeedback(this, 'thumbs_up')" title="Good response">
                    <img src="/images/thumbs-up-icon.svg?v=2" alt="Thumbs up" width="16" height="16">
                  </button>
                  <button class="feedback-btn thumbs-down" onclick="submitFeedback(this, 'thumbs_down')" title="Bad response">
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
    
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const randomId = Math.random().toString(36).substr(2, 9);
    sessionId = `cf.conversation.${date}.${randomId}`;
    localStorage.setItem('chatbot_session_id', sessionId);
    messagesDiv!.innerHTML = '';
  }

  function handleLogout() {
    localStorage.removeItem('user');
    window.location.href = "/login";
  }

  function toggleDropdown() {
    const dropdown = document.getElementById('userDropdown');
    dropdown!.classList.toggle('show');
  }

  // Event listeners
  sendBtn!.addEventListener("click", sendMessage);
  input!.addEventListener("keypress", (e) => { if (e.key === "Enter") sendMessage(); });
  document.getElementById('newChatBtn')!.addEventListener('click', handleNewChat);
  document.getElementById('userMenu')!.addEventListener('click', toggleDropdown);
  document.getElementById('logoutBtn')!.addEventListener('click', handleLogout);
  
  document.addEventListener('click', (event) => {
    const userMenu = document.getElementById('userMenu');
    const dropdown = document.getElementById('userDropdown');
    
    if (!userMenu!.contains(event.target as Node)) {
      dropdown!.classList.remove('show');
    }
  });

  initAuth();
}
