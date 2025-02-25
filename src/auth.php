<?php
require_once 'db.php';
session_start();

function signup($username, $password) {
    $db = getDB();
    $hashed_password = password_hash($password, PASSWORD_DEFAULT);
    try {
        $stmt = $db->prepare("INSERT INTO users (username, password) VALUES (:username, :password)");
        $stmt->execute(['username' => $username, 'password' => $hashed_password]);
        $_SESSION['user'] = $username;
        header("Location: ../public/dashboard.php");
        exit();
    } catch (PDOException $e) {
        echo "Error: " . $e->getMessage();
    }
}

function login($username, $password) {
    $db = getDB();
    $stmt = $db->prepare("SELECT * FROM users WHERE username = :username");
    $stmt->execute(['username' => $username]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if ($user && password_verify($password, $user['password'])) {
        $_SESSION['user'] = $username;
        header("Location: ../public/dashboard.php");
        exit();
    } else {
        echo "Invalid credentials";
    }
}