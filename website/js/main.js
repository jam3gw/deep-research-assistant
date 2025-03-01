document.addEventListener('DOMContentLoaded', function () {
    // DOM elements
    const questionForm = document.getElementById('question-form');
    const researchQuestion = document.getElementById('research-question');
    const recursionDepth = document.getElementById('recursion-depth');
    const recursionDepthValue = document.getElementById('recursion-depth-value');
    const subQuestions = document.getElementById('sub-questions');
    const subQuestionsValue = document.getElementById('sub-questions-value');
    const recursionThreshold = document.getElementById('recursion-threshold');
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

    // Share functionality elements
    const shareButton = document.getElementById('share-button');
    const shareOptions = document.getElementById('share-options');
    const shareLink = document.getElementById('share-link');
    const copyLinkButton = document.getElementById('copy-link-button');
    const shareTwitter = document.getElementById('share-twitter');
    const shareFacebook = document.getElementById('share-facebook');
    const shareLinkedin = document.getElementById('share-linkedin');

    // Current research data
    let currentResearchData = null;

    // Check for shared research in URL
    checkForSharedResearch();

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

    // Share button functionality
    shareButton.addEventListener('click', function () {
        shareOptions.classList.toggle('hidden');

        if (!shareOptions.classList.contains('hidden')) {
            generateShareLink();
        }
    });

    // Copy link button
    copyLinkButton.addEventListener('click', function () {
        shareLink.select();
        document.execCommand('copy');

        showToast('Link copied to clipboard!');
    });

    // Social share buttons
    shareTwitter.addEventListener('click', function () {
        const text = `Check out my research on: "${currentResearchData.question}"`;
        const url = shareLink.value;
        window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`, '_blank');
    });

    shareFacebook.addEventListener('click', function () {
        const url = shareLink.value;
        window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, '_blank');
    });

    shareLinkedin.addEventListener('click', function () {
        const title = `Research on: ${currentResearchData.question}`;
        const url = shareLink.value;
        window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}`, '_blank');
    });

    // Form submission
    questionForm.addEventListener('submit', function (e) {
        e.preventDefault();

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
            recursion_threshold: parseInt(recursionThreshold.value)
        };

        // Invoke Lambda directly via Function URL
        invokeLambda(requestData)
            .then(data => {
                // Store current research data for sharing
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
        try {
            // Display answer
            if (data.explanation) {
                answerContent.innerHTML = data.explanation;
            } else {
                answerContent.innerHTML = '<p class="error-message">No explanation available.</p>';
            }

            // Display tree visualization
            if (data.tree_visualization) {
                treeVisualization.innerHTML = data.tree_visualization;

                // Execute scripts in the visualization
                const scripts = treeVisualization.querySelectorAll('script');
                scripts.forEach(script => {
                    const newScript = document.createElement('script');
                    newScript.textContent = script.textContent;
                    document.body.appendChild(newScript);
                });
            } else {
                treeVisualization.innerHTML = '<p class="error-message">No visualization available.</p>';
            }

            // Display JSON data
            jsonContent.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            console.error('Error displaying results:', error);
            showError('Error displaying results. Please try again.');
        }
    }

    // Function to generate a shareable link
    function generateShareLink() {
        if (!currentResearchData) return;

        // Create a compressed version of the data for sharing
        const shareData = {
            q: currentResearchData.question,
            p: currentResearchData.parameters,
            r: compressResult(currentResearchData.result)
        };

        // Convert to base64
        const base64Data = btoa(JSON.stringify(shareData));

        // Generate the URL
        const shareUrl = `${window.location.origin}${window.location.pathname}?share=${encodeURIComponent(base64Data)}`;

        // Update the share link input
        shareLink.value = shareUrl;
    }

    // Function to compress the result for sharing
    function compressResult(result) {
        // Create a simplified version of the result
        return {
            explanation: result.explanation,
            // Include only essential parts of the question tree
            question_tree: simplifyQuestionTree(result.question_tree)
        };
    }

    // Function to simplify the question tree for sharing
    function simplifyQuestionTree(tree) {
        if (!tree) return null;

        const simplified = {
            question: tree.question,
            depth: tree.depth
        };

        if (tree.answer) {
            simplified.answer = tree.answer;
        }

        if (tree.children && tree.children.length > 0) {
            simplified.children = tree.children.map(child => simplifyQuestionTree(child));
        }

        return simplified;
    }

    // Function to check for shared research in URL
    function checkForSharedResearch() {
        const urlParams = new URLSearchParams(window.location.search);
        const shareData = urlParams.get('share');

        if (shareData) {
            try {
                // Decode the share data
                const decodedData = JSON.parse(atob(decodeURIComponent(shareData)));

                // Set the form values
                researchQuestion.value = decodedData.q;

                if (decodedData.p) {
                    recursionDepth.value = decodedData.p.max_recursion_depth || 2;
                    recursionDepthValue.textContent = recursionDepth.value;

                    subQuestions.value = decodedData.p.max_sub_questions || 3;
                    subQuestionsValue.textContent = subQuestions.value;

                    recursionThreshold.value = decodedData.p.recursion_threshold || 1;
                }

                // Store the research data
                currentResearchData = {
                    question: decodedData.q,
                    parameters: decodedData.p,
                    result: decodedData.r
                };

                // Display the results
                if (decodedData.r) {
                    displayResults(decodedData.r);
                    resultsSection.classList.remove('hidden');
                }

                // Show a notification
                showToast('Viewing shared research results');
            } catch (error) {
                console.error('Error parsing shared data:', error);
                showError('The shared link is invalid or corrupted.');
            }
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
        document.title = 'Research Question Generator (DEV)';
    } else {
        environmentTag.textContent = 'Production Environment';
        environmentTag.style.color = '#27ae60';
    }
}); 