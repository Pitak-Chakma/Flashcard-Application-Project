// Flash message handling
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
    
    // Close button for flash messages
    const closeButtons = document.querySelectorAll('.flash .close-btn');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const message = button.parentElement;
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                message.remove();
            }, 300);
        });
    });
});
