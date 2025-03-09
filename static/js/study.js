document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const studyContainer = document.getElementById('studyContainer');
    const questionContainer = document.getElementById('questionContainer');
    const answerContainer = document.getElementById('answerContainer');
    const showAnswerBtn = document.getElementById('showAnswerBtn');
    const answerButtons = document.getElementById('answerButtons');
    const currentCardCounter = document.getElementById('currentCardCounter');
    const noCardsMessage = document.getElementById('noCardsMessage');
    
    // State
    let currentCard = null;
    
    // Initial load
    loadNextCard();
    
    // Show answer button
    showAnswerBtn.addEventListener('click', function() {
        questionContainer.classList.add('d-none');
        answerContainer.classList.remove('d-none');
    });
    
    // Difficulty buttons
    document.querySelectorAll('.difficulty-btn').forEach(button => {
        button.addEventListener('click', function() {
            const difficulty = this.getAttribute('data-difficulty');
            submitReview(currentCard.review_id, difficulty);
        });
    });
    
    // Load the next card
    function loadNextCard() {
        fetch('/api/get_next_card')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'complete') {
                    // No more cards to study
                    studyContainer.classList.add('d-none');
                    noCardsMessage.classList.remove('d-none');
                    return;
                }
                
                // Save current card data
                currentCard = data;
                
                // Update the UI
                document.getElementById('cardQuestion').textContent = data.question;
                document.getElementById('cardAnswer').textContent = data.answer;
                
                // Update tags
                const tagsContainer = document.getElementById('cardTags');
                tagsContainer.innerHTML = '';
                data.tags.forEach(tag => {
                    const tagSpan = document.createElement('span');
                    tagSpan.classList.add('card-tag');
                    tagSpan.textContent = tag;
                    tagsContainer.appendChild(tagSpan);
                });
                
                // Reset the view state
                questionContainer.classList.remove('d-none');
                answerContainer.classList.add('d-none');
                
                // Make sure study container is visible
                studyContainer.classList.remove('d-none');
                noCardsMessage.classList.add('d-none');
            })
            .catch(error => {
                console.error('Error loading card:', error);
                alert('Failed to load next card. Please try again later.');
            });
    }
    
    // Submit review and load next card
    function submitReview(reviewId, difficulty) {
        fetch(`/api/update_review/${reviewId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ difficulty: difficulty }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Load the next card
                loadNextCard();
            } else {
                alert('Failed to update review. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error updating review:', error);
            alert('Failed to update review. Please try again later.');
        });
    }
});
