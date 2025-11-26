'use client';

import { useEffect } from 'react';
import Image from 'next/image';

export default function LoginPage() {
  useEffect(() => {
    initializeLoginPage();
  }, []);

  return (
    <>
      <header>
        <Image src="/images/CloudFuze Horizontal Logo.svg" alt="CloudFuze Logo" width={150} height={40} priority />
      </header>

      <div className="main-content">
        <div className="login-container">
          <h1 className="login-title">Welcome to CF Chatbot</h1>
          <p className="login-subtitle">Please sign in to continue</p>
          <button id="microsoftLogin" className="login-btn">
            <svg className="provider-icon" viewBox="0 0 24 24">
              <path fill="currentColor" d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zM24 11.4H12.6V0H24v11.4z"/>
            </svg>
            Sign in with Microsoft
          </button>
        </div>
      </div>
    </>
  );
}

function initializeLoginPage() {
  // Microsoft OAuth configuration
  let MICROSOFT_CLIENT_ID: string | null = null;
  let MICROSOFT_TENANT = "cloudfuze.com";
  const MICROSOFT_REDIRECT_URI = window.location.origin + '/login';
  const MICROSOFT_SCOPE = "openid email profile User.Read";

  // API Base URL configuration
  function getApiBase() {
    const hostname = window.location.hostname;
    
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8002';
    }
    
    return window.location.origin;
  }

  // Load Microsoft OAuth configuration from backend
  async function loadOAuthConfig() {
    try {
      const response = await fetch(`${getApiBase()}/auth/config`);
      if (response.ok) {
        const config = await response.json();
        MICROSOFT_CLIENT_ID = config.client_id;
        MICROSOFT_TENANT = config.tenant || "cloudfuze.com";
        console.log('[AUTH] Loaded OAuth config:', { client_id: MICROSOFT_CLIENT_ID, tenant: MICROSOFT_TENANT });
      } else {
        throw new Error('Failed to load OAuth configuration');
      }
    } catch (error) {
      console.error('[AUTH] Error loading OAuth config:', error);
      MICROSOFT_CLIENT_ID = process.env.NEXT_PUBLIC_MICROSOFT_CLIENT_ID || "861e696d-f41c-41ee-a7c2-c838fd185d6d";
      console.log('[AUTH] Using fallback client ID');
    }
  }

  // PKCE helper functions
  function generateCodeVerifier() {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return base64URLEncode(array);
  }

  async function generateCodeChallenge(verifier: string) {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const hash = await crypto.subtle.digest('SHA-256', data);
    return base64URLEncode(new Uint8Array(hash));
  }

  function base64URLEncode(array: Uint8Array) {
    return btoa(String.fromCharCode.apply(null, Array.from(array)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }

  // Check if user is already logged in
  function checkAuthStatus() {
    // Don't check auth status if we're currently processing an OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('code')) {
      console.log('OAuth callback in progress, skipping auth check');
      return;
    }
    
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (user && user.access_token) {
      console.log('User found in localStorage, verifying token...');
      
      showLoadingIndicator('Checking authentication...');
      
      verifyToken(user.access_token).then(isValid => {
        hideLoadingIndicator();
        if (isValid) {
          console.log('Token is valid, redirecting to main page');
          window.location.href = "/";
        } else {
          console.log('Token is invalid, clearing user data');
          localStorage.removeItem('user');
          showError('Your session has expired. Please sign in again.');
        }
      }).catch(error => {
        console.error('Token verification failed:', error);
        hideLoadingIndicator();
        localStorage.removeItem('user');
        showError('Authentication check failed. Please sign in again.');
      });
    }
  }

  // Verify Microsoft access token
  async function verifyToken(accessToken: string) {
    try {
      const response = await fetch('https://graph.microsoft.com/v1.0/me', {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  // Microsoft login handler
  async function handleMicrosoftLogin(event: Event) {
    event.preventDefault();
    
    sessionStorage.removeItem('code_verifier');
    localStorage.removeItem('user');
    
    const button = event.target as HTMLButtonElement;
    const originalText = button.innerHTML;
    button.innerHTML = '<span>Signing in...</span>';
    button.disabled = true;
    
    const codeVerifier = generateCodeVerifier();
    const codeChallenge = await generateCodeChallenge(codeVerifier);
    
    sessionStorage.setItem('code_verifier', codeVerifier);
    sessionStorage.setItem('login_in_progress', 'true');
    
    const authUrl = `https://login.microsoftonline.com/${MICROSOFT_TENANT}/oauth2/v2.0/authorize?` +
      `client_id=${MICROSOFT_CLIENT_ID}&` +
      `response_type=code&` +
      `redirect_uri=${encodeURIComponent(MICROSOFT_REDIRECT_URI)}&` +
      `response_mode=query&` +
      `scope=${encodeURIComponent(MICROSOFT_SCOPE)}&` +
      `prompt=select_account&` +
      `code_challenge=${codeChallenge}&` +
      `code_challenge_method=S256&` +
      `state=${Date.now()}`;
    
    try {
      window.location.href = authUrl;
    } catch (error) {
      button.innerHTML = originalText;
      button.disabled = false;
      sessionStorage.removeItem('login_in_progress');
      showError('Failed to initiate login: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  }

  // Error display function
  function showError(message: string) {
    const existingError = document.querySelector('.error-message');
    if (existingError) {
      existingError.remove();
    }
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
      background: #fee;
      color: #c33;
      padding: 15px;
      border-radius: 10px;
      margin-top: 20px;
      border: 1px solid #fcc;
      font-size: 14px;
    `;
    errorDiv.innerHTML = message;
    document.querySelector('.login-container')!.appendChild(errorDiv);
    
    setTimeout(() => {
      if (errorDiv.parentNode) {
        errorDiv.remove();
      }
    }, 5000);
  }

  // Success display function
  function showSuccess(message: string) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.style.cssText = `
      background: #efe;
      color: #363;
      padding: 15px;
      border-radius: 10px;
      margin-top: 20px;
      border: 1px solid #cfc;
      font-size: 14px;
    `;
    successDiv.innerHTML = message;
    document.querySelector('.login-container')!.appendChild(successDiv);
  }

  // Loading indicator functions
  function showLoadingIndicator(message: string) {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loading-indicator';
    loadingDiv.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 20px 30px;
      border-radius: 8px;
      z-index: 10000;
      font-size: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
    `;
    loadingDiv.innerHTML = `
      <div style="width: 20px; height: 20px; border: 2px solid #fff; border-top: 2px solid transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
      ${message}
    `;
    document.body.appendChild(loadingDiv);
  }
  
  function hideLoadingIndicator() {
    const loadingDiv = document.getElementById('loading-indicator');
    if (loadingDiv) {
      loadingDiv.remove();
    }
  }

  // Handle OAuth callback
  function handleOAuthCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const error = urlParams.get('error');

    if (error) {
      console.log('OAuth error:', error);
      showError('Microsoft login failed: ' + error);
      return;
    }

    if (code) {
      console.log('OAuth code received, processing...');
      // Show loading indicator immediately and hide login form
      showLoadingIndicator('Completing sign-in...');
      const loginContainer = document.querySelector('.login-container') as HTMLElement;
      if (loginContainer) {
        loginContainer.style.display = 'none';
      }
      exchangeCodeForToken(code);
    }
  }

  // Exchange authorization code for access token
  async function exchangeCodeForToken(code: string) {
    const codeVerifier = sessionStorage.getItem('code_verifier');
    
    if (!codeVerifier) {
      console.log('Code verifier not found, starting fresh login flow...');
      hideLoadingIndicator();
      const loginContainer = document.querySelector('.login-container') as HTMLElement;
      if (loginContainer) {
        loginContainer.style.display = 'block';
      }
      localStorage.removeItem('user');
      window.history.replaceState({}, document.title, window.location.pathname);
      showSuccess('Starting fresh login...');
      setTimeout(() => {
        const loginButton = document.getElementById('microsoftLogin');
        if (loginButton) {
          loginButton.click();
        }
      }, 1000);
      return;
    }
    
    try {
      const requestBody = {
        code: code,
        redirect_uri: MICROSOFT_REDIRECT_URI,
        code_verifier: codeVerifier
      };
      const API_BASE = getApiBase();
      const CALLBACK_URL = `${API_BASE}/auth/microsoft/callback`;

      const response = await fetch(CALLBACK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        
        sessionStorage.removeItem('code_verifier');
        sessionStorage.removeItem('login_in_progress');
        
        const user = {
          id: data.user_id,
          name: data.name,
          email: data.email,
          access_token: data.access_token,
          refresh_token: data.refresh_token
        };
        
        localStorage.setItem('user', JSON.stringify(user));
        // Clear URL parameters before redirecting
        window.history.replaceState({}, document.title, window.location.pathname);
        // Redirect to main page
        window.location.href = "/";
      } else {
        const errorText = await response.text();
        console.log('Server error response:', errorText);
        hideLoadingIndicator();
        const loginContainer = document.querySelector('.login-container') as HTMLElement;
        if (loginContainer) {
          loginContainer.style.display = 'block';
        }
        
        if (errorText.includes('code_verifier') || errorText.includes('Code verifier')) {
          console.log('Code verifier error detected, starting fresh login...');
          localStorage.removeItem('user');
          window.history.replaceState({}, document.title, window.location.pathname);
          showSuccess('Starting fresh login...');
          setTimeout(() => {
            const loginButton = document.getElementById('microsoftLogin');
            if (loginButton) {
              loginButton.click();
            }
          }, 1000);
          return;
        }
        
        window.history.replaceState({}, document.title, window.location.pathname);
        showError('Login failed: ' + (errorText || 'Unknown error'));
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.log('Network or other error:', errorMessage);
      hideLoadingIndicator();
      const loginContainer = document.querySelector('.login-container') as HTMLElement;
      if (loginContainer) {
        loginContainer.style.display = 'block';
      }
      
      if (errorMessage.includes('code_verifier') || errorMessage.includes('Code verifier')) {
        console.log('Code verifier error detected in catch, starting fresh login...');
        localStorage.removeItem('user');
        window.history.replaceState({}, document.title, window.location.pathname);
        showSuccess('Starting fresh login...');
        setTimeout(() => {
          const loginButton = document.getElementById('microsoftLogin');
          if (loginButton) {
            loginButton.click();
          }
        }, 1000);
        return;
      }
      
      window.history.replaceState({}, document.title, window.location.pathname);
      showError('Login failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  }

  // Reset login button to original state
  function resetLoginButton() {
    const button = document.getElementById('microsoftLogin') as HTMLButtonElement;
    if (button) {
      sessionStorage.removeItem('login_in_progress');
      
      button.innerHTML = `
        <svg class="provider-icon" viewBox="0 0 24 24">
          <path fill="currentColor" d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zM24 11.4H12.6V0H24v11.4z"/>
        </svg>
        Sign in with Microsoft
      `;
      button.disabled = false;
    }
  }

  // Initialize when DOM is loaded
  resetLoginButton();
  
  loadOAuthConfig().then(() => {
    console.log('Login page initialized');
    console.log('Current hostname:', window.location.hostname);
    console.log('API Base URL:', getApiBase());
    
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const email = urlParams.get('email');
    
    if (error === 'unauthorized_domain') {
      const errorMessage = `⚠️ Access Denied\n\nOnly CloudFuze company accounts (@cloudfuze.com) are allowed to access this application.\n\n${email ? `Your email: ${decodeURIComponent(email)}` : ''}\n\nPlease log in with your CloudFuze account.`;
      showError(errorMessage.replace(/\n/g, '<br>'));
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (error === 'invalid_token' || error === 'session_expired') {
      showError('⚠️ Your session has expired. Please log in again.');
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (error === 'verification_failed') {
      showError('⚠️ Unable to verify your access. Please log in again.');
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    const microsoftButton = document.getElementById("microsoftLogin");
    
    if (microsoftButton) {
      microsoftButton.addEventListener("click", handleMicrosoftLogin);
    } else {
      console.error('Microsoft login button not found');
    }
    
    checkAuthStatus();
    handleOAuthCallback();
  });

  // Check authentication status when page becomes visible
  document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
      console.log('Page became visible, checking auth status...');
      resetLoginButton();
      checkAuthStatus();
    }
  });

  // Also check when the page is focused
  window.addEventListener('focus', function() {
    console.log('Window focused, checking auth status...');
    resetLoginButton();
    checkAuthStatus();
  });

  // Check authentication on page load
  window.addEventListener('load', function() {
    console.log('Page loaded, checking auth status...');
    resetLoginButton();
    checkAuthStatus();
  });
}

