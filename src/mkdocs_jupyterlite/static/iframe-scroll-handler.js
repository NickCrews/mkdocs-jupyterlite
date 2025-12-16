/**
 * iframe Scroll Handler for JupyterLite
 * 
 * This script listens for postMessage events from the parent page
 * and scrolls to the corresponding heading in the notebook.
 */
(function() {
    'use strict';
    
    // JupyterLite appends this character to rendered markdown headings
    const PILCROW_CHAR = '¶';
    
    // Expected origin for messages (same origin as this page)
    const EXPECTED_ORIGIN = window.location.origin;
    
    console.log('[mkdocs-jupyterlite] iframe scroll handler loaded');
    
    // Listen for messages from parent window
    window.addEventListener('message', function(event) {
        // Validate the message origin for security
        if (event.origin !== EXPECTED_ORIGIN) {
            console.log('[mkdocs-jupyterlite] Ignoring message from unexpected origin:', event.origin);
            return;
        }
        
        if (event.data && event.data.type === 'jupyterlite-toc-navigate') {
            const targetId = event.data.targetId;
            const headingText = event.data.headingText;
            console.log('[mkdocs-jupyterlite] Received scroll request for:', targetId, 'with text:', headingText);
            
            // Helper function to find heading by text content
            function findHeadingByText() {
                console.log('[mkdocs-jupyterlite] Looking for heading with text:', headingText);
                
                // Find all headings in the notebook
                // Try different selectors as JupyterLite may use different structures
                const selectors = [
                    'h1, h2, h3, h4, h5, h6',  // Standard headings
                    '.jp-MarkdownCell h1, .jp-MarkdownCell h2, .jp-MarkdownCell h3, .jp-MarkdownCell h4, .jp-MarkdownCell h5, .jp-MarkdownCell h6',  // JupyterLab markdown cell headings
                    '[role="heading"]'  // ARIA role headings
                ];
                
                for (const selector of selectors) {
                    const headings = document.querySelectorAll(selector);
                    console.log('[mkdocs-jupyterlite] Found', headings.length, 'headings with selector:', selector);
                    for (const heading of headings) {
                        // JupyterLite adds a pilcrow character to headings, so we need to strip it
                        const text = heading.textContent.trim();
                        const cleanText = text.endsWith(PILCROW_CHAR) ? text.slice(0, -1) : text;
                        console.log('[mkdocs-jupyterlite] Comparing:', cleanText, 'with:', headingText);
                        if (cleanText === headingText) {
                            return heading;
                        }
                    }
                }
                return null;
            }
            
            // Try to find the heading element
            let targetElement = findHeadingByText();
            
            if (targetElement) {
                console.log('[mkdocs-jupyterlite] Found target element, scrolling...');
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                // If not found immediately, wait for notebook to fully load and try again
                console.log('[mkdocs-jupyterlite] Target element not found, waiting for notebook to load...');
                
                // Use MutationObserver to watch for when the notebook content is added
                const observer = new MutationObserver(function(mutations, obs) {
                    const element = findHeadingByText();
                    if (element) {
                        console.log('[mkdocs-jupyterlite] Found target element after mutation, scrolling...');
                        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        obs.disconnect();
                    }
                });
                
                // Start observing the document for changes
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
                
                // Stop observing after 10 seconds to avoid memory leaks
                setTimeout(function() {
                    observer.disconnect();
                    console.log('[mkdocs-jupyterlite] Stopped waiting for target element');
                }, 10000);
            }
        }
    });
    
    console.log('[mkdocs-jupyterlite] Message listener attached');
})();
