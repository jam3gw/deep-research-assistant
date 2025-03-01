document.addEventListener('DOMContentLoaded', function () {
    // API endpoint
    const API_ENDPOINT = 'https://ow5zhzdho1.execute-api.us-west-2.amazonaws.com/prod/research';

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
            alert('Please enter a research question.');
            return;
        }

        // Show loading indicator and disable submit button
        submitButton.disabled = true;
        loadingIndicator.classList.add('active');
        resultsSection.classList.add('hidden');

        // Prepare request data
        const requestData = {
            expression: researchQuestion.value.trim(),
            max_recursion_depth: parseInt(recursionDepth.value),
            max_sub_questions: parseInt(subQuestions.value),
            recursion_threshold: parseInt(recursionThreshold.value)
        };

        // Make API request
        fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
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
                alert('An error occurred while processing your request. Please try again.');
            })
            .finally(() => {
                // Always hide loading indicator and enable submit button
                submitButton.disabled = false;
                loadingIndicator.classList.remove('active');
            });
    });

    // Function to display results
    function displayResults(data) {
        // Display answer
        answerContent.innerHTML = data.explanation || 'No explanation available.';

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
            treeVisualization.innerHTML = '<p>No visualization available.</p>';
        }

        // Display JSON data
        jsonContent.textContent = JSON.stringify(data, null, 2);
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