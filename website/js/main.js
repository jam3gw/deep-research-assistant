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
                showError(error.message || 'An error occurred while processing your request. Please try again.');
            })
            .finally(() => {
                // Always hide loading indicator and enable submit button
                submitButton.disabled = false;
                loadingIndicator.classList.remove('active');
            });
    });

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
}); 