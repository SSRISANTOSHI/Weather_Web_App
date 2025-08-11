CREATE DATABASE IF NOT EXISTS emojiweather_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE emojiweather_db;

CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
