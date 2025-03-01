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