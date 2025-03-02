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
    const jsonContent = document.getElementById('json-content');
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
        if (data.tree_visualization) {
            treeVisualization.innerHTML = data.tree_visualization;
            treeVisualization.classList.remove('hidden');
            console.log('Set tree visualization from data.tree_visualization');
            // Initialize the tree after adding it to the DOM
            setTimeout(initializeTree, 0);
        } else if (data.question_tree) {
            // If we only have the question tree but not the visualization,
            // generate the visualization from the tree
            console.log('Generating tree visualization from question_tree');
            const visualization = generateTreeVisualization(data.question_tree);
            treeVisualization.innerHTML = visualization;
            treeVisualization.classList.remove('hidden');
            // Initialize the tree after adding it to the DOM
            setTimeout(initializeTree, 0);
        } else {
            console.warn('No tree visualization or question tree found in data');
            treeVisualization.classList.add('hidden');
        }

        // Display JSON data if the element exists
        if (jsonContent) {
            jsonContent.textContent = JSON.stringify(data, null, 2);
            console.log('Set JSON content');
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
        answerContent.innerHTML = '';
        treeVisualization.innerHTML = '';
        jsonContent.textContent = '';
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

    // Function to generate tree visualization from a question tree
    function generateTreeVisualization(questionTree) {
        // This is a simplified version of the server-side tree visualization
        // It generates HTML for the tree structure

        // Start with the HTML template
        let html = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Research Question Tree</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    line-height: 1.6;
                }
                .tree-container {
                    margin: 20px 0;
                }
                .node {
                    margin: 10px 0;
                    border-radius: 5px;
                    overflow: hidden;
                }
                .question-node {
                    background-color: #e6f7ff;
                    border-left: 4px solid #1890ff;
                }
                .max-depth-node {
                    background-color: #fff7e6;
                    border-left: 4px solid #fa8c16;
                }
                .broad-topic-node {
                    background-color: #f9f0ff;
                    border-left: 4px solid #722ed1;
                }
                .answer-node {
                    background-color: #f6ffed;
                    border-left: 4px solid #52c41a;
                    margin-left: 20px;
                    padding: 10px;
                    display: none; /* Hidden by default */
                }
                .node-header {
                    padding: 10px;
                    cursor: pointer;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .node-title {
                    font-weight: bold;
                    flex-grow: 1;
                }
                .depth-indicator {
                    color: #888;
                    font-size: 0.8em;
                    margin-right: 10px;
                    background-color: #f0f0f0;
                    padding: 2px 6px;
                    border-radius: 10px;
                    display: inline-block;
                }
                .toggle-icon {
                    font-size: 18px;
                    width: 20px;
                    text-align: center;
                }
                .children {
                    margin-left: 30px;
                    border-left: 1px dashed #d9d9d9;
                    padding-left: 20px;
                    display: none; /* Hidden by default */
                }
                .expanded > .children, 
                .expanded > .answer-node {
                    display: block; /* Show when expanded */
                }
                .node-content {
                    padding: 0 10px 10px 10px;
                }
                .max-depth-badge {
                    display: inline-block;
                    background-color: #fa8c16;
                    color: white;
                    font-size: 0.8em;
                    padding: 2px 8px;
                    border-radius: 10px;
                    margin-left: 10px;
                }
                .broad-topic-badge {
                    display: inline-block;
                    background-color: #722ed1;
                    color: white;
                    font-size: 0.8em;
                    padding: 2px 8px;
                    border-radius: 10px;
                    margin-left: 10px;
                }
                .detail-button {
                    background-color: #1890ff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 0.8em;
                    cursor: pointer;
                    margin-right: 10px;
                    transition: background-color 0.3s;
                }
                .detail-button:hover {
                    background-color: #096dd9;
                }
                @media (max-width: 768px) {
                    .detail-view {
                        width: 80%;
                    }
                }
            </style>
        </head>
        <body>
            <h1>Research Question Tree</h1>
            <p>Click on any question to expand/collapse.</p>
            
            <div class="tree-container">
        `;

        // Add the tree structure
        html += renderNodeHtml(questionTree);

        // Add the closing tags (without the script tags)
        html += `
            </div>
        </body>
        </html>
        `;

        return html;
    }

    // Global function to toggle node expansion
    // This needs to be in the global scope to be accessible from the HTML
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

    // Global function to show node details
    // This needs to be in the global scope to be accessible from the HTML
    window.showDetails = function (nodeId, isQuestion) {
        try {
            const node = document.getElementById(nodeId);
            if (!node) {
                console.error(`Node with ID ${nodeId} not found`);
                return;
            }

            // Create or get the detail view container
            let detailView = document.getElementById('detailView');
            if (!detailView) {
                detailView = document.createElement('div');
                detailView.id = 'detailView';
                detailView.className = 'detail-view';
                detailView.innerHTML = `
                    <button class="detail-view-close" onclick="window.closeDetailView()">&times;</button>
                    <h2 class="detail-view-title" id="detailViewTitle">Question Details</h2>
                    <div class="detail-view-content" id="detailViewContent"></div>
                `;
                document.body.appendChild(detailView);

                // Add styles if not already present
                if (!document.getElementById('detail-view-styles')) {
                    const style = document.createElement('style');
                    style.id = 'detail-view-styles';
                    style.textContent = `
                        .detail-view {
                            position: fixed;
                            top: 0;
                            right: 0;
                            width: 40%;
                            height: 100%;
                            background: white;
                            border-left: 1px solid #ccc;
                            box-shadow: -2px 0 5px rgba(0,0,0,0.1);
                            padding: 20px;
                            overflow-y: auto;
                            transform: translateX(100%);
                            transition: transform 0.3s ease;
                            z-index: 1000;
                        }
                        .detail-view.active {
                            transform: translateX(0);
                        }
                        .detail-view-close {
                            position: absolute;
                            top: 10px;
                            right: 10px;
                            font-size: 24px;
                            cursor: pointer;
                            background: none;
                            border: none;
                        }
                        .detail-view-title {
                            margin-top: 0;
                            padding-right: 30px;
                        }
                        .detail-view-content {
                            margin-top: 20px;
                        }
                    `;
                    document.head.appendChild(style);
                }
            }

            const detailViewTitle = document.getElementById('detailViewTitle');
            const detailViewContent = document.getElementById('detailViewContent');

            if (!detailViewTitle || !detailViewContent) {
                console.error('Detail view elements not found');
                return;
            }

            if (isQuestion) {
                const nodeTitle = node.querySelector('.node-title');
                if (!nodeTitle) {
                    console.error('Node title element not found');
                    detailViewTitle.textContent = 'Question Details';
                    detailViewContent.innerHTML = '<p>Unable to load question details.</p>';
                } else {
                    const questionText = nodeTitle.textContent.split(':')[1]?.trim() || 'Unknown Question';
                    detailViewTitle.textContent = 'Question: ' + questionText;

                    // Check if this node has children or an answer
                    const children = node.querySelector('.children');
                    const answer = node.querySelector('.answer-node');

                    let content = '';
                    if (children && children.childElementCount > 0) {
                        content = '<h3>Sub-questions:</h3><ul>';
                        const subQuestions = children.querySelectorAll('.node-title');
                        subQuestions.forEach(sq => {
                            const subQuestionText = sq.textContent.split(':')[1]?.trim() || 'Unknown Question';
                            content += '<li>' + subQuestionText + '</li>';
                        });
                        content += '</ul>';
                    } else if (answer) {
                        content = '<h3>Answer:</h3>' + answer.innerHTML;
                    } else {
                        content = '<p>No answer or sub-questions available.</p>';
                    }

                    detailViewContent.innerHTML = content;
                }
            } else {
                // It's an answer node
                const questionNode = node.closest('.question-node');
                if (!questionNode) {
                    console.error('Parent question node not found');
                    detailViewTitle.textContent = 'Answer Details';
                    detailViewContent.innerHTML = node.innerHTML || '<p>Unable to load answer details.</p>';
                } else {
                    const nodeTitle = questionNode.querySelector('.node-title');
                    const questionText = nodeTitle ? nodeTitle.textContent.split(':')[1]?.trim() || 'Unknown Question' : 'Unknown Question';
                    detailViewTitle.textContent = 'Answer to: ' + questionText;

                    // Get the answer content
                    detailViewContent.innerHTML = node.innerHTML || '<p>No answer content available.</p>';
                }
            }

            detailView.classList.add('active');
        } catch (error) {
            console.error('Error in showDetails:', error);
            showError('An error occurred while showing details. Please try again.');
        }
    };

    // Global function to close detail view
    window.closeDetailView = function () {
        const detailView = document.getElementById('detailView');
        if (detailView) {
            detailView.classList.remove('active');
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
                } else {
                    console.error('Could not find any question nodes to initialize');
                }
            } else {
                rootNode.classList.add('expanded');
                const icon = rootNode.querySelector('.toggle-icon');
                if (icon) icon.textContent = '−';
            }
        } catch (error) {
            console.error('Error initializing tree:', error);
        }
    }

    // Helper function to render a single node
    function renderNodeHtml(node, path = "") {
        if (!node) return '';

        const depth = node.depth || 0;
        const nodeId = node.id || 'node-' + Math.random().toString(36).substr(2, 9);

        // Add special classes for max depth or broad topic nodes
        const maxDepthClass = node.max_depth_reached ? " max-depth-node" : "";
        const broadTopicClass = node.is_vague ? " broad-topic-node" : "";

        // Create the path for this node
        const questionText = node.question || '';
        const shortQuestion = questionText.length > 20 ? questionText.substring(0, 20) + '...' : questionText;
        const currentPath = path + (path ? " > " + shortQuestion : "");

        let html = `
        <div class="node question-node${maxDepthClass}${broadTopicClass}" id="${nodeId}" data-depth="${depth}">
            <div class="node-header" onclick="window.toggleNode('${nodeId}')">
                <span class="depth-indicator">Level ${depth}</span>
                <span class="node-title">Question: ${questionText}</span>
                <span class="toggle-icon">+</span>
            </div>
            <div class="node-content">
                <button class="detail-button" onclick="window.showDetails('${nodeId}', true); event.stopPropagation();">View Details</button>
                ${node.max_depth_reached ? '<span class="max-depth-badge">Max Depth</span>' : ''}
                ${node.is_vague ? '<span class="broad-topic-badge">Broad Topic</span>' : ''}
            </div>
        `;

        if (node.needs_breakdown && node.children && node.children.length > 0) {
            html += '<div class="children">';
            for (const child of node.children) {
                html += renderNodeHtml(child, currentPath);
            }
            html += '</div>';
        } else if (node.answer) {
            const answerId = `answer-${nodeId}`;
            html += `
            <div class="answer-node" id="${answerId}">
                <h3>Answer:</h3>
                <div>${node.answer}</div>
                <button class="detail-button" onclick="window.showDetails('${answerId}', false); event.stopPropagation();">View Full Answer</button>
            </div>
            `;
        }

        html += '</div>';
        return html;
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