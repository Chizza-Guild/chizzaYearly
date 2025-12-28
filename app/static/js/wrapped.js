// Hypixel Guild Wrapped - Interactive Navigation and Animations

let currentPage = 1;
let totalPages = 7;
let isAnimating = false;

/**
 * Initialize the wrapped interface
 * @param {number} pages - Total number of pages
 */
function initializeWrapped(pages) {
    totalPages = pages;
    currentPage = 1;

    setupNavigation();
    setupKeyboardControls();
    setupTouchControls();
    updateProgress();
    updateNavButtons();
    startCountUpAnimations();
    fadeOutNavHint();
}

/**
 * Set up navigation button event listeners
 */
function setupNavigation() {
    const prevButton = document.getElementById('nav-prev');
    const nextButton = document.getElementById('nav-next');

    if (prevButton) {
        prevButton.addEventListener('click', () => goToPage(currentPage - 1));
    }

    if (nextButton) {
        nextButton.addEventListener('click', () => goToPage(currentPage + 1));
    }
}

/**
 * Set up keyboard navigation
 */
function setupKeyboardControls() {
    document.addEventListener('keydown', (e) => {
        if (isAnimating) return;

        if (e.key === 'ArrowLeft') {
            goToPage(currentPage - 1);
        } else if (e.key === 'ArrowRight' || e.key === ' ') {
            e.preventDefault();
            goToPage(currentPage + 1);
        }
    });
}

/**
 * Set up touch/swipe controls for mobile
 */
function setupTouchControls() {
    let touchStartX = 0;
    let touchEndX = 0;

    const container = document.getElementById('wrapped-container');

    if (!container) return;

    container.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    });

    container.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });

    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;

        if (Math.abs(diff) < swipeThreshold) return;

        if (diff > 0) {
            // Swiped left - next page
            goToPage(currentPage + 1);
        } else {
            // Swiped right - previous page
            goToPage(currentPage - 1);
        }
    }
}

/**
 * Navigate to a specific page
 * @param {number} pageNum - Page number to navigate to
 */
function goToPage(pageNum) {
    if (pageNum < 1 || pageNum > totalPages || pageNum === currentPage || isAnimating) {
        return;
    }

    isAnimating = true;

    const pages = document.querySelectorAll('.story-page');
    const currentElement = pages[currentPage - 1];
    const nextElement = pages[pageNum - 1];

    // Update classes
    currentElement.classList.remove('active');
    if (pageNum > currentPage) {
        currentElement.classList.add('prev');
    }

    nextElement.classList.remove('prev');
    nextElement.classList.add('active');

    currentPage = pageNum;

    updateProgress();
    updateNavButtons();

    // Restart animations on new page
    setTimeout(() => {
        startCountUpAnimations();
        isAnimating = false;
    }, 500);
}

/**
 * Update progress bar
 */
function updateProgress() {
    const progressFill = document.getElementById('progress-fill');
    if (progressFill) {
        const progress = (currentPage / totalPages) * 100;
        progressFill.style.width = `${progress}%`;
    }
}

/**
 * Update navigation button states
 */
function updateNavButtons() {
    const prevButton = document.getElementById('nav-prev');
    const nextButton = document.getElementById('nav-next');

    if (prevButton) {
        prevButton.disabled = currentPage === 1;
    }

    if (nextButton) {
        nextButton.disabled = currentPage === totalPages;
    }
}

/**
 * Animate numbers counting up
 */
function startCountUpAnimations() {
    const elements = document.querySelectorAll('.story-page.active .count-up');

    elements.forEach(element => {
        const target = parseInt(element.dataset.target);
        const duration = 2000; // 2 seconds
        const increment = target / (duration / 16); // 60fps

        let current = 0;
        element.textContent = '0';

        const timer = setInterval(() => {
            current += increment;

            if (current >= target) {
                element.textContent = formatNumber(target);
                clearInterval(timer);
            } else {
                element.textContent = formatNumber(Math.floor(current));
            }
        }, 16);
    });
}

/**
 * Format numbers with commas
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Fade out the navigation hint after a few seconds
 */
function fadeOutNavHint() {
    const navHint = document.querySelector('.nav-hint');
    if (!navHint) return;

    // Wait 8 seconds, then add fade-out class (gives users time to read main content first)
    setTimeout(() => {
        navHint.classList.add('fade-out');

        // Remove from DOM after fade completes
        setTimeout(() => {
            navHint.style.display = 'none';
        }, 1000);
    }, 8000);
}

// Auto-initialize if we're on the wrapped page
document.addEventListener('DOMContentLoaded', () => {
    const wrappedContainer = document.getElementById('wrapped-container');
    if (wrappedContainer) {
        const pages = document.querySelectorAll('.story-page').length;
        if (pages > 0) {
            initializeWrapped(pages);
        }
    }
});
