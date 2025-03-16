// Flashcard related JavaScript

// Flip a flashcard
function flipCard(card) {
    card.classList.toggle('flipped');
}

// Preview card in the create/edit form
// Updated cards.js file
document.addEventListener('DOMContentLoaded', function() {
    const questionInput = document.getElementById('question');
    const answerInput = document.getElementById('answer');
    const previewQuestion = document.getElementById('previewQuestion');
    const previewAnswer = document.getElementById('previewAnswer');
    const previewCard = document.getElementById('previewCard');
    const flipPreviewButton = document.getElementById('flipPreviewButton');
    
    // Update preview when question/answer changes
    if (questionInput && previewQuestion) {
        questionInput.addEventListener('input', function() {
            previewQuestion.textContent = this.value || 'Question will appear here';
        });
    }
    
    if (answerInput && previewAnswer) {
        answerInput.addEventListener('input', function() {
            previewAnswer.textContent = this.value || 'Answer will appear here';
        });
    }
    
    // Fixed flip preview card function
    if (flipPreviewButton && previewCard) {
        flipPreviewButton.addEventListener('click', function() {
            previewCard.classList.toggle('flipped');  // Use toggle instead of flipCard function
        });
    }
    
    // Initialize preview with current values
    if (questionInput && previewQuestion) {
        previewQuestion.textContent = questionInput.value || 'Question will appear here';
    }
    
    if (answerInput && previewAnswer) {
        previewAnswer.textContent = answerInput.value || 'Answer will appear here';
    }
});

// Make flipCard function available globally
function flipCard(card) {
    card.classList.toggle('flipped');
}
