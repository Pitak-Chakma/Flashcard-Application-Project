# Flashcard Website

Developed by: Pitak Chakma (2220162)
## 📝 About the Project

The Flashcard Website is an interactive and user-friendly platform designed to enhance learning through digital flashcards. This website allows users to create, manage, and study flashcards efficiently, making it an ideal tool for students, educators, and lifelong learners. With features like personalized flashcards, study modes, progress tracking, and sharing options, the platform is optimized for both desktop and mobile use, enabling effective learning on the go.

## 🌟 Features
###  🧠 [1] Flashcard Creation

    Unlimited Flashcards: Users can create as many flashcards as they want.
    Tagging System: Flashcards can be tagged with subjects or topics for easy organization.
    Dual-Sided Design: Each flashcard has a front side for questions and a back side for correct answers.

###  👀 [2] Visibility/Sharing

    Customizable Visibility:
        Public: Flashcards are visible to all users under the same tag, fostering collaboration.
        Private: Flashcards are visible only to the user who created them, ensuring privacy.

### [3] 📝 Flashcard Testing (with Randomize Feature)

    Targeted Testing: Users can test themselves by selecting a specific tag folder and choosing a flashcard.
    Randomized Testing: A "Randomize Test" button allows users to test themselves with a randomly selected flashcard from a tag folder, adding variety and challenge.

### [4] 💹 Statistics/Progress Tracking

    Detailed Insights: Users can view statistics such as:
        Total flashcards attempted.
        Success percentage.
        Number of remaining flashcards to study.
    Motivational Feedback: Progress tracking helps users stay motivated and identify areas for improvement.

### [5] 🔁 Advanced Spaced Repetition

    Enhanced Retention: This feature schedules flashcard reviews at increasing intervals, optimizing long-term memory retention through scientifically proven spaced repetition techniques.
    SuperMemo SM-2 Algorithm: Uses an enhanced implementation of the SM-2 algorithm with adaptive difficulty adjustments.
    Learning Efficiency Metrics: Tracks retention rate, review streak, and average ease factor to provide insights into learning progress.
    Randomized Intervals: Adds small randomization to intervals to prevent cards from clustering on the same day.

### [6] 🎲 Gamification Elements

    Rewards System: Users earn rewards based on their activity and success rates, gamifying the learning experience and encouraging consistent engagement.


# 📧 Contact

For questions, suggestions, or feedback, feel free to reach out:

    - 🧑‍💻 Developer: Pitak Chakma
    - 📬 Email: pitakchakmacse@gmail.com
    - 📦 GitHub: Pitak-Chakma

# 🎯 Future Enhancements

    Add support for multimedia flashcards (images, audio, video).
    Implement collaborative study groups for public flashcards.
    Introduce AI-powered suggestions for flashcard content and study schedules.
    Enhance mobile responsiveness with a dedicated mobile app.
    Integrate with external learning APIs for expanded content.

# 🔧 Setup and Configuration

## Environment Variables

The application uses environment variables to securely store sensitive information. To set up:

1. Copy the `.env.example` file to a new file named `.env`
2. Fill in your values for the environment variables

```
# Example .env file
SECRET_KEY=your-secure-random-key-here
DATABASE_URL=sqlite:///flashcards.db
SPACED_REPETITION_API_KEY=your-api-key-here
MAX_CARDS_PER_SESSION=20
```

## Security

All sensitive information including API keys are stored using environment variables to ensure they are not exposed in the codebase or public repositories. This follows security best practices for protecting credentials and sensitive configuration.

### 🙏 Thank you for exploring the Flashcard Website project! We hope it helps you achieve your learning goals efficiently and enjoyably. 🎓
