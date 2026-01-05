/**
 * Custom Leaf Cursor
 * Creates an animated leaf cursor that follows the mouse with a gentle sway effect
 */

(function() {
  'use strict';

  // Configuration
  const CURSOR_IMAGE = '/static/uploads/images/leaf-pixel-Picsart-BackgroundRemover.png';
  const CURSOR_SIZE = 32; // pixels
  const SMOOTH_FACTOR = 0.15; // Lower = smoother but more lag (0.1 - 0.3 recommended)

  // State
  let cursor = null;
  let mouseX = 0;
  let mouseY = 0;
  let cursorX = 0;
  let cursorY = 0;
  let isVisible = false;
  let animationFrame = null;

  /**
   * Create the cursor element
   */
  function createCursor() {
    // Don't create if already exists
    if (cursor) return;

    // Create cursor container
    cursor = document.createElement('div');
    cursor.className = 'leaf-cursor';
    cursor.innerHTML = `<img src="${CURSOR_IMAGE}" alt="" draggable="false">`;
    
    document.body.appendChild(cursor);

    // Add class to body to hide default cursor
    document.body.classList.add('custom-cursor-active');

    // Start the animation loop
    animate();
  }

  /**
   * Smooth animation loop - makes cursor follow mouse smoothly
   */
  function animate() {
    // Smooth interpolation towards mouse position
    cursorX += (mouseX - cursorX) * SMOOTH_FACTOR;
    cursorY += (mouseY - cursorY) * SMOOTH_FACTOR;

    // Update cursor position (offset to center the cursor on mouse point)
    if (cursor) {
      cursor.style.left = (cursorX - CURSOR_SIZE / 2) + 'px';
      cursor.style.top = (cursorY - CURSOR_SIZE / 2) + 'px';
    }

    // Continue animation
    animationFrame = requestAnimationFrame(animate);
  }

  /**
   * Handle mouse movement
   */
  function onMouseMove(e) {
    mouseX = e.clientX;
    mouseY = e.clientY;

    // Show cursor on first move
    if (!isVisible && cursor) {
      cursor.classList.add('visible');
      isVisible = true;
    }
  }

  /**
   * Handle mouse entering the window
   */
  function onMouseEnter() {
    if (cursor) {
      cursor.classList.add('visible');
      isVisible = true;
    }
  }

  /**
   * Handle mouse leaving the window
   */
  function onMouseLeave() {
    if (cursor) {
      cursor.classList.remove('visible');
      isVisible = false;
    }
  }

  /**
   * Handle mouse down (click)
   */
  function onMouseDown() {
    if (cursor) {
      cursor.classList.add('clicking');
      setTimeout(() => {
        cursor.classList.remove('clicking');
      }, 150);
    }
  }

  /**
   * Handle hovering over interactive elements
   */
  function onMouseOver(e) {
    const target = e.target;
    const isInteractive = 
      target.tagName === 'A' ||
      target.tagName === 'BUTTON' ||
      target.closest('a') ||
      target.closest('button') ||
      target.getAttribute('role') === 'button' ||
      target.classList.contains('btn') ||
      target.classList.contains('primary') ||
      target.classList.contains('card');

    if (cursor) {
      if (isInteractive) {
        cursor.classList.add('hovering');
      } else {
        cursor.classList.remove('hovering');
      }
    }
  }

  /**
   * Initialize the custom cursor
   */
  function init() {
    // Don't initialize on touch devices
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
      console.log('Touch device detected - custom cursor disabled');
      return;
    }

    // Create cursor element
    createCursor();

    // Add event listeners
    document.addEventListener('mousemove', onMouseMove, { passive: true });
    document.addEventListener('mouseenter', onMouseEnter);
    document.addEventListener('mouseleave', onMouseLeave);
    document.addEventListener('mousedown', onMouseDown);
    document.addEventListener('mouseover', onMouseOver, { passive: true });

    console.log('🍃 Custom leaf cursor initialized');
  }

  /**
   * Destroy the custom cursor (if needed)
   */
  function destroy() {
    if (animationFrame) {
      cancelAnimationFrame(animationFrame);
    }

    if (cursor) {
      cursor.remove();
      cursor = null;
    }

    document.body.classList.remove('custom-cursor-active');
    
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseenter', onMouseEnter);
    document.removeEventListener('mouseleave', onMouseLeave);
    document.removeEventListener('mousedown', onMouseDown);
    document.removeEventListener('mouseover', onMouseOver);

    isVisible = false;
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose for manual control
  window.LeafCursor = {
    init: init,
    destroy: destroy,
    show: function() {
      if (cursor) cursor.classList.add('visible');
    },
    hide: function() {
      if (cursor) cursor.classList.remove('visible');
    }
  };

})();

