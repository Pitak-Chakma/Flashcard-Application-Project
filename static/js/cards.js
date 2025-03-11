// Flashcard related JavaScript

// Flip a flashcard
function flipCard(card) {
    card.classList.toggle('flipped');
}

// Preview card in the create/edit form
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


// Tag input functionality
document.addEventListener('DOMContentLoaded', function() {
    const tagInput = document.getElementById('tags');
    
    if (!tagInput) return;
    
    // Convert comma-separated string to array of tags
    function parseTags(input) {
        if (!input) return [];
        return input.split(',')
            .map(tag => tag.trim())
            .filter(tag => tag.length > 0);
    }
    
    // Join array of tags into comma-separated string
    function joinTags(tags) {
        return tags.join(', ');
    }
    
    // Event listener for tag input - convert multiple commas to single comma
    tagInput.addEventListener('input', function() {
        const value = this.value;
        if (value.includes(',,')) {
            this.value = value.replace(/,{2,}/g, ',');
        }
    });
    
    // Event listener for tag input - clean up on blur
    tagInput.addEventListener('blur', function() {
        const tags = parseTags(this.value);
        this.value = joinTags(tags);
    });
});

// Delete card confirmation
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('[data-action="delete-card"]');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this card? This action cannot be undone.')) {
                event.preventDefault();
            }
        });
    });
});
