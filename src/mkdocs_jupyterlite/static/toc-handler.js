/**
 * TOC Link Handler for JupyterLite iframes
 * 
 * This script intercepts clicks on Table of Contents links and sends a message
 * to the JupyterLite iframe to scroll to the corresponding heading.
 */
(function() {
    'use strict';
    
    // Since JupyterLite is hosted on the same domain, we can use window.location.origin
    const IFRAME_ORIGIN = window.location.origin;
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTocHandler);
    } else {
        initTocHandler();
    }
    
    function initTocHandler() {
        // Find the iframe that contains the JupyterLite notebook
        const iframe = document.querySelector('iframe[src*="jupyterlite/notebooks"]');
        if (!iframe) {
            console.log('[mkdocs-jupyterlite] No JupyterLite iframe found on this page');
            return;
        }
        
        console.log('[mkdocs-jupyterlite] TOC handler initialized');
        
        // Find all TOC links
        const tocLinks = document.querySelectorAll('#toc-collapse a[href^="#"]');
        
        tocLinks.forEach(function(link) {
            link.addEventListener('click', function(event) {
                event.preventDefault();
                
                // Get the target heading ID from the href
                const targetId = this.getAttribute('href').substring(1);
                // Get the link text which is the actual heading text
                const headingText = this.textContent.trim();
                console.log('[mkdocs-jupyterlite] TOC link clicked:', targetId, 'with text:', headingText);
                
                // Send message to iframe to scroll to the heading
                // Use the same origin since JupyterLite is hosted on the same domain
                iframe.contentWindow.postMessage({
                    type: 'jupyterlite-toc-navigate',
                    targetId: targetId,
                    headingText: headingText
                }, IFRAME_ORIGIN);
            });
        });
        
        console.log('[mkdocs-jupyterlite] Attached handlers to', tocLinks.length, 'TOC links');
    }
})();
