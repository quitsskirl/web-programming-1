/**
 * Feedback Popup System
 * Shows a feedback popup after successful actions (like booking an appointment).
 * Also shows after a timer (5 minutes) after login for testing.
 * Once feedback is given, the popup never shows again.
 */

(function() {
  'use strict';

  // Configuration
  const DISMISS_COOLDOWN_MS = 60000; // 1 minute cooldown after dismissing
  const LOGIN_TIMER_MS = 5 * 60 * 1000; // 5 minutes after login (for testing)

  // State
  let popupCreated = false;
  let selectedRating = 0;
  let timerCheckInterval = null;
  
  // Helper to get user-specific storage keys
  function getUsername() {
    return localStorage.getItem('username') || 'guest';
  }
  
  function getDismissKey() {
    return 'feedback_dismiss_time_' + getUsername();
  }
  
  function getLoginTimerKey() {
    return 'feedback_login_time_' + getUsername();
  }
  
  function getFeedbackGivenKey() {
    return 'has_given_feedback_' + getUsername();
  }

  /**
   * Create the feedback popup HTML and inject into the page
   */
  function createPopupHTML() {
    if (popupCreated) return;
    
    const popupHTML = `
      <!-- Feedback Overlay -->
      <div class="feedback-overlay" id="feedbackOverlay"></div>
      
      <!-- Feedback Popup -->
      <div class="feedback-popup" id="feedbackPopup">
        <div class="feedback-header">
          <h3><i class="bi bi-chat-heart"></i> We'd Love Your Feedback!</h3>
          <p>Help us improve your experience</p>
          <button class="feedback-close" id="feedbackClose" title="Close">&times;</button>
        </div>
        
        <div class="feedback-body">
          <!-- Form Content -->
          <div class="feedback-form" id="feedbackForm">
            <!-- Star Rating -->
            <div class="feedback-rating">
              <label>How would you rate your experience so far?</label>
              <div class="star-rating">
                <input type="radio" name="rating" value="5" id="star5">
                <label for="star5" title="Excellent">★</label>
                <input type="radio" name="rating" value="4" id="star4">
                <label for="star4" title="Good">★</label>
                <input type="radio" name="rating" value="3" id="star3">
                <label for="star3" title="Average">★</label>
                <input type="radio" name="rating" value="2" id="star2">
                <label for="star2" title="Poor">★</label>
                <input type="radio" name="rating" value="1" id="star1">
                <label for="star1" title="Very Poor">★</label>
              </div>
            </div>
            
            <!-- Comment -->
            <div class="feedback-comment">
              <label for="feedbackComment">Any additional comments? (Optional)</label>
              <textarea id="feedbackComment" placeholder="Tell us what you think..."></textarea>
            </div>
            
            <!-- Action Buttons -->
            <div class="feedback-actions">
              <button class="feedback-btn feedback-btn-secondary" id="feedbackSkip">
                Maybe Later
              </button>
              <button class="feedback-btn feedback-btn-primary" id="feedbackSubmit" disabled>
                <i class="bi bi-send"></i> Submit
              </button>
            </div>
          </div>
          
          <!-- Success State -->
          <div class="feedback-success" id="feedbackSuccess">
            <div class="feedback-success-icon">
              <i class="bi bi-check-lg"></i>
            </div>
            <h4>Thank You!</h4>
            <p>Your feedback helps us improve.</p>
          </div>
        </div>
      </div>
    `;
    
    // Inject into page
    const container = document.createElement('div');
    container.id = 'feedbackContainer';
    container.innerHTML = popupHTML;
    document.body.appendChild(container);
    
    popupCreated = true;
    
    // Attach event listeners
    attachEventListeners();
  }

  /**
   * Attach event listeners to popup elements
   */
  function attachEventListeners() {
    const overlay = document.getElementById('feedbackOverlay');
    const popup = document.getElementById('feedbackPopup');
    const closeBtn = document.getElementById('feedbackClose');
    const skipBtn = document.getElementById('feedbackSkip');
    const submitBtn = document.getElementById('feedbackSubmit');
    const ratingInputs = document.querySelectorAll('.star-rating input');
    
    // Close/dismiss handlers
    closeBtn.addEventListener('click', dismissPopup);
    skipBtn.addEventListener('click', dismissPopup);
    overlay.addEventListener('click', dismissPopup);
    
    // Prevent popup click from closing
    popup.addEventListener('click', (e) => e.stopPropagation());
    
    // Rating selection
    ratingInputs.forEach(input => {
      input.addEventListener('change', (e) => {
        selectedRating = parseInt(e.target.value);
        submitBtn.disabled = false;
      });
    });
    
    // Submit feedback
    submitBtn.addEventListener('click', submitFeedback);
    
    // ESC key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && popup.classList.contains('active')) {
        dismissPopup();
      }
    });
  }

  /**
   * Show the feedback popup
   * Only shows if user hasn't already given feedback
   */
  async function showPopup() {
    // Check if user has already given feedback (local check first)
    if (localStorage.getItem(getFeedbackGivenKey()) === 'true') {
      console.log('Feedback already given, not showing popup');
      return;
    }
    
    // Check dismiss cooldown
    const dismissTime = localStorage.getItem(getDismissKey());
    if (dismissTime && Date.now() - parseInt(dismissTime) < DISMISS_COOLDOWN_MS) {
      console.log('Feedback popup in cooldown');
      return;
    }
    
    // Verify with server that feedback hasn't been given
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await fetch('/api/feedback/status', {
          method: 'GET',
          headers: { 'Authorization': 'Bearer ' + token }
        });
        if (response.ok) {
          const data = await response.json();
          if (data.has_given_feedback) {
            localStorage.setItem(getFeedbackGivenKey(), 'true');
            console.log('Feedback already given (server check), not showing popup');
            return;
          }
        }
      } catch (error) {
        console.log('Could not verify feedback status with server');
      }
    }
    
    createPopupHTML();
    
    const overlay = document.getElementById('feedbackOverlay');
    const popup = document.getElementById('feedbackPopup');
    
    overlay.classList.add('active');
    popup.classList.add('active');
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
  }

  /**
   * Hide the feedback popup
   */
  function hidePopup() {
    const overlay = document.getElementById('feedbackOverlay');
    const popup = document.getElementById('feedbackPopup');
    
    if (overlay) overlay.classList.remove('active');
    if (popup) popup.classList.remove('active');
    
    // Restore body scroll
    document.body.style.overflow = '';
  }

  /**
   * Dismiss popup temporarily (will show again later)
   */
  async function dismissPopup() {
    hidePopup();
    
    // Set cooldown timestamp (user-specific)
    localStorage.setItem(getDismissKey(), Date.now().toString());
    
    // Call dismiss API
    const token = localStorage.getItem('token');
    if (token) {
      try {
        await fetch('/api/feedback/dismiss', {
          method: 'POST',
          headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
          }
        });
      } catch (error) {
        console.log('Dismiss feedback error:', error);
      }
    }
  }

  /**
   * Submit the feedback
   */
  async function submitFeedback() {
    if (selectedRating === 0) return;
    
    const token = localStorage.getItem('token');
    if (!token) return;
    
    const comment = document.getElementById('feedbackComment').value.trim();
    const submitBtn = document.getElementById('feedbackSubmit');
    
    // Disable button and show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Sending...';
    
    try {
      const response = await fetch('/api/feedback/submit', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + token,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          rating: selectedRating,
          comment: comment
        })
      });
      
      if (response.ok) {
        // Show success state
        document.getElementById('feedbackForm').classList.add('hidden');
        document.getElementById('feedbackSuccess').classList.add('active');
        
        // Mark as given in localStorage for immediate effect (user-specific)
        localStorage.setItem(getFeedbackGivenKey(), 'true');
        
        // Clear the login timer since feedback was given
        localStorage.removeItem(getLoginTimerKey());
        
        // Close popup after 2 seconds
        setTimeout(() => {
          hidePopup();
        }, 2000);
      } else {
        const data = await response.json();
        alert('Error: ' + (data.message || 'Failed to submit feedback'));
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-send"></i> Submit';
      }
    } catch (error) {
      console.error('Submit feedback error:', error);
      alert('Network error. Please try again.');
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="bi bi-send"></i> Submit';
    }
  }

  /**
   * Track user activity (page visit)
   */
  async function trackActivity() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
      await fetch('/api/feedback/track-activity', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + token,
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.log('Track activity error:', error);
    }
  }

  /**
   * Check if feedback popup should be shown
   */
  async function checkFeedbackStatus() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    // Check local flag first (immediate response)
    if (localStorage.getItem('has_given_feedback') === 'true') {
      return;
    }
    
    // Check dismiss cooldown
    const dismissTime = localStorage.getItem(DISMISS_COOLDOWN_KEY);
    if (dismissTime && Date.now() - parseInt(dismissTime) < DISMISS_COOLDOWN_MS) {
      return;
    }
    
    try {
      const response = await fetch('/api/feedback/status', {
        method: 'GET',
        headers: {
          'Authorization': 'Bearer ' + token
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Update local flag
        if (data.has_given_feedback) {
          localStorage.setItem('has_given_feedback', 'true');
          return;
        }
        
        // Show popup if conditions are met
        if (data.should_show_feedback) {
          // Small delay for better UX (let page load first)
          setTimeout(() => {
            showPopup();
          }, 1500);
        }
      }
    } catch (error) {
      console.log('Check feedback status error:', error);
    }
  }

  /**
   * Start the login timer for feedback popup
   * Records login time if not already set, and checks periodically
   */
  function startLoginTimer() {
    // Don't start if feedback already given
    if (localStorage.getItem(getFeedbackGivenKey()) === 'true') {
      console.log('Feedback already given, timer not needed');
      return;
    }
    
    // Check if login time is already recorded (user-specific)
    let loginTime = localStorage.getItem(getLoginTimerKey());
    
    if (!loginTime) {
      // Record current time as login time
      loginTime = Date.now().toString();
      localStorage.setItem(getLoginTimerKey(), loginTime);
      console.log('Feedback timer started for ' + getUsername() + ' - will show in 5 minutes');
    }
    
    // Check every 30 seconds if timer has elapsed
    timerCheckInterval = setInterval(function() {
      checkLoginTimer();
    }, 30000); // Check every 30 seconds
    
    // Also check immediately
    checkLoginTimer();
  }
  
  /**
   * Check if the login timer has elapsed and show popup if needed
   */
  function checkLoginTimer() {
    // Don't show if feedback already given (user-specific)
    if (localStorage.getItem(getFeedbackGivenKey()) === 'true') {
      if (timerCheckInterval) {
        clearInterval(timerCheckInterval);
        timerCheckInterval = null;
      }
      return;
    }
    
    const loginTime = localStorage.getItem(getLoginTimerKey());
    if (!loginTime) return;
    
    const elapsed = Date.now() - parseInt(loginTime);
    
    if (elapsed >= LOGIN_TIMER_MS) {
      console.log('5 minute timer elapsed - showing feedback popup for ' + getUsername());
      // Clear the timer so it doesn't show again
      if (timerCheckInterval) {
        clearInterval(timerCheckInterval);
        timerCheckInterval = null;
      }
      // Show the popup
      showPopup();
    } else {
      const remaining = Math.round((LOGIN_TIMER_MS - elapsed) / 1000);
      console.log(`Feedback timer for ${getUsername()}: ${remaining} seconds remaining`);
    }
  }

  /**
   * Initialize the feedback system
   * Sets up login timer and prepares popup
   */
  function init() {
    // Only run if user is logged in
    const token = localStorage.getItem('token');
    if (!token) {
      return;
    }
    
    // Pre-create the popup HTML so it's ready when needed
    createPopupHTML();
    
    // Start the login timer (5 minutes after login)
    startLoginTimer();
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // DOM already loaded
    setTimeout(init, 100);
  }

  // Expose for manual triggering
  window.FeedbackPopup = {
    show: showPopup,
    hide: hidePopup,
    checkStatus: checkFeedbackStatus,
    resetTimer: function() {
      localStorage.removeItem(getLoginTimerKey());
      localStorage.removeItem(getFeedbackGivenKey());
      console.log('Feedback timer and status reset for ' + getUsername());
    }
  };

})();

