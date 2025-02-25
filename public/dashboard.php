<?php
session_start();
if (!isset($_SESSION['user'])) {
    header("Location: login.php");
    exit();
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dashboard - Flashcard</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <h1>Welcome, <?php echo htmlspecialchars($_SESSION['user']); ?></h1>
        <a href="logout.php" class="btn">Logout</a>
    </header>
    <main>
        <section class="dashboard">
            <h2>Your Flashcards</h2>
            <p>Start creating flashcards here (feature to be added).</p>
        </section>
    </main>
</body>
</html>