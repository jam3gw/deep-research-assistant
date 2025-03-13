document.addEventListener('DOMContentLoaded', function () {
    // Load LZString library for compression
    loadLZString().then(() => {
        // Check for shared research in URL after LZString is loaded
        checkForSharedResearch();
    }).catch(error => {
        console.error('Error loading LZString:', error);
        // Still try to check for shared research even if LZString fails to load
        checkForSharedResearch();
    });

    // DOM elements
    const questionForm = document.getElementById('question-form');
    const researchQuestion = document.getElementById('research-question');
    const recursionDepth = document.getElementById('recursion-depth');
    const recursionDepthValue = document.getElementById('recursion-depth-value');
    const subQuestions = document.getElementById('sub-questions');
    const subQuestionsValue = document.getElementById('sub-questions-value');
    const toggleParameters = document.getElementById('toggle-parameters');
    const parametersContainer = document.getElementById('parameters-container');
    const submitButton = document.getElementById('submit-button');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultsSection = document.getElementById('results-section');
    const answerContent = document.getElementById('answer-content');
    const treeVisualization = document.getElementById('tree-visualization');
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');

    // Share functionality elements - DISABLED
    const shareButton = document.getElementById('share-button');
    if (shareButton) {
        shareButton.style.display = 'none'; // Hide the share button
    }
    const shareOptions = document.getElementById('share-options');
    const shareLink = document.getElementById('share-link');
    const copyLinkButton = document.getElementById('copy-link-button');
    const shareTwitter = document.getElementById('share-twitter');
    const shareFacebook = document.getElementById('share-facebook');
    const shareLinkedin = document.getElementById('share-linkedin');
    const shareCompactToggle = document.getElementById('share-compact-toggle');

    // Hide the entire share container if it exists
    const shareContainer = document.querySelector('.share-container');
    if (shareContainer) {
        shareContainer.style.display = 'none';
    }

    // Current research data
    let currentResearchData = null;

    // Update range input values
    recursionDepth.addEventListener('input', function () {
        recursionDepthValue.textContent = this.value;
    });

    subQuestions.addEventListener('input', function () {
        subQuestionsValue.textContent = this.value;
    });

    // Toggle advanced parameters
    toggleParameters.addEventListener('click', function () {
        parametersContainer.classList.toggle('hidden');
        const icon = this.querySelector('i');
        if (parametersContainer.classList.contains('hidden')) {
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        } else {
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
        }
    });

    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', function () {
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            // Add active class to current button and corresponding pane
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    // Share button functionality - DISABLED
    // shareButton.addEventListener('click', function () {
    //     shareOptions.classList.toggle('hidden');
    //
    //     if (!shareOptions.classList.contains('hidden')) {
    //         generateShareLink();
    //     }
    // });

    // Copy link button - DISABLED
    // copyLinkButton.addEventListener('click', function () {
    //     shareLink.select();
    //     document.execCommand('copy');
    //
    //     showToast('Link copied to clipboard!');
    // });

    // Social share buttons - DISABLED
    // shareTwitter.addEventListener('click', function () {
    //     const text = `Check out my research on: "${currentResearchData.question}"`;
    //     const url = shareLink.value;
    //     window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`, '_blank');
    // });
    //
    // shareFacebook.addEventListener('click', function () {
    //     const url = shareLink.value;
    //     window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, '_blank');
    // });
    //
    // shareLinkedin.addEventListener('click', function () {
    //     const title = `Research on: ${currentResearchData.question}`;
    //     const url = shareLink.value;
    //     window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}`, '_blank');
    // });

    // Form submission
    questionForm.addEventListener('submit', function (e) {
        e.preventDefault(); // This prevents the form from submitting normally

        // Update URL without reloading the page
        const currentUrl = new URL(window.location.href);
        // Remove any existing 'share' parameter to avoid confusion
        currentUrl.searchParams.delete('share');
        window.history.replaceState({}, '', currentUrl.toString());

        // Validate form
        if (!researchQuestion.value.trim()) {
            showError('Please enter a research question.');
            return;
        }

        // Show loading indicator and disable submit button
        submitButton.disabled = true;
        loadingIndicator.classList.add('active');
        resultsSection.classList.add('hidden');
        clearPreviousResults();

        // Prepare request data
        const requestData = {
            expression: researchQuestion.value.trim(),
            max_recursion_depth: parseInt(recursionDepth.value),
            max_sub_questions: parseInt(subQuestions.value),
            recursion_threshold: 1 // Default to Conservative (1)
        };

        // Invoke Lambda directly via Function URL
        invokeLambda(requestData)
            .then(data => {
                // Check if data is valid
                if (!data || !data.explanation) {
                    throw new Error('The research engine returned an incomplete response. Please try again.');
                }

                // Store current research data for sharing - DISABLED
                currentResearchData = {
                    question: requestData.expression,
                    parameters: {
                        max_recursion_depth: requestData.max_recursion_depth,
                        max_sub_questions: requestData.max_sub_questions,
                        recursion_threshold: requestData.recursion_threshold
                    },
                    result: data
                };

                // Process and display results
                displayResults(data);

                // Show results section
                resultsSection.classList.remove('hidden');

                // Scroll to results
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            })
            .catch(error => {
                console.error('Error:', error);

                // Provide more specific error messages based on the error
                let errorMessage = error.message || 'An error occurred while processing your request. Please try again.';

                // Check for specific error types
                if (errorMessage.includes('timeout') || errorMessage.includes('timed out')) {
                    errorMessage = 'The request timed out. Your question might be too complex. Please try a more specific question or try again later.';
                } else if (errorMessage.includes('network') || errorMessage.includes('connection')) {
                    errorMessage = 'A network error occurred. Please check your internet connection and try again.';
                } else if (errorMessage.includes('500')) {
                    errorMessage = 'The research engine encountered an internal error. Please try again with a different question.';
                }

                showError(errorMessage);

                // Clear loading state
                hideLoadingIndicators();
            })
            .finally(() => {
                // Always hide loading indicator and enable submit button
                submitButton.disabled = false;
                loadingIndicator.classList.remove('active');
            });
    });

    /**
     * Hides all loading indicators
     */
    function hideLoadingIndicators() {
        submitButton.disabled = false;
        loadingIndicator.classList.remove('active');
    }

    // Function to display results
    function displayResults(data) {
        if (!data) {
            console.error('No data provided to displayResults');
            return;
        }

        console.log('Displaying results:', data);

        // Show the results section
        resultsSection.classList.remove('hidden');

        // Display the explanation
        if (data.explanation) {
            answerContent.innerHTML = data.explanation;
            console.log('Set answer content');

            // Add source summary if available
            if (data.sources_metadata && data.all_sources && data.all_sources.length > 0) {
                addSourceSummary(answerContent, data.sources_metadata, data.all_sources);
            }

            // Add sources section to the final answer if not already present
            if (data.all_sources && data.all_sources.length > 0) {
                addSourcesSection(answerContent, data.all_sources);
            }

            // Enhance source links in the final answer
            enhanceSourceLinks(answerContent);
        } else {
            console.warn('No explanation found in data');
            answerContent.innerHTML = '<p>No explanation available for this research.</p>';
        }

        // Display the tree visualization if available
        if (data.question_tree) {
            // Generate the visualization from the question tree
            console.log('Generating tree visualization from question_tree');
            renderClientSideTree(data.question_tree, data.metadata);
            treeVisualization.classList.remove('hidden');
        } else {
            console.warn('No question tree found in data');
            treeVisualization.classList.add('hidden');
        }

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * Adds a source summary to the final answer
     * @param {HTMLElement} container - The container with the answer HTML
     * @param {Object} sourcesMetadata - Metadata about the sources
     * @param {Array} allSources - All sources
     */
    function addSourceSummary(container, sourcesMetadata, allSources) {
        // Create summary element
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'source-summary';

        // Get top sources
        const topSources = sourcesMetadata.most_frequent_sources || [];

        // Create summary content
        summaryDiv.innerHTML = `
            <h3>Source Summary</h3>
            <p>This research is based on <strong>${sourcesMetadata.total_sources}</strong> unique sources.</p>
            ${topSources.length > 0 ? `
                <p>Most frequently referenced sources:</p>
                <ul class="top-sources">
                    ${topSources.slice(0, 3).map(source => `
                        <li>
                            <a href="${source.url}" target="_blank" rel="noopener noreferrer">${source.title}</a>
                            ${source.frequency > 1 ? ` (Referenced ${source.frequency} times)` : ''}
                        </li>
                    `).join('')}
                </ul>
            ` : ''}
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .source-summary {
                background-color: #f0f7ff;
                border-left: 3px solid #0969da;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }
            
            .source-summary h3 {
                margin-top: 0;
                color: #0969da;
                font-size: 1.1rem;
            }
            
            .top-sources {
                margin-top: 10px;
                padding-left: 20px;
            }
            
            .top-sources li {
                margin-bottom: 5px;
            }
        `;
        document.head.appendChild(style);

        // Insert after the first heading or at the beginning
        const firstHeading = container.querySelector('h1, h2');
        if (firstHeading) {
            firstHeading.after(summaryDiv);
        } else {
            container.prepend(summaryDiv);
        }
    }

    /**
     * Adds a sources section to the final answer if not already present
     * @param {HTMLElement} container - The container with the answer HTML
     * @param {Array} sources - Array of source objects with url and title properties
     */
    function addSourcesSection(container, sources) {
        // Check if sources section already exists
        if (!container.querySelector('.sources')) {
            // Create sources section
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources';

            // Create heading
            const heading = document.createElement('h2');
            heading.textContent = `Sources (${sources.length})`;
            sourcesDiv.appendChild(heading);

            // Create content wrapper
            const contentWrapper = document.createElement('div');
            contentWrapper.className = 'sources-content';

            // Add source filtering options if there are many sources
            if (sources.length > 5) {
                const filterOptions = document.createElement('div');
                filterOptions.className = 'source-filter-options';
                filterOptions.innerHTML = `
                    <div class="filter-label">Sort by:</div>
                    <button class="filter-btn active" data-sort="relevance">Relevance</button>
                    <button class="filter-btn" data-sort="frequency">Frequency</button>
                    <button class="filter-btn" data-sort="alphabetical">Alphabetical</button>
                `;

                // Add event listeners for filter buttons
                filterOptions.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.addEventListener('click', function () {
                        // Remove active class from all buttons
                        filterOptions.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                        // Add active class to clicked button
                        this.classList.add('active');

                        // Sort sources based on selected option
                        const sortBy = this.getAttribute('data-sort');
                        const sourcesList = contentWrapper.querySelector('ol');
                        const sourceItems = Array.from(sourcesList.querySelectorAll('li'));

                        sourceItems.sort((a, b) => {
                            const aData = JSON.parse(a.getAttribute('data-source') || '{}');
                            const bData = JSON.parse(b.getAttribute('data-source') || '{}');

                            if (sortBy === 'relevance') {
                                return (bData.relevance || 0) - (aData.relevance || 0);
                            } else if (sortBy === 'frequency') {
                                return (bData.frequency || 0) - (aData.frequency || 0);
                            } else {
                                return (aData.title || '').localeCompare(bData.title || '');
                            }
                        });

                        // Re-append sorted items
                        sourceItems.forEach(item => sourcesList.appendChild(item));
                    });
                });

                contentWrapper.appendChild(filterOptions);
            }

            // Create ordered list
            const ol = document.createElement('ol');

            // Add each source with metadata
            sources.forEach(source => {
                const li = document.createElement('li');

                // Store source data for sorting
                li.setAttribute('data-source', JSON.stringify({
                    url: source.url,
                    title: source.title,
                    relevance: source.relevance || 0,
                    frequency: source.frequency || 0
                }));

                // Create link
                const a = document.createElement('a');
                a.href = source.url;
                a.textContent = source.title;
                a.setAttribute('target', '_blank');
                a.setAttribute('rel', 'noopener noreferrer');
                li.appendChild(a);

                // Add metadata if available
                if (source.frequency > 1 || source.relevance) {
                    const metadata = document.createElement('span');
                    metadata.className = 'source-metadata';

                    let metadataText = [];
                    if (source.frequency > 1) {
                        metadataText.push(`Referenced ${source.frequency} times`);
                    }
                    if (source.relevance) {
                        const relevanceScore = Math.round(source.relevance * 10) / 10;
                        metadataText.push(`Relevance: ${relevanceScore}`);
                    }

                    metadata.textContent = ` (${metadataText.join(', ')})`;
                    li.appendChild(metadata);
                }

                // Add to list
                ol.appendChild(li);
            });

            contentWrapper.appendChild(ol);
            sourcesDiv.appendChild(contentWrapper);
            container.appendChild(sourcesDiv);

            // Add CSS for new elements
            addSourcesSectionStyles();
        }
    }

    /**
     * Adds CSS styles for the enhanced sources section
     */
    function addSourcesSectionStyles() {
        // Check if styles already exist
        if (!document.getElementById('sources-section-styles')) {
            const style = document.createElement('style');
            style.id = 'sources-section-styles';
            style.textContent = `
                .source-filter-options {
                    display: flex;
                    align-items: center;
                    margin-bottom: 15px;
                    padding: 10px;
                    background-color: #f5f8fa;
                    border-radius: 4px;
                }
                
                .filter-label {
                    margin-right: 10px;
                    font-size: 0.9rem;
                    color: #555;
                }
                
                .filter-btn {
                    background-color: #f0f4f8;
                    border: 1px solid #d0d7de;
                    border-radius: 4px;
                    padding: 5px 10px;
                    margin-right: 5px;
                    font-size: 0.8rem;
                    cursor: pointer;
                    color: #0969da;
                    transition: all 0.2s;
                }
                
                .filter-btn:hover {
                    background-color: #e6ebf1;
                }
                
                .filter-btn.active {
                    background-color: #0969da;
                    color: white;
                    border-color: #0969da;
                }
                
                .source-metadata {
                    font-size: 0.85rem;
                    color: #666;
                    font-style: italic;
                }
                
                .sources ol li {
                    margin-bottom: 12px;
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Enhances source links in the final answer by adding target="_blank" and rel="noopener noreferrer"
     * and implementing dropdown functionality
     * @param {HTMLElement} container - The container with the answer HTML
     */
    function enhanceSourceLinks(container) {
        // Find the sources section
        const sourcesDiv = container.querySelector('.sources');
        if (sourcesDiv) {
            console.log('Found sources section in final answer');

            // Add security attributes to all links
            const links = sourcesDiv.querySelectorAll('a');
            links.forEach(link => {
                link.setAttribute('target', '_blank');
                link.setAttribute('rel', 'noopener noreferrer');
            });

            // Implement dropdown functionality
            const sourcesHeading = sourcesDiv.querySelector('h2');
            if (sourcesHeading) {
                // Check if the sources-content wrapper already exists
                let contentWrapper = sourcesDiv.querySelector('.sources-content');

                // If the wrapper doesn't exist, create it
                if (!contentWrapper) {
                    // Create a wrapper for the content to be toggled
                    const contentElements = Array.from(sourcesDiv.children).filter(el => el.tagName !== 'H2');
                    contentWrapper = document.createElement('div');
                    contentWrapper.className = 'sources-content';

                    // Move content elements into the wrapper
                    contentElements.forEach(el => {
                        contentWrapper.appendChild(el);
                    });

                    // Add the wrapper after the heading
                    sourcesHeading.after(contentWrapper);
                }

                // Add click event to toggle
                sourcesHeading.addEventListener('click', function () {
                    sourcesDiv.classList.toggle('collapsed');
                });

                // Start with sources expanded by default
                sourcesDiv.classList.remove('collapsed');

                // Update heading to show source count
                const sourceItems = sourcesDiv.querySelectorAll('ol > li');
                if (sourceItems.length > 0) {
                    sourcesHeading.textContent = `Sources (${sourceItems.length})`;
                }
            }
        } else {
            console.warn('No sources section found in final answer');
        }
    }

    // Function to generate a shareable link - DISABLED
    function generateShareLink() {
        // Share functionality is disabled
        console.log('Share functionality is disabled');
        return;
    }

    // Function to compress the result for sharing - DISABLED
    function compressResult(result) {
        // Share functionality is disabled
        console.log('Share functionality is disabled');
        return null;
    }

    // Function to check for shared research in URL
    function checkForSharedResearch() {
        console.log('Checking for shared research...');
        const urlParams = new URLSearchParams(window.location.search);
        const shareData = urlParams.get('share');

        // Remove share parameter from URL to prevent sharing
        if (shareData) {
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.delete('share');
            window.history.replaceState({}, '', currentUrl.toString());

            console.log('Share functionality is currently disabled');
            showToast('Share functionality is currently disabled');
            return;
        }
    }

    // Function to show a toast notification
    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;

        document.body.appendChild(toast);

        // Add active class after a small delay to trigger animation
        setTimeout(() => {
            toast.classList.add('active');
        }, 10);

        // Remove toast after 3 seconds
        setTimeout(() => {
            toast.classList.remove('active');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 3000);
    }

    // Function to show error message
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.innerHTML = `
            <div class="error-icon"><i class="fas fa-exclamation-circle"></i></div>
            <div class="error-message">${message}</div>
            <button class="error-close">&times;</button>
        `;

        document.body.appendChild(errorDiv);

        // Add active class after a small delay to trigger animation
        setTimeout(() => {
            errorDiv.classList.add('active');
        }, 10);

        // Remove error after 5 seconds
        const timeout = setTimeout(() => {
            removeError(errorDiv);
        }, 5000);

        // Close button
        const closeButton = errorDiv.querySelector('.error-close');
        closeButton.addEventListener('click', () => {
            clearTimeout(timeout);
            removeError(errorDiv);
        });
    }

    // Function to remove error notification
    function removeError(errorDiv) {
        errorDiv.classList.remove('active');
        setTimeout(() => {
            errorDiv.remove();
        }, 300);
    }

    // Function to clear previous results
    function clearPreviousResults() {
        const answerContent = document.getElementById('answer-content');
        const treeVisualization = document.getElementById('tree-visualization');

        if (answerContent) {
            answerContent.innerHTML = '';
        }

        if (treeVisualization) {
            treeVisualization.innerHTML = '';
        }
    }

    // Detect environment based on URL
    const hostname = window.location.hostname;
    const environmentTag = document.getElementById('environment-tag');

    if (hostname.includes('dev.')) {
        environmentTag.textContent = 'Development Environment';
        environmentTag.style.color = '#e67e22';
        document.title = 'Deep Research Assitant (DEV)';
    } else {
        environmentTag.textContent = 'Production Environment';
        environmentTag.style.color = '#27ae60';
    }

    // Function to render the client-side tree visualization
    function renderClientSideTree(questionTree, metadata) {
        console.log('renderClientSideTree called with:', { questionTree, metadata });

        // Use our custom tree visualization
        if (typeof window.renderTreeVisualization === 'function') {
            console.log('Using custom tree visualization');
            window.renderTreeVisualization(questionTree, metadata, 'tree-visualization');
            return;
        }

        // Fallback to a simple visualization if custom visualization is not available
        console.warn('Custom tree visualization not available, falling back to simple implementation');

        // Clear previous content
        treeVisualization.innerHTML = '';

        // Add metadata section if available
        if (metadata) {
            const metadataHtml = `
                <div class="tree-metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">Total Nodes:</span>
                        <span class="metadata-value">${metadata.total_nodes || 'N/A'}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Max Depth:</span>
                        <span class="metadata-value">${metadata.max_depth || 'N/A'}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Processing Time:</span>
                        <span class="metadata-value">${metadata.processing_time || 'N/A'}</span>
                    </div>
                </div>
            `;
            treeVisualization.insertAdjacentHTML('beforeend', metadataHtml);
        }

        // Simple fallback visualization
        const fallbackHtml = `
            <div style="padding: 20px; background-color: #f8f9fa; border-radius: 8px; margin-top: 20px;">
                <h3>${questionTree.question}</h3>
                ${questionTree.answer ? `<p>${questionTree.answer}</p>` : ''}
                ${questionTree.children && questionTree.children.length > 0 ? `
                    <h4>Sub-questions:</h4>
                    <ul>
                        ${questionTree.children.map(child => `
                            <li>
                                <strong>${child.question}</strong>
                                ${child.answer ? `<p>${child.answer}</p>` : ''}
                            </li>
                        `).join('')}
                    </ul>
                ` : ''}
            </div>
        `;
        treeVisualization.insertAdjacentHTML('beforeend', fallbackHtml);
    }

    // Global function to toggle node expansion
    window.toggleNode = function (nodeId) {
        const node = document.getElementById(nodeId);
        if (!node) return;

        node.classList.toggle('expanded');

        // Update toggle icon
        const icon = node.querySelector('.toggle-icon');
        if (icon) {
            if (node.classList.contains('expanded')) {
                icon.textContent = '−';
            } else {
                icon.textContent = '+';
            }
        }
    };

    // Function to initialize the tree after it's added to the DOM
    function initializeTree() {
        try {
            // Expand the root node
            const rootNode = document.querySelector('.tree-container > .question-node');

            // If we can't find the root node directly, try a more general approach
            if (!rootNode) {
                console.warn('Root node not found with direct selector, trying alternative approach');
                const allNodes = document.querySelectorAll('.question-node');
                // Find the node with the lowest depth
                let lowestDepthNode = null;
                let lowestDepth = Infinity;

                allNodes.forEach(node => {
                    const depth = parseInt(node.getAttribute('data-depth') || '0');
                    if (depth < lowestDepth) {
                        lowestDepth = depth;
                        lowestDepthNode = node;
                    }
                });

                if (lowestDepthNode) {
                    lowestDepthNode.classList.add('expanded');
                    const icon = lowestDepthNode.querySelector('.toggle-icon');
                    if (icon) icon.textContent = '−';

                    // Also expand all level 1 nodes by default
                    const level1Nodes = document.querySelectorAll('.question-node[data-depth="1"]');
                    level1Nodes.forEach(node => {
                        node.classList.add('expanded');
                        const nodeIcon = node.querySelector('.toggle-icon');
                        if (nodeIcon) nodeIcon.textContent = '−';
                    });
                } else {
                    console.error('Could not find any question nodes to initialize');
                }
            } else {
                rootNode.classList.add('expanded');
                const icon = rootNode.querySelector('.toggle-icon');
                if (icon) icon.textContent = '−';

                // Also expand all level 1 nodes by default
                const level1Nodes = document.querySelectorAll('.question-node[data-depth="1"]');
                level1Nodes.forEach(node => {
                    node.classList.add('expanded');
                    const nodeIcon = node.querySelector('.toggle-icon');
                    if (nodeIcon) nodeIcon.textContent = '−';
                });
            }
        } catch (error) {
            console.error('Error initializing tree:', error);
        }
    }

    // Function to load LZString library
    function loadLZString() {
        return new Promise((resolve, reject) => {
            if (typeof LZString !== 'undefined') {
                console.log('LZString already loaded');
                resolve();
                return;
            }

            console.log('Loading LZString...');
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/lz-string@1.4.4/libs/lz-string.min.js';
            script.onload = () => {
                console.log('LZString loaded successfully');
                resolve();
            };
            script.onerror = (error) => {
                console.error('Failed to load LZString:', error);
                reject(error);
            };
            document.head.appendChild(script);
        });
    }

    // Create compact share toggle if it doesn't exist
    function createShareCompactToggle() {
        const toggle = document.createElement('div');
        toggle.id = 'share-compact-toggle';
        toggle.className = 'share-option-toggle';
        toggle.innerHTML = `
            <label class="toggle-switch">
                <input type="checkbox" id="compact-share-checkbox" checked>
                <span class="toggle-slider"></span>
            </label>
            <span class="toggle-label">Share question only (shorter link)</span>
        `;

        // Insert before the first share button
        if (shareOptions) {
            const firstButton = shareOptions.querySelector('button, a');
            if (firstButton) {
                shareOptions.insertBefore(toggle, firstButton);
            } else {
                shareOptions.appendChild(toggle);
            }
        }

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .share-option-toggle {
                display: flex;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid #eee;
            }
            .toggle-switch {
                position: relative;
                display: inline-block;
                width: 50px;
                height: 24px;
                margin-right: 10px;
            }
            .toggle-switch input {
                opacity: 0;
                width: 0;
                height: 0;
            }
            .toggle-slider {
                position: absolute;
                cursor: pointer;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: #ccc;
                transition: .4s;
                border-radius: 24px;
            }
            .toggle-slider:before {
                position: absolute;
                content: "";
                height: 16px;
                width: 16px;
                left: 4px;
                bottom: 4px;
                background-color: white;
                transition: .4s;
                border-radius: 50%;
            }
            input:checked + .toggle-slider {
                background-color: #2196F3;
            }
            input:checked + .toggle-slider:before {
                transform: translateX(26px);
            }
            .toggle-label {
                font-size: 14px;
            }
        `;
        document.head.appendChild(style);

        return toggle;
    }

    /**
     * Handles the response from the API
     * @param {Object} response - The response from the API
     */
    function handleResponse(response) {
        console.log('Handling response:', response);

        // Hide loading indicators
        hideLoadingIndicators();

        // Check if the response is valid
        if (!response) {
            showError('No response received from the server.');
            return;
        }

        // Display the results
        displayResults(response);
    }
}); 