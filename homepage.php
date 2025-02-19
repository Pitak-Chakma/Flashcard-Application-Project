<?php
session_start();

if (!isset($_SESSION['user_id'])) {
    header("Location: user_login.html");
    exit;
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cardiology - Homepage</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #11998e, #38ef7d);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
        }
        .form-container {
            background: rgba(255, 255, 255, 0.8);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            max-width: 600px;
            width: 100%;
            text-align: center;
        }
        .form-container h2 {
            margin-bottom: 20px;
        }
        .form-container .btn {
            margin-top: 20px;
        }
        .company-name {
            margin-bottom: 20px;
            font-size: 1.5em;
            color: #333;
        }
    </style>
</head>
<body>

<div class="form-container">
    <div class="company-name">Cardiology</div>
    <h2>Welcome to Your Homepage</h2>
    <p>This is your personalized homepage. You can customize it as per your needs.</p>
    <a href="logout.php" class="btn btn-danger">Logout</a>
</div>

</body>
</html>
