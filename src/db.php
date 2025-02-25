<?php
function getDB() {
    $dsn = 'mysql:host=mysql.oregon.render.com;dbname=flashcard_db'; // Replace with your Render MySQL host/dbname
    $username = 'root'; // Replace with your Render MySQL username
    $password = 'somepassword'; // Replace with your Render MySQL password

    try {
        $db = new PDO($dsn, $username, $password);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        return $db;
    } catch (PDOException $e) {
        die("Connection failed: " . $e->getMessage());
    }
}

// Create users table if it doesn’t exist
$db = getDB();
$db->exec("CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
)");