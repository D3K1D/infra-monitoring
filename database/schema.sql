-- Data Center Infrastructure Monitoring and Alert Management System
-- MySQL schema: users, nodes, metrics, thresholds, alerts
--
-- Run once on the database server:
--   mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS monitoring
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE monitoring;

-- Application users who log into the dashboard.
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('admin', 'technician') NOT NULL DEFAULT 'technician',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Each monitored machine that reports metrics.
CREATE TABLE IF NOT EXISTS nodes (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    hostname      VARCHAR(100) NOT NULL UNIQUE,
    ip_address    VARCHAR(45),
    os            VARCHAR(100),
    location      VARCHAR(100),
    status        ENUM('online', 'warning', 'offline') NOT NULL DEFAULT 'offline',
    last_seen     DATETIME,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Historical metric readings sent by the agents.
CREATE TABLE IF NOT EXISTS metrics (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    node_id       INT NOT NULL,
    cpu_percent   FLOAT NOT NULL,
    memory_percent FLOAT NOT NULL,
    disk_percent  FLOAT NOT NULL,
    recorded_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_metrics_node FOREIGN KEY (node_id)
        REFERENCES nodes(id) ON DELETE CASCADE
);

-- Index speeds up history-by-node-over-time queries used for the charts.
CREATE INDEX idx_metrics_node_time ON metrics (node_id, recorded_at);

-- Admin-configured alert thresholds. One row per metric type.
CREATE TABLE IF NOT EXISTS thresholds (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    metric_type   ENUM('cpu', 'memory', 'disk') NOT NULL UNIQUE,
    warning_value FLOAT NOT NULL,
    critical_value FLOAT NOT NULL,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                  ON UPDATE CURRENT_TIMESTAMP
);

-- Alerts raised when a metric crosses a threshold or a node goes offline.
CREATE TABLE IF NOT EXISTS alerts (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    node_id       INT NOT NULL,
    severity      ENUM('warning', 'critical') NOT NULL,
    trigger_reason VARCHAR(255) NOT NULL,
    status        ENUM('active', 'acknowledged') NOT NULL DEFAULT 'active',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at DATETIME,
    acknowledged_by INT,
    CONSTRAINT fk_alerts_node FOREIGN KEY (node_id)
        REFERENCES nodes(id) ON DELETE CASCADE,
    CONSTRAINT fk_alerts_user FOREIGN KEY (acknowledged_by)
        REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_alerts_status ON alerts (status, created_at);

-- Default thresholds so the system has sensible values before an admin edits them.
INSERT INTO thresholds (metric_type, warning_value, critical_value)
VALUES
    ('cpu', 75, 85),
    ('memory', 80, 90),
    ('disk', 80, 90)
ON DUPLICATE KEY UPDATE metric_type = metric_type;
