-- phpMyAdmin SQL Dump
-- version 5.1.1deb5ubuntu1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Jul 02, 2025 at 10:24 AM
-- Server version: 8.0.42-0ubuntu0.22.04.1
-- PHP Version: 8.1.2-1ubuntu2.21

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+07:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `automotive`
--

-- --------------------------------------------------------

--
-- Table structure for table `qc_3rd`
--

CREATE TABLE `qc_3rd` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `qc_fb`
--

CREATE TABLE `qc_fb` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `qc_fc`
--

CREATE TABLE `qc_fc` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `qc_ng`
--

CREATE TABLE `qc_ng` (
  `id` int NOT NULL,
  `part` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `detail` varchar(255) NOT NULL,
  `lot` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `process` varchar(10) NOT NULL,
  `qty` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `qc_rb`
--

CREATE TABLE `qc_rb` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `qc_rc`
--

CREATE TABLE `qc_rc` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_3rd`
--

CREATE TABLE `sewing_3rd` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_aman`
--

CREATE TABLE `sewing_aman` (
  `id` int NOT NULL,
  `fc_act` int NOT NULL DEFAULT '0',
  `fb_act` int NOT NULL DEFAULT '0',
  `rc_act` int NOT NULL DEFAULT '0',
  `rb_act` int NOT NULL DEFAULT '0',
  `3rd_act` int NOT NULL DEFAULT '0',
  `subass_act` int NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_fb`
--

CREATE TABLE `sewing_fb` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_fc`
--

CREATE TABLE `sewing_fc` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_pman`
--

CREATE TABLE `sewing_pman` (
  `id` int NOT NULL,
  `fc_plan` int NOT NULL DEFAULT '0',
  `fb_plan` int NOT NULL DEFAULT '0',
  `rc_plan` int NOT NULL DEFAULT '0',
  `rb_plan` int NOT NULL DEFAULT '0',
  `3rd_plan` int NOT NULL DEFAULT '0',
  `subass_plan` int NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_rb`
--

CREATE TABLE `sewing_rb` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_rc`
--

CREATE TABLE `sewing_rc` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_subass`
--

CREATE TABLE `sewing_subass` (
  `id` int NOT NULL,
  `item` varchar(255) NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `status` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sewing_target`
--

CREATE TABLE `sewing_target` (
  `id` int NOT NULL,
  `fc` int NOT NULL,
  `fb` int NOT NULL,
  `rc` int NOT NULL,
  `rb` int NOT NULL,
  `3rd` int NOT NULL,
  `subass` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `qc_3rd`
--
ALTER TABLE `qc_3rd`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `qc_fb`
--
ALTER TABLE `qc_fb`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `qc_fc`
--
ALTER TABLE `qc_fc`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `qc_ng`
--
ALTER TABLE `qc_ng`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `qc_rb`
--
ALTER TABLE `qc_rb`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `qc_rc`
--
ALTER TABLE `qc_rc`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_3rd`
--
ALTER TABLE `sewing_3rd`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_aman`
--
ALTER TABLE `sewing_aman`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_fb`
--
ALTER TABLE `sewing_fb`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_fc`
--
ALTER TABLE `sewing_fc`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_pman`
--
ALTER TABLE `sewing_pman`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_rb`
--
ALTER TABLE `sewing_rb`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_rc`
--
ALTER TABLE `sewing_rc`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_subass`
--
ALTER TABLE `sewing_subass`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sewing_target`
--
ALTER TABLE `sewing_target`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `qc_3rd`
--
ALTER TABLE `qc_3rd`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `qc_fb`
--
ALTER TABLE `qc_fb`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `qc_fc`
--
ALTER TABLE `qc_fc`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `qc_ng`
--
ALTER TABLE `qc_ng`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `qc_rb`
--
ALTER TABLE `qc_rb`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `qc_rc`
--
ALTER TABLE `qc_rc`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_3rd`
--
ALTER TABLE `sewing_3rd`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_aman`
--
ALTER TABLE `sewing_aman`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_fb`
--
ALTER TABLE `sewing_fb`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_fc`
--
ALTER TABLE `sewing_fc`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_pman`
--
ALTER TABLE `sewing_pman`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_rb`
--
ALTER TABLE `sewing_rb`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_rc`
--
ALTER TABLE `sewing_rc`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_subass`
--
ALTER TABLE `sewing_subass`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sewing_target`
--
ALTER TABLE `sewing_target`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
