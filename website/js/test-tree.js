// Test script to diagnose tree visualization issues
document.addEventListener('DOMContentLoaded', function () {
    console.log('Test script loaded');

    // Check if our tree visualization function is available
    console.log('renderTreeVisualization available:', typeof window.renderTreeVisualization !== 'undefined');

    // Create a button to test the tree visualization with sample data
    const testButton = document.createElement('button');
    testButton.textContent = 'Test Tree Visualization';
    testButton.style.position = 'fixed';
    testButton.style.bottom = '20px';
    testButton.style.right = '20px';
    testButton.style.zIndex = '9999';
    testButton.style.padding = '10px 15px';
    testButton.style.backgroundColor = '#3498db';
    testButton.style.color = 'white';
    testButton.style.border = 'none';
    testButton.style.borderRadius = '4px';
    testButton.style.cursor = 'pointer';

    testButton.addEventListener('click', function () {
        console.log('Test button clicked');

        // Sample data for testing
        const sampleData = {
            question_tree: {
                question: "What are the key differences between supervised and unsupervised learning?",
                answer: "Supervised and unsupervised learning differ primarily in their use of labeled data, learning approach, applications, and evaluation methods.",
                depth: 0,
                id: "root",
                children: [
                    {
                        question: "How does supervised learning work?",
                        answer: "Supervised learning uses labeled training data with input-output pairs.",
                        depth: 1,
                        id: "node-1",
                        children: []
                    },
                    {
                        question: "How does unsupervised learning work?",
                        answer: "Unsupervised learning works with unlabeled data, identifying patterns and structures without predefined outputs.",
                        depth: 1,
                        id: "node-2",
                        children: []
                    }
                ]
            },
            metadata: {
                total_nodes: 3,
                max_depth: 1,
                processing_time: "1.5 seconds"
            }
        };

        // Get the tree visualization container
        const treeVisualization = document.getElementById('tree-visualization');

        if (!treeVisualization) {
            console.error('Tree visualization container not found');

            // Create a container if it doesn't exist
            const container = document.createElement('div');
            container.id = 'tree-visualization';
            container.style.width = '100%';
            container.style.height = '600px';
            container.style.border = '1px solid #ddd';
            container.style.marginTop = '20px';
            document.body.appendChild(container);

            console.log('Created tree visualization container');

            // Try to render the tree in the new container
            if (typeof window.renderTreeVisualization === 'function') {
                console.log('Calling renderTreeVisualization with sample data on new container');
                window.renderTreeVisualization(sampleData.question_tree, sampleData.metadata, 'tree-visualization');
            }

            return;
        }

        console.log('Tree visualization container found');

        // Make sure the tree tab is active
        const treeTab = document.querySelector('[data-tab="question-tree"]');
        if (treeTab) {
            treeTab.click();
        }

        // Try to render the tree
        if (typeof window.renderTreeVisualization === 'function') {
            console.log('Calling renderTreeVisualization with sample data');
            window.renderTreeVisualization(sampleData.question_tree, sampleData.metadata);

            // Add a message to indicate success
            const successMessage = document.createElement('div');
            successMessage.style.padding = '10px';
            successMessage.style.backgroundColor = '#d4edda';
            successMessage.style.color = '#155724';
            successMessage.style.borderRadius = '4px';
            successMessage.style.marginTop = '10px';
            successMessage.style.textAlign = 'center';
            successMessage.textContent = 'Tree visualization rendered successfully. If you don\'t see it, check the console for errors.';
            treeVisualization.parentNode.insertBefore(successMessage, treeVisualization.nextSibling);

            // Scroll to the visualization
            treeVisualization.scrollIntoView({ behavior: 'smooth' });
        } else {
            console.error('renderTreeVisualization function not available');

            // Fallback to basic rendering
            console.log('Using fallback rendering');
            treeVisualization.innerHTML = '<div style="padding: 20px; background-color: #f8f9fa; border-radius: 8px;">' +
                '<h3>' + sampleData.question_tree.question + '</h3>' +
                '<p>' + sampleData.question_tree.answer + '</p>' +
                '<ul>' +
                sampleData.question_tree.children.map(child =>
                    '<li><strong>' + child.question + '</strong><br>' + child.answer + '</li>'
                ).join('') +
                '</ul>' +
                '</div>';
        }
    });

    document.body.appendChild(testButton);
}); 