-- Создаем базу данных
DROP DATABASE IF EXISTS mydb;
CREATE DATABASE mydb;

\c mydb;

-- Создаем таблицу для хранения электронной почты
CREATE TABLE mail (
    ID SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);

-- Создаем таблицу для хранения номеров телефонов
CREATE TABLE number (
    ID SERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL
);

-- Создаем пользователя для репликации
CREATE USER replicator WITH REPLICATION PASSWORD 'Qq12345';
SELECT pg_create_physical_replication_slot('replication_slot');

-- Настройки логирования
ALTER SYSTEM SET log_directory TO '/var/log/postgres/';
ALTER SYSTEM SET log_filename TO 'postgres.log';
ALTER SYSTEM SET logging_collector TO 'on';
ALTER SYSTEM SET log_replication_commands TO 'on';
