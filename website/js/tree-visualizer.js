/**
 * Simple Tree Visualization
 * This file contains a straightforward HTML/CSS implementation for visualizing question trees.
 */

// Initialize the visualization when the DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    console.log('Simple Tree Visualizer loaded');

    // Add CSS for source frequency
    addSourceFrequencyStyles();

    // Make sure the renderTreeVisualization function is globally available
    window.renderTreeVisualization = renderTreeVisualization;
    console.log('Tree visualization function registered globally');
});

/**
 * Adds CSS styles for source frequency display
 */
function addSourceFrequencyStyles() {
    // Check if styles already exist
    if (!document.getElementById('source-frequency-styles')) {
        const style = document.createElement('style');
        style.id = 'source-frequency-styles';
        style.textContent = `
            .source-frequency {
                font-size: 0.8rem;
                color: #666;
                margin-left: 5px;
                font-style: italic;
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Renders a tree visualization using simple HTML/CSS
 * @param {Object} questionTree - The question tree data structure
 * @param {Object} metadata - Metadata about the tree (total_nodes, max_depth, processing_time)
 * @param {string} containerId - The ID of the container element to render the tree in
 */
function renderTreeVisualization(questionTree, metadata, containerId = 'tree-visualization') {
    console.log('Rendering simple tree visualization:', { questionTree, metadata, containerId });

    // Get the container element
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container element with ID "${containerId}" not found`);
        return;
    }

    // Clear the container
    container.innerHTML = '';
    console.log('Container cleared');

    // Add metadata section if available
    if (metadata) {
        const metadataDiv = document.createElement('div');
        metadataDiv.className = 'tree-metadata';
        metadataDiv.innerHTML = `
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
        `;
        container.appendChild(metadataDiv);
        console.log('Metadata added to container');
    }

    try {
        // Create a container for the tree
        const treeContainer = document.createElement('div');
        treeContainer.className = 'simple-tree-container';
        treeContainer.style.width = '100%';
        treeContainer.style.padding = '20px';
        treeContainer.style.overflowX = 'auto';
        container.appendChild(treeContainer);

        // Create the tree structure with a new approach
        renderTreeStructure(questionTree, treeContainer);

        console.log('Simple tree visualization created successfully');
    } catch (error) {
        console.error('Error creating tree:', error);
        showErrorMessage(container, 'Error creating tree visualization: ' + error.message);
    }

    // Create modal for displaying answers
    createAnswerModal();
}

/**
 * Renders the tree structure with a new approach that ensures all Level 1 nodes are visible
 * @param {Object} rootNode - The root node of the tree
 * @param {HTMLElement} container - The container to render the tree in
 */
function renderTreeStructure(rootNode, container) {
    if (!rootNode) return;

    // Create the root node
    const rootNodeElement = document.createElement('div');
    rootNodeElement.className = 'tree-node depth-0';
    rootNodeElement.setAttribute('data-node-id', rootNode.id || 'root');

    let rootNodeContent = `
        <div class="node-content">
            <div class="node-header">
                <span class="depth-indicator">Level 0</span>
                <button class="expand-btn">-</button>
            </div>
            <div class="node-question">${rootNode.question}</div>
            ${rootNode.answer ? `<button class="answer-btn" data-node-id="${rootNode.id || 'root'}">Show Answer</button>` : ''}
            <div class="node-answer" style="display: none;">${rootNode.answer || ''}</div>
    `;

    // Always add sources section, even if empty
    rootNodeContent += `
        <div class="node-sources">
            <button class="sources-btn" data-node-id="${rootNode.id || 'root'}">Sources ${rootNode.sources && rootNode.sources.length > 0 ? `(${rootNode.sources.length})` : '(0)'}</button>
            <div class="sources-list" style="display: none;">
                <h4>Sources:</h4>
    `;

    if (rootNode.sources && rootNode.sources.length > 0) {
        rootNodeContent += `
                <ul>
                    ${rootNode.sources.map((source, index) =>
            `<li><a href="${source.url}" target="_blank" rel="noopener noreferrer">${source.title}</a></li>`
        ).join('')}
                </ul>
        `;
    } else {
        rootNodeContent += `<p>No sources available for this node.</p>`;
    }

    rootNodeContent += `
            </div>
        </div>
    `;

    rootNodeContent += `</div>`;
    rootNodeElement.innerHTML = rootNodeContent;
    container.appendChild(rootNodeElement);

    // Create container for level 1 nodes
    const level1Container = document.createElement('div');
    level1Container.className = 'level-1-container';
    rootNodeElement.appendChild(level1Container);

    // Render level 1 nodes
    if (rootNode.children && rootNode.children.length > 0) {
        rootNode.children.forEach(childNode => {
            renderLevel2Node(childNode, level1Container);
        });
    }

    // Setup interactions
    setupTreeInteractions(container);
}

/**
 * Renders a Level 1 node with its children
 * @param {Object} node - The node to render
 * @param {HTMLElement} container - The container to render the node in
 */
function renderLevel2Node(node, container) {
    if (!node) return;

    // Create the level 1 node
    const nodeElement = document.createElement('div');
    nodeElement.className = 'tree-node depth-1';
    nodeElement.setAttribute('data-node-id', node.id || `node-${Math.random()}`);

    let nodeContent = `
        <div class="node-content">
            <div class="node-header">
                <span class="depth-indicator">Level 1</span>
                <button class="expand-btn">${node.children && node.children.length > 0 ? '+' : '-'}</button>
            </div>
            <div class="node-question">${node.question}</div>
            ${node.answer ? `<button class="answer-btn" data-node-id="${node.id}">Show Answer</button>` : ''}
            <div class="node-answer" style="display: none;">${node.answer || ''}</div>
    `;

    // Always add sources section, even if empty
    nodeContent += `
        <div class="node-sources">
            <button class="sources-btn" data-node-id="${node.id}">Sources ${node.sources && node.sources.length > 0 ? `(${node.sources.length})` : '(0)'}</button>
            <div class="sources-list" style="display: none;">
                <h4>Sources:</h4>
    `;

    if (node.sources && node.sources.length > 0) {
        nodeContent += `
                <ul>
                    ${node.sources.map((source, index) =>
            `<li><a href="${source.url}" target="_blank" rel="noopener noreferrer">${source.title}</a></li>`
        ).join('')}
                </ul>
        `;
    } else {
        nodeContent += `<p>No sources available for this node.</p>`;
    }

    nodeContent += `
            </div>
        </div>
    `;

    nodeContent += `</div>`;
    nodeElement.innerHTML = nodeContent;
    container.appendChild(nodeElement);

    // Create container for children
    if (node.children && node.children.length > 0) {
        const childrenContainer = document.createElement('div');
        childrenContainer.className = 'node-children';
        childrenContainer.style.display = 'none'; // Initially hidden
        nodeElement.appendChild(childrenContainer);

        // Render children
        node.children.forEach(childNode => {
            renderChildNode(childNode, childrenContainer, 2);
        });
    }
}

/**
 * Renders a child node at any depth
 * @param {Object} node - The node to render
 * @param {HTMLElement} container - The container to render the node in
 * @param {number} depth - The depth of the node
 */
function renderChildNode(node, container, depth) {
    if (!node) return;

    const nodeElement = document.createElement('div');
    nodeElement.className = `tree-node depth-${depth}`;
    nodeElement.setAttribute('data-node-id', node.id || `node-${Math.random()}`);

    // Create the node content
    let nodeContent = `
        <div class="node-content">
            <div class="node-header">
                <span class="depth-indicator">Level ${depth}</span>
                <button class="expand-btn">${node.children && node.children.length > 0 ? '+' : '-'}</button>
            </div>
            <div class="node-question">${node.question}</div>
            ${node.answer ? `<button class="answer-btn" data-node-id="${node.id}">Show Answer</button>` : ''}
            <div class="node-answer" style="display: none;">${node.answer || ''}</div>
    `;

    // Always add sources section, even if empty
    nodeContent += `
        <div class="node-sources">
            <button class="sources-btn" data-node-id="${node.id}">Sources ${node.sources && node.sources.length > 0 ? `(${node.sources.length})` : '(0)'}</button>
            <div class="sources-list" style="display: none;">
                <h4>Sources:</h4>
    `;

    if (node.sources && node.sources.length > 0) {
        nodeContent += `
                <ul>
                    ${node.sources.map((source, index) =>
            `<li>
                <a href="${source.url}" target="_blank" rel="noopener noreferrer">${source.title}</a>
                ${source.frequency > 1 ? `<span class="source-frequency">(Referenced ${source.frequency} times)</span>` : ''}
            </li>`
        ).join('')}
                </ul>
        `;
    } else {
        nodeContent += `<p>No sources available for this node.</p>`;
    }

    nodeContent += `
            </div>
        </div>
    `;

    nodeContent += `</div>`;
    nodeElement.innerHTML = nodeContent;

    container.appendChild(nodeElement);

    // Render children if any
    if (node.children && node.children.length > 0) {
        const childrenContainer = document.createElement('div');
        childrenContainer.className = 'node-children';
        childrenContainer.style.display = 'none'; // Initially hidden
        nodeElement.appendChild(childrenContainer);

        node.children.forEach(child => {
            renderChildNode(child, childrenContainer, depth + 1);
        });
    }
}

/**
 * Sets up interactions for the tree (expand/collapse, show answers)
 * @param {HTMLElement} container - The tree container
 */
function setupTreeInteractions(container) {
    // Expand/collapse functionality
    container.addEventListener('click', function (event) {
        if (event.target.classList.contains('expand-btn')) {
            const nodeElement = event.target.closest('.tree-node');
            const childrenContainer = nodeElement.querySelector('.node-children');

            if (childrenContainer) {
                const isExpanded = childrenContainer.style.display !== 'none';
                childrenContainer.style.display = isExpanded ? 'none' : 'block';
                event.target.textContent = isExpanded ? '+' : '-';
            }
        }

        // Show/hide answer functionality
        if (event.target.classList.contains('answer-btn')) {
            const nodeId = event.target.getAttribute('data-node-id');
            const nodeElement = event.target.closest('.tree-node');
            const answerElement = nodeElement.querySelector('.node-answer');

            const isVisible = answerElement.style.display !== 'none';
            answerElement.style.display = isVisible ? 'none' : 'block';
            event.target.textContent = isVisible ? 'Show Answer' : 'Hide Answer';

            // If showing the answer, remove any sources section from the answer HTML
            if (!isVisible) {
                removeSourcesSectionFromAnswer(answerElement);
            }
        }

        // Show/hide sources functionality
        if (event.target.classList.contains('sources-btn')) {
            const nodeElement = event.target.closest('.tree-node');
            const sourcesElement = nodeElement.querySelector('.sources-list');

            const isVisible = sourcesElement.style.display !== 'none';
            sourcesElement.style.display = isVisible ? 'none' : 'block';
            event.target.classList.toggle('active');
        }
    });

    // Initialize all sources buttons with accurate counts and consistent styling
    const sourcesButtons = container.querySelectorAll('.sources-btn');
    sourcesButtons.forEach(button => {
        const nodeElement = button.closest('.tree-node');
        const sourcesElement = nodeElement.querySelector('.sources-list');
        const sourcesList = sourcesElement.querySelector('ul');

        // Update button text to show number of sources
        if (sourcesList) {
            const sourceCount = sourcesList.children.length;
            button.textContent = `Sources (${sourceCount})`;
        } else {
            button.textContent = 'Sources (0)';
        }
    });
}

/**
 * Removes any sources section from the answer HTML
 * @param {HTMLElement} answerElement - The answer element
 */
function removeSourcesSectionFromAnswer(answerElement) {
    // Find any sources section in the answer HTML
    const sourcesSection = answerElement.querySelector('.sources');
    if (sourcesSection) {
        // Remove the sources section
        sourcesSection.remove();
    }
}

/**
 * Creates a modal for displaying answers
 */
function createAnswerModal() {
    // Remove any existing modal
    const existingModal = document.getElementById('answer-modal');
    if (existingModal) {
        existingModal.remove();
    }

    // Create the modal
    const modal = document.createElement('div');
    modal.id = 'answer-modal';
    modal.className = 'answer-modal';
    modal.style.display = 'none';

    modal.innerHTML = `
        <div class="modal-content">
            <span class="close-modal">&times;</span>
            <h2 class="modal-title"></h2>
            <div class="modal-body"></div>
        </div>
    `;

    document.body.appendChild(modal);

    // Setup close button
    const closeButton = modal.querySelector('.close-modal');
    closeButton.addEventListener('click', function () {
        modal.style.display = 'none';
    });

    // Close when clicking outside
    window.addEventListener('click', function (event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

/**
 * Shows an error message in the container
 * @param {HTMLElement} container - The container element
 * @param {string} message - The error message
 */
function showErrorMessage(container, message) {
    console.error('Showing error message:', message);
    container.innerHTML = `
        <div style="padding: 20px; background-color: #f8d7da; border-radius: 8px; color: #721c24; text-align: center;">
            <h3>Error</h3>
            <p>${message}</p>
        </div>
    `;
}

/**
 * Renders the tree visualization on the client side
 * @param {Object} treeData - The tree data from the API
 * @param {Object} metadata - Metadata about the tree
 */
function renderClientSideTree(treeData, metadata) {
    console.log('Rendering client-side tree with data:', treeData);

    // Get the container
    const container = document.getElementById('tree-visualization');
    if (!container) {
        console.error('Tree visualization container not found');
        return;
    }

    // Clear the container
    container.innerHTML = '';

    // Create the tree metadata section
    const metadataSection = document.createElement('div');
    metadataSection.className = 'tree-metadata';

    // Add metadata information
    if (metadata) {
        metadataSection.innerHTML = `
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
        `;
    }

    // Add metadata section to container
    container.appendChild(metadataSection);

    // Create the tree container
    const treeContainer = document.createElement('div');
    treeContainer.className = 'tree-container';
    container.appendChild(treeContainer);

    // Render the tree structure
    renderTreeStructure(treeData, treeContainer);

    // Setup interactions
    setupTreeInteractions(treeContainer);

    console.log('Tree visualization rendered');
}

// Export the render function for use in other files
window.renderTreeVisualization = renderTreeVisualization;
console.log('Tree visualization function exported to window object'); 