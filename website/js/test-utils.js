/**
 * Test utilities for tree visualization
 * This file contains sample data and helper functions for testing the tree visualization
 */

// Initialize test data
window.testData = {
    // Simple tree with basic structure
    simple: {
        tree: {
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
                    children: [
                        {
                            question: "What are common supervised learning algorithms?",
                            answer: "Common supervised learning algorithms include Linear Regression, Logistic Regression, Support Vector Machines (SVM), Decision Trees, Random Forests, and Neural Networks.",
                            depth: 2,
                            id: "node-1-1",
                            children: []
                        }
                    ]
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
            total_nodes: 4,
            max_depth: 2,
            processing_time: "1.5 seconds"
        }
    },

    // Complex tree with more nodes and deeper structure
    complex: {
        tree: {
            question: "What are the economic and environmental impacts of renewable energy adoption?",
            answer: "Renewable energy adoption has significant economic and environmental impacts, including job creation, reduced emissions, and energy independence.",
            depth: 0,
            id: "complex-root",
            children: [
                {
                    question: "What are the economic impacts of renewable energy?",
                    answer: "Economic impacts include job creation, reduced energy costs over time, energy independence, and new market opportunities.",
                    depth: 1,
                    id: "complex-node-1",
                    children: [
                        {
                            question: "How does renewable energy affect job markets?",
                            answer: "Renewable energy creates jobs in manufacturing, installation, maintenance, and research & development. The sector employs millions globally, with solar and wind being the largest employers.",
                            depth: 2,
                            id: "complex-node-1-1",
                            children: []
                        },
                        {
                            question: "What is the cost trajectory of renewable energy?",
                            answer: "Renewable energy costs have declined dramatically over the past decade. Solar PV costs fell by 85% and wind by 55% between 2010-2020, making them competitive with or cheaper than fossil fuels in many markets.",
                            depth: 2,
                            id: "complex-node-1-2",
                            children: []
                        }
                    ]
                },
                {
                    question: "What are the environmental impacts of renewable energy?",
                    answer: "Environmental impacts include reduced greenhouse gas emissions, improved air quality, reduced water usage, and conservation of natural resources.",
                    depth: 1,
                    id: "complex-node-2",
                    children: [
                        {
                            question: "How do renewables reduce greenhouse gas emissions?",
                            answer: "Renewables generate electricity without burning fossil fuels, directly reducing CO2 and methane emissions. A typical solar panel prevents 3-4 tons of CO2 emissions annually compared to coal power.",
                            depth: 2,
                            id: "complex-node-2-1",
                            children: []
                        },
                        {
                            question: "What are the land use implications of renewable energy?",
                            answer: "Renewable energy can require significant land area, particularly for utility-scale solar and wind farms. However, innovations like floating solar, agrivoltaics, and offshore wind help minimize land use conflicts.",
                            depth: 2,
                            id: "complex-node-2-2",
                            children: [
                                {
                                    question: "What is agrivoltaics?",
                                    answer: "Agrivoltaics is the practice of co-locating solar panels with agricultural production, allowing land to be used for both energy generation and farming. This approach can increase land productivity and provide shade for certain crops in hot climates.",
                                    depth: 3,
                                    id: "complex-node-2-2-1",
                                    children: []
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        metadata: {
            total_nodes: 8,
            max_depth: 3,
            processing_time: "2.3 seconds"
        }
    },

    // Tree with long HTML-formatted answers
    longAnswer: {
        tree: {
            question: "What are the economic and environmental impacts of renewable energy adoption globally?",
            answer: "<h1>Economic and Environmental Impacts of Renewable Energy</h1><p>Renewable energy adoption has significant economic and environmental impacts globally. From an economic perspective, it creates jobs, reduces energy costs in the long term, and decreases dependence on imported fossil fuels. Environmentally, it reduces greenhouse gas emissions, improves air quality, and helps mitigate climate change.</p>",
            depth: 0,
            id: "long-root",
            children: [
                {
                    question: "What are the economic impacts of renewable energy adoption?",
                    answer: "<h2>Economic Impacts of Renewable Energy</h2><p>The economic impacts of renewable energy adoption include:</p><ul><li>Job creation in manufacturing, installation, and maintenance</li><li>Reduced energy costs over time as technology improves</li><li>Energy independence and reduced fossil fuel imports</li><li>New market opportunities and innovation</li><li>Increased energy access in remote areas</li><li>Stable energy prices less subject to global market fluctuations</li><li>Reduced healthcare costs due to decreased pollution</li></ul><p>According to the International Renewable Energy Agency (IRENA), the renewable energy sector employed over 11 million people globally in 2018, and this number continues to grow as more countries invest in clean energy infrastructure.</p>",
                    depth: 1,
                    id: "long-node-1",
                    children: []
                },
                {
                    question: "What are the environmental impacts of renewable energy adoption?",
                    answer: "<h2>Environmental Impacts of Renewable Energy</h2><p>The environmental benefits of renewable energy adoption are substantial:</p><ul><li>Reduction in greenhouse gas emissions</li><li>Improved air quality and public health</li><li>Reduced water usage compared to conventional power generation</li><li>Conservation of natural resources</li><li>Decreased land degradation from fossil fuel extraction</li><li>Protection of ecosystems and biodiversity</li><li>Mitigation of climate change impacts</li></ul><p>Studies show that a transition to 100% renewable energy could reduce carbon dioxide emissions from the power sector by approximately 3 gigatons annually, which is essential for meeting global climate targets established in the Paris Agreement.</p><p>However, it's important to note that renewable energy technologies do have some environmental impacts, such as land use requirements for solar and wind farms, habitat disruption, and the environmental costs of manufacturing components. These impacts are generally considered significantly less harmful than those associated with fossil fuels.</p>",
                    depth: 1,
                    id: "long-node-2",
                    children: []
                }
            ]
        },
        metadata: {
            total_nodes: 3,
            max_depth: 1,
            processing_time: "2.3 seconds"
        }
    }
};

// Add a test button to the page if we're not on the test page
document.addEventListener('DOMContentLoaded', function () {
    // Check if we're on the test page
    if (document.querySelector('.test-buttons')) {
        console.log('On test page, not adding test button');
        return;
    }

    // Create a floating test button
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
                window.renderTreeVisualization(window.testData.simple.tree, window.testData.simple.metadata, 'tree-visualization');
            }

            return;
        }

        console.log('Tree visualization container found');

        // Make sure the tree tab is active
        const treeTab = document.querySelector('[data-tab="visualization"]');
        if (treeTab) {
            treeTab.click();
        }

        // Try to render the tree
        if (typeof window.renderTreeVisualization === 'function') {
            console.log('Calling renderTreeVisualization with sample data');
            window.renderTreeVisualization(window.testData.simple.tree, window.testData.simple.metadata);

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
                '<h3>' + window.testData.simple.tree.question + '</h3>' +
                '<p>' + window.testData.simple.tree.answer + '</p>' +
                '<ul>' +
                window.testData.simple.tree.children.map(child =>
                    '<li><strong>' + child.question + '</strong><br>' + child.answer + '</li>'
                ).join('') +
                '</ul>' +
                '</div>';
        }
    });

    document.body.appendChild(testButton);
}); 