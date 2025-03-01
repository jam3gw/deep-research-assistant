document.addEventListener('DOMContentLoaded', function () {
    // Get the start button element
    const startButton = document.getElementById('start-button');

    // Add click event listener to the start button
    startButton.addEventListener('click', function () {
        alert('Welcome to Personal Assistant! This feature is coming soon.');
    });

    // Detect environment based on URL
    const hostname = window.location.hostname;
    const environmentTag = document.getElementById('environment-tag');

    if (hostname.includes('dev.jake-moses.com')) {
        environmentTag.textContent = 'Development Environment';
        environmentTag.style.color = '#e67e22';
        document.title = 'Personal Assistant (DEV)';
    } else {
        environmentTag.textContent = 'Production Environment';
        environmentTag.style.color = '#27ae60';
    }
}); 