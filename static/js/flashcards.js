// Flashcard functionality
document.addEventListener('DOMContentLoaded', function() {
    // Flashcard flipping functionality
    const flipButtons = document.querySelectorAll('.flip-btn');
    
    flipButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const flashcard = this.closest('.flashcard');
            const front = flashcard.querySelector('.flashcard-front');
            const back = flashcard.querySelector('.flashcard-back');
            
            if (front.classList.contains('active')) {
                front.classList.remove('active');
                back.classList.add('active');
                this.textContent = 'Show Question';
            } else {
                back.classList.remove('active');
                front.classList.add('active');
                this.textContent = 'Show Answer';
            }
        });
    });
    
    // Option selection in test mode
    const optionLabels = document.querySelectorAll('.option-label');
    
    optionLabels.forEach(label => {
        label.addEventListener('click', function() {
            // Remove active class from all options
            document.querySelectorAll('.option').forEach(opt => {
                opt.classList.remove('active');
            });
            
            // Add active class to the selected option
            this.closest('.option').classList.add('active');
        });
    });
    
    // Flashcard creation - dynamic options management
    const addOptionBtn = document.getElementById('add-option');
    
    if (addOptionBtn) {
        const optionsContainer = document.getElementById('options-container');
        
        addOptionBtn.addEventListener('click', function() {
            const optionCount = optionsContainer.querySelectorAll('.option-row').length;
            
            const newRow = document.createElement('div');
            newRow.className = 'option-row';
            newRow.innerHTML = `
                <input type="text" name="options[]" required placeholder="Option ${optionCount + 1}">
                <button type="button" class="btn btn-sm btn-outline option-delete">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            
            optionsContainer.appendChild(newRow);
            
            // Enable delete buttons if we have more than 2 options
            if (optionCount >= 2) {
                const deleteButtons = document.querySelectorAll('.option-delete');
                deleteButtons.forEach(btn => btn.removeAttribute('disabled'));
            }
        });
        
        // Delete option functionality with event delegation
        optionsContainer.addEventListener('click', function(e) {
            if (e.target.closest('.option-delete')) {
                const optionRows = optionsContainer.querySelectorAll('.option-row');
                
                // Don't allow fewer than 2 options
                if (optionRows.length <= 2) {
                    return;
                }
                
                const row = e.target.closest('.option-row');
                row.remove();
                
                // Disable delete buttons if we have only 2 options left
                if (optionRows.length <= 3) {
                    const deleteButtons = document.querySelectorAll('.option-delete');
                    deleteButtons.forEach(btn => btn.setAttribute('disabled', 'true'));
                }
                
                // Renumber the placeholders
                const inputs = optionsContainer.querySelectorAll('input');
                inputs.forEach((input, index) => {
                    input.placeholder = `Option ${index + 1}`;
                });
            }
        });
    }
    
    // Flashcard Preview functionality
    const previewBtn = document.getElementById('preview-btn');
    
    if (previewBtn) {
        const flashcardPreview = document.getElementById('flashcard-preview');
        const previewQuestion = document.getElementById('preview-question');
        const previewOptions = document.getElementById('preview-options');
        const previewAnswer = document.getElementById('preview-answer');
        const closePreviewBtn = document.getElementById('close-preview');
        
        previewBtn.addEventListener('click', function() {
            const question = document.getElementById('question').value;
            const options = Array.from(document.querySelectorAll('input[name="options[]"]'))
                .map(input => input.value);
            const correctAnswer = document.getElementById('correct_answer').value;
            
            if (!question || options.some(opt => !opt) || !correctAnswer) {
                alert('Please fill in all fields to preview the flashcard');
                return;
            }
            
            previewQuestion.textContent = question;
            
            // Clear existing options first
            previewOptions.innerHTML = '';
            
            // Add each option to the preview
            options.forEach(option => {
                const optionEl = document.createElement('div');
                optionEl.className = 'option';
                optionEl.innerHTML = `
                    <label class="option-label">
                        <input type="radio" name="preview_answer" value="${option}">
                        <span class="option-text">${option}</span>
                    </label>
                `;
                previewOptions.appendChild(optionEl);
            });
            
            previewAnswer.textContent = correctAnswer;
            flashcardPreview.style.display = 'block';
        });
        
        if (closePreviewBtn) {
            closePreviewBtn.addEventListener('click', function() {
                flashcardPreview.style.display = 'none';
            });
        }
    }
});
