/**
 * Simple Tree Visualization
 * This file contains a straightforward HTML/CSS implementation for visualizing question trees.
 */

// Initialize the visualization when the DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    console.log('Simple Tree Visualizer loaded');

    // Make sure the renderTreeVisualization function is globally available
    window.renderTreeVisualization = renderTreeVisualization;
    console.log('Tree visualization function registered globally');
});

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

    rootNodeElement.innerHTML = `
        <div class="node-content">
            <div class="node-header">
                <span class="depth-indicator">Level 0</span>
                <button class="expand-btn">-</button>
            </div>
            <div class="node-question">${rootNode.question}</div>
            ${rootNode.answer ? `<button class="answer-btn" data-node-id="${rootNode.id || 'root'}">Show Answer</button>` : ''}
            <div class="node-answer" style="display: none;">${rootNode.answer || ''}</div>
        </div>
    `;

    container.appendChild(rootNodeElement);

    // Store the answer for the root node if it exists
    if (rootNode.answer) {
        rootNodeElement.setAttribute('data-answer', rootNode.answer);
    }

    // Create a container for all Level 1 nodes
    const level1Container = document.createElement('div');
    level1Container.className = 'node-children';
    level1Container.style.display = 'block'; // Always show Level 1 nodes
    rootNodeElement.appendChild(level1Container);

    // If the root has children (Level 1 nodes), render them all at the top level
    if (rootNode.children && rootNode.children.length > 0) {
        rootNode.children.forEach(level1Node => {
            // Create Level 1 node
            const level1Element = document.createElement('div');
            level1Element.className = 'tree-node depth-1';
            level1Element.setAttribute('data-node-id', level1Node.id || `level1-${Math.random().toString(36).substr(2, 9)}`);

            const hasChildren = level1Node.children && level1Node.children.length > 0;

            level1Element.innerHTML = `
                <div class="node-content">
                    <div class="node-header">
                        <span class="depth-indicator">Level 1</span>
                        <button class="expand-btn">${hasChildren ? '-' : ''}</button>
                    </div>
                    <div class="node-question">${level1Node.question}</div>
                    ${level1Node.answer ? `<button class="answer-btn" data-node-id="${level1Node.id || level1Element.getAttribute('data-node-id')}">Show Answer</button>` : ''}
                    <div class="node-answer" style="display: none;">${level1Node.answer || ''}</div>
                </div>
            `;

            level1Container.appendChild(level1Element);

            // If Level 1 node has children, render them inside its node-children div
            if (hasChildren) {
                const childrenContainer = document.createElement('div');
                childrenContainer.className = 'node-children';
                childrenContainer.style.display = 'block'; // Show Level 2 nodes by default
                level1Element.appendChild(childrenContainer);

                level1Node.children.forEach(level2Node => {
                    renderLevel2Node(level2Node, childrenContainer);
                });
            }
        });
    }

    // Add event listeners
    setupTreeInteractions(container);
}

/**
 * Renders a Level 2 node and its children
 * @param {Object} node - The Level 2 node
 * @param {HTMLElement} container - The container to render the node in
 */
function renderLevel2Node(node, container) {
    if (!node) return;

    const nodeId = node.id || `node-${Math.random().toString(36).substr(2, 9)}`;
    const hasChildren = node.children && node.children.length > 0;

    const nodeElement = document.createElement('div');
    nodeElement.className = 'tree-node depth-2';
    nodeElement.setAttribute('data-node-id', nodeId);

    nodeElement.innerHTML = `
        <div class="node-content">
            <div class="node-header">
                <span class="depth-indicator">Level 2</span>
                <button class="expand-btn" ${!hasChildren ? 'style="visibility: hidden;"' : ''}>+</button>
            </div>
            <div class="node-question">${node.question}</div>
            ${node.answer ? `<button class="answer-btn" data-node-id="${nodeId}">Show Answer</button>` : ''}
            <div class="node-answer" style="display: none;">${node.answer || ''}</div>
        </div>
    `;

    container.appendChild(nodeElement);

    // If this node has children, render them recursively
    if (hasChildren) {
        const childrenContainer = document.createElement('div');
        childrenContainer.className = 'node-children';
        childrenContainer.style.display = 'none'; // Hide deeper levels by default
        nodeElement.appendChild(childrenContainer);

        node.children.forEach(childNode => {
            renderChildNode(childNode, childrenContainer, 3); // Start at depth 3
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

    const nodeId = node.id || `node-${Math.random().toString(36).substr(2, 9)}`;
    const hasChildren = node.children && node.children.length > 0;

    const nodeElement = document.createElement('div');
    nodeElement.className = `tree-node depth-${depth}`;
    nodeElement.setAttribute('data-node-id', nodeId);

    nodeElement.innerHTML = `
        <div class="node-content">
            <div class="node-header">
                <span class="depth-indicator">Level ${depth}</span>
                ${hasChildren ? '<button class="expand-btn">+</button>' : ''}
            </div>
            <div class="node-question">${node.question}</div>
            ${node.answer ? `<button class="answer-btn" data-node-id="${nodeId}">Show Answer</button>` : ''}
            <div class="node-answer" style="display: none;">${node.answer || ''}</div>
        </div>
        ${hasChildren ? '<div class="node-children" style="display: none;"></div>' : ''}
    `;

    container.appendChild(nodeElement);

    // If this node has children, render them recursively
    if (hasChildren) {
        const childrenContainer = nodeElement.querySelector('.node-children');
        node.children.forEach(childNode => {
            renderChildNode(childNode, childrenContainer, depth + 1);
        });
    }
}

/**
 * Sets up interactions for the tree (expand/collapse, show answers)
 * @param {HTMLElement} container - The tree container
 */
function setupTreeInteractions(container) {
    // Setup expand/collapse buttons
    const expandButtons = container.querySelectorAll('.expand-btn');
    expandButtons.forEach(button => {
        // Skip empty buttons (those with no text content)
        if (!button.textContent.trim()) return;

        button.addEventListener('click', function () {
            const node = this.closest('.tree-node');
            const children = node.querySelector('.node-children');

            if (!children) return;

            if (children.style.display === 'none') {
                children.style.display = 'block';
                this.textContent = '-';
                node.classList.add('expanded');
            } else {
                children.style.display = 'none';
                this.textContent = '+';
                node.classList.remove('expanded');
            }
        });
    });

    // Setup answer buttons
    const answerButtons = container.querySelectorAll('.answer-btn');
    answerButtons.forEach(button => {
        button.addEventListener('click', function () {
            const nodeId = this.getAttribute('data-node-id');
            const node = container.querySelector(`.tree-node[data-node-id="${nodeId}"]`);
            const question = node.querySelector('.node-question').textContent;
            const answer = node.querySelector('.node-answer').innerHTML;

            // Show the answer in the modal
            const modal = document.getElementById('answer-modal');
            modal.querySelector('.modal-title').textContent = question;
            modal.querySelector('.modal-body').innerHTML = answer;
            modal.style.display = 'block';
        });
    });
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

// Export the render function for use in other files
window.renderTreeVisualization = renderTreeVisualization;
console.log('Tree visualization function exported to window object'); 