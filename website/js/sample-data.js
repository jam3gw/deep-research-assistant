// Sample data for testing the tree visualization
const sampleData = {
    explanation: "<p>This is a sample answer to demonstrate the tree visualization.</p>",
    question_tree: {
        question: "What are the key differences between supervised and unsupervised learning?",
        answer: "Supervised and unsupervised learning differ primarily in their use of labeled data, learning approach, applications, and evaluation methods.",
        depth: 0,
        id: "root",
        children: [
            {
                question: "How does supervised learning work?",
                answer: "Supervised learning uses labeled training data with input-output pairs. The algorithm learns to map inputs to correct outputs by minimizing prediction errors. Examples include classification and regression tasks.",
                depth: 1,
                id: "node-1",
                children: [
                    {
                        question: "What are common supervised learning algorithms?",
                        answer: "Common supervised learning algorithms include Linear Regression, Logistic Regression, Support Vector Machines (SVM), Decision Trees, Random Forests, and Neural Networks.",
                        depth: 2,
                        id: "node-1-1"
                    },
                    {
                        question: "What are the applications of supervised learning?",
                        answer: "Supervised learning is used for image classification, spam detection, sentiment analysis, price prediction, medical diagnosis, and many other tasks where labeled data is available.",
                        depth: 2,
                        id: "node-1-2"
                    }
                ]
            },
            {
                question: "How does unsupervised learning work?",
                answer: "Unsupervised learning works with unlabeled data, identifying patterns and structures without predefined outputs. It discovers hidden patterns or intrinsic structures in input data.",
                depth: 1,
                id: "node-2",
                children: [
                    {
                        question: "What are common unsupervised learning algorithms?",
                        answer: "Common unsupervised learning algorithms include K-means clustering, Hierarchical Clustering, Principal Component Analysis (PCA), Independent Component Analysis, and Autoencoders.",
                        depth: 2,
                        id: "node-2-1"
                    },
                    {
                        question: "What are the applications of unsupervised learning?",
                        answer: "Unsupervised learning is used for customer segmentation, anomaly detection, feature learning, dimensionality reduction, recommendation systems, and exploring data structure.",
                        depth: 2,
                        id: "node-2-2"
                    }
                ]
            },
            {
                question: "What are the evaluation metrics for each type?",
                answer: "Supervised learning uses metrics like accuracy, precision, recall, F1-score, and mean squared error. Unsupervised learning uses metrics like silhouette score, Davies-Bouldin index, and reconstruction error.",
                depth: 1,
                id: "node-3"
            }
        ]
    },
    metadata: {
        total_nodes: 8,
        max_depth: 2,
        processing_time: "2.5 seconds"
    }
};

// Make the sample data available globally
window.sampleData = sampleData; 