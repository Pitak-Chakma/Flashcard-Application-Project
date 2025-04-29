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
    let cardsRemaining = parseInt(currentCardCounter.textContent.match(/\d+/)[0]) || 0;
    
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
    
    // Add event listener for the "Return to Dashboard" button in the no cards message
    document.querySelector('#noCardsMessage a.btn-outline-secondary').addEventListener('click', function(e) {
        e.preventDefault();
        window.location.href = this.getAttribute('href');
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
                    
                    // Set a timeout to redirect to dashboard after showing the completion message
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 3000); // Redirect after 3 seconds
                    
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
                
                // Re-enable all difficulty buttons
                document.querySelectorAll('.difficulty-btn').forEach(btn => {
                    btn.disabled = false;
                    btn.classList.remove('opacity-50');
                });
                
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
        // Show loading indicator or disable buttons
        document.querySelectorAll('.difficulty-btn').forEach(btn => {
            btn.disabled = true;
            btn.classList.add('opacity-50');
        });
        
        fetch(`/api/update_review/${reviewId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ difficulty: difficulty }),
            credentials: 'same-origin' // Ensure cookies are sent with the request
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Update cards remaining counter
                cardsRemaining--;
                if (cardsRemaining >= 0) {
                    currentCardCounter.textContent = `${cardsRemaining} cards remaining`;
                }
                
                // If no cards remaining, redirect to dashboard
                if (cardsRemaining <= 0) {
                    // Show a brief message before redirecting
                    studyContainer.classList.add('d-none');
                    noCardsMessage.classList.remove('d-none');
                    
                    // Redirect to dashboard after a short delay
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1500);
                } else {
                    // Load the next card
                    loadNextCard();
                }
            } else {
                console.error('API returned error:', data);
                alert(`Failed to update review: ${data.message || 'Unknown error'}`);
                
                // Re-enable buttons
                document.querySelectorAll('.difficulty-btn').forEach(btn => {
                    btn.disabled = false;
                    btn.classList.remove('opacity-50');
                });
            }
        })
        .catch(error => {
            console.error('Error updating review:', error);
            alert('Failed to update review. Please try again later. If the problem persists, try refreshing the page.');
            
            // Re-enable buttons
            document.querySelectorAll('.difficulty-btn').forEach(btn => {
                btn.disabled = false;
                btn.classList.remove('opacity-50');
            });
        });
    }
});
