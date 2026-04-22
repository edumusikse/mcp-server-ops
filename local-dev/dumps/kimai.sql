-- MySQL dump 10.13  Distrib 8.4.8, for Linux (x86_64)
--
-- Host: localhost    Database: kimai
-- ------------------------------------------------------
-- Server version	8.4.8

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `kimai2_access_token`
--

DROP TABLE IF EXISTS `kimai2_access_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_access_token` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `token` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_usage` datetime DEFAULT NULL COMMENT '(DC2Type:datetime_immutable)',
  `expires_at` datetime DEFAULT NULL COMMENT '(DC2Type:datetime_immutable)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_6FB0DB1E5F37A13B` (`token`),
  KEY `IDX_6FB0DB1EA76ED395` (`user_id`),
  CONSTRAINT `FK_6FB0DB1EA76ED395` FOREIGN KEY (`user_id`) REFERENCES `kimai2_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_access_token`
--

LOCK TABLES `kimai2_access_token` WRITE;
/*!40000 ALTER TABLE `kimai2_access_token` DISABLE KEYS */;
INSERT INTO `kimai2_access_token` VALUES (1,1,'00343969d9454b28ea2ca4af5','iphone','2026-03-08 09:32:41',NULL);
/*!40000 ALTER TABLE `kimai2_access_token` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_activities`
--

DROP TABLE IF EXISTS `kimai2_activities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_activities` (
  `id` int NOT NULL AUTO_INCREMENT,
  `project_id` int DEFAULT NULL,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `comment` text COLLATE utf8mb4_unicode_ci,
  `visible` tinyint(1) NOT NULL,
  `color` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `time_budget` int NOT NULL DEFAULT '0',
  `budget` double NOT NULL DEFAULT '0',
  `budget_type` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `billable` tinyint(1) NOT NULL DEFAULT '1',
  `invoice_text` longtext COLLATE utf8mb4_unicode_ci,
  `number` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL COMMENT '(DC2Type:datetime_immutable)',
  PRIMARY KEY (`id`),
  KEY `IDX_8811FE1C166D1F9C` (`project_id`),
  KEY `IDX_8811FE1C7AB0E859166D1F9C` (`visible`,`project_id`),
  KEY `IDX_8811FE1C7AB0E859166D1F9C5E237E06` (`visible`,`project_id`,`name`),
  KEY `IDX_8811FE1C7AB0E8595E237E06` (`visible`,`name`),
  CONSTRAINT `FK_8811FE1C166D1F9C` FOREIGN KEY (`project_id`) REFERENCES `kimai2_projects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_activities`
--

LOCK TABLES `kimai2_activities` WRITE;
/*!40000 ALTER TABLE `kimai2_activities` DISABLE KEYS */;
INSERT INTO `kimai2_activities` VALUES (1,NULL,'Meeting',NULL,1,NULL,0,0,NULL,1,NULL,'0002','2026-03-07 17:46:50'),(2,NULL,'Server config / programming',NULL,1,NULL,0,0,NULL,1,NULL,'0003','2026-03-08 05:59:17'),(3,1,'Admin',NULL,1,NULL,0,0,NULL,1,NULL,'0004','2026-03-09 08:16:02');
/*!40000 ALTER TABLE `kimai2_activities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_activities_meta`
--

DROP TABLE IF EXISTS `kimai2_activities_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_activities_meta` (
  `id` int NOT NULL AUTO_INCREMENT,
  `activity_id` int NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci,
  `visible` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_A7C0A43D81C060965E237E06` (`activity_id`,`name`),
  KEY `IDX_A7C0A43D81C06096` (`activity_id`),
  CONSTRAINT `FK_A7C0A43D81C06096` FOREIGN KEY (`activity_id`) REFERENCES `kimai2_activities` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_activities_meta`
--

LOCK TABLES `kimai2_activities_meta` WRITE;
/*!40000 ALTER TABLE `kimai2_activities_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_activities_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_activities_rates`
--

DROP TABLE IF EXISTS `kimai2_activities_rates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_activities_rates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `activity_id` int DEFAULT NULL,
  `rate` double NOT NULL,
  `fixed` tinyint(1) NOT NULL,
  `internal_rate` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_4A7F11BEA76ED39581C06096` (`user_id`,`activity_id`),
  KEY `IDX_4A7F11BEA76ED395` (`user_id`),
  KEY `IDX_4A7F11BE81C06096` (`activity_id`),
  CONSTRAINT `FK_4A7F11BE81C06096` FOREIGN KEY (`activity_id`) REFERENCES `kimai2_activities` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_4A7F11BEA76ED395` FOREIGN KEY (`user_id`) REFERENCES `kimai2_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_activities_rates`
--

LOCK TABLES `kimai2_activities_rates` WRITE;
/*!40000 ALTER TABLE `kimai2_activities_rates` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_activities_rates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_activities_teams`
--

DROP TABLE IF EXISTS `kimai2_activities_teams`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_activities_teams` (
  `activity_id` int NOT NULL,
  `team_id` int NOT NULL,
  PRIMARY KEY (`activity_id`,`team_id`),
  KEY `IDX_986998DA81C06096` (`activity_id`),
  KEY `IDX_986998DA296CD8AE` (`team_id`),
  CONSTRAINT `FK_986998DA296CD8AE` FOREIGN KEY (`team_id`) REFERENCES `kimai2_teams` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_986998DA81C06096` FOREIGN KEY (`activity_id`) REFERENCES `kimai2_activities` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_activities_teams`
--

LOCK TABLES `kimai2_activities_teams` WRITE;
/*!40000 ALTER TABLE `kimai2_activities_teams` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_activities_teams` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_bookmarks`
--

DROP TABLE IF EXISTS `kimai2_bookmarks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_bookmarks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_4016EF25A76ED3955E237E06` (`user_id`,`name`),
  KEY `IDX_4016EF25A76ED395` (`user_id`),
  CONSTRAINT `FK_4016EF25A76ED395` FOREIGN KEY (`user_id`) REFERENCES `kimai2_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_bookmarks`
--

LOCK TABLES `kimai2_bookmarks` WRITE;
/*!40000 ALTER TABLE `kimai2_bookmarks` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_bookmarks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_configuration`
--

DROP TABLE IF EXISTS `kimai2_configuration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_configuration` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_1C5D63D85E237E06` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_configuration`
--

LOCK TABLES `kimai2_configuration` WRITE;
/*!40000 ALTER TABLE `kimai2_configuration` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_configuration` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_customers`
--

DROP TABLE IF EXISTS `kimai2_customers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_customers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `comment` text COLLATE utf8mb4_unicode_ci,
  `visible` tinyint(1) NOT NULL,
  `company` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `contact` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` text COLLATE utf8mb4_unicode_ci,
  `country` varchar(2) COLLATE utf8mb4_unicode_ci NOT NULL,
  `currency` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fax` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `mobile` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(75) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `homepage` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `timezone` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `color` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `time_budget` int NOT NULL DEFAULT '0',
  `budget` double NOT NULL DEFAULT '0',
  `vat_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `budget_type` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `billable` tinyint(1) NOT NULL DEFAULT '1',
  `invoice_template_id` int DEFAULT NULL,
  `invoice_text` longtext COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT NULL COMMENT '(DC2Type:datetime_immutable)',
  `address_line1` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address_line2` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address_line3` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `postcode` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `buyer_reference` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `IDX_5A9760447AB0E859` (`visible`),
  KEY `IDX_5A97604412946D8B` (`invoice_template_id`),
  CONSTRAINT `FK_5A97604412946D8B` FOREIGN KEY (`invoice_template_id`) REFERENCES `kimai2_invoice_templates` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_customers`
--

LOCK TABLES `kimai2_customers` WRITE;
/*!40000 ALTER TABLE `kimai2_customers` DISABLE KEYS */;
INSERT INTO `kimai2_customers` VALUES (1,'ecswe','0002',NULL,1,NULL,NULL,NULL,'DE','EUR',NULL,NULL,NULL,NULL,NULL,'Europe/Brussels',NULL,0,0,NULL,NULL,1,NULL,NULL,'2026-03-07 17:42:00',NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `kimai2_customers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_customers_comments`
--

DROP TABLE IF EXISTS `kimai2_customers_comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_customers_comments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_id` int NOT NULL,
  `created_by_id` int NOT NULL,
  `message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL,
  `pinned` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `IDX_A5B142D99395C3F3` (`customer_id`),
  KEY `IDX_A5B142D9B03A8386` (`created_by_id`),
  CONSTRAINT `FK_A5B142D99395C3F3` FOREIGN KEY (`customer_id`) REFERENCES `kimai2_customers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_A5B142D9B03A8386` FOREIGN KEY (`created_by_id`) REFERENCES `kimai2_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_customers_comments`
--

LOCK TABLES `kimai2_customers_comments` WRITE;
/*!40000 ALTER TABLE `kimai2_customers_comments` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_customers_comments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_customers_meta`
--

DROP TABLE IF EXISTS `kimai2_customers_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_customers_meta` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_id` int NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci,
  `visible` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_A48A760F9395C3F35E237E06` (`customer_id`,`name`),
  KEY `IDX_A48A760F9395C3F3` (`customer_id`),
  CONSTRAINT `FK_A48A760F9395C3F3` FOREIGN KEY (`customer_id`) REFERENCES `kimai2_customers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_customers_meta`
--

LOCK TABLES `kimai2_customers_meta` WRITE;
/*!40000 ALTER TABLE `kimai2_customers_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_customers_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_customers_rates`
--

DROP TABLE IF EXISTS `kimai2_customers_rates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_customers_rates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `customer_id` int DEFAULT NULL,
  `rate` double NOT NULL,
  `fixed` tinyint(1) NOT NULL,
  `internal_rate` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_82AB0AECA76ED3959395C3F3` (`user_id`,`customer_id`),
  KEY `IDX_82AB0AECA76ED395` (`user_id`),
  KEY `IDX_82AB0AEC9395C3F3` (`customer_id`),
  CONSTRAINT `FK_82AB0AEC9395C3F3` FOREIGN KEY (`customer_id`) REFERENCES `kimai2_customers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_82AB0AECA76ED395` FOREIGN KEY (`user_id`) REFERENCES `kimai2_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_customers_rates`
--

LOCK TABLES `kimai2_customers_rates` WRITE;
/*!40000 ALTER TABLE `kimai2_customers_rates` DISABLE KEYS */;
INSERT INTO `kimai2_customers_rates` VALUES (1,1,1,40,0,NULL);
/*!40000 ALTER TABLE `kimai2_customers_rates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_customers_teams`
--

DROP TABLE IF EXISTS `kimai2_customers_teams`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_customers_teams` (
  `customer_id` int NOT NULL,
  `team_id` int NOT NULL,
  PRIMARY KEY (`customer_id`,`team_id`),
  KEY `IDX_50BD83889395C3F3` (`customer_id`),
  KEY `IDX_50BD8388296CD8AE` (`team_id`),
  CONSTRAINT `FK_50BD8388296CD8AE` FOREIGN KEY (`team_id`) REFERENCES `kimai2_teams` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_50BD83889395C3F3` FOREIGN KEY (`customer_id`) REFERENCES `kimai2_customers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_customers_teams`
--

LOCK TABLES `kimai2_customers_teams` WRITE;
/*!40000 ALTER TABLE `kimai2_customers_teams` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_customers_teams` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_export_templates`
--

DROP TABLE IF EXISTS `kimai2_export_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_export_templates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `renderer` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `language` varchar(6) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `columns` json NOT NULL,
  `options` json NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_2F0CA26F2B36786B` (`title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_export_templates`
--

LOCK TABLES `kimai2_export_templates` WRITE;
/*!40000 ALTER TABLE `kimai2_export_templates` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_export_templates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_invoice_templates`
--

DROP TABLE IF EXISTS `kimai2_invoice_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_invoice_templates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `company` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` text COLLATE utf8mb4_unicode_ci,
  `due_days` int NOT NULL,
  `vat` double DEFAULT '0',
  `calculator` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `number_generator` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `renderer` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payment_terms` text COLLATE utf8mb4_unicode_ci,
  `vat_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `contact` longtext COLLATE utf8mb4_unicode_ci,
  `payment_details` longtext COLLATE utf8mb4_unicode_ci,
  `language` varchar(6) COLLATE utf8mb4_unicode_ci NOT NULL,
  `customer_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_1626CFE95E237E06` (`name`),
  KEY `IDX_1626CFE99395C3F3` (`customer_id`),
  CONSTRAINT `FK_1626CFE99395C3F3` FOREIGN KEY (`customer_id`) REFERENCES `kimai2_customers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_invoice_templates`
--

LOCK TABLES `kimai2_invoice_templates` WRITE;
/*!40000 ALTER TABLE `kimai2_invoice_templates` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_invoice_templates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_invoice_templates_meta`
--

DROP TABLE IF EXISTS `kimai2_invoice_templates_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_invoice_templates_meta` (
  `id` int NOT NULL AUTO_INCREMENT,
  `template_id` int NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci,
  `visible` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_A165B0555DA0FB85E237E06` (`template_id`,`name`),
  KEY `IDX_A165B0555DA0FB8` (`template_id`),
  CONSTRAINT `FK_A165B0555DA0FB8` FOREIGN KEY (`template_id`) REFERENCES `kimai2_invoice_templates` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_invoice_templates_meta`
--

LOCK TABLES `kimai2_invoice_templates_meta` WRITE;
/*!40000 ALTER TABLE `kimai2_invoice_templates_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_invoice_templates_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_invoices`
--

DROP TABLE IF EXISTS `kimai2_invoices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_invoices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_id` int NOT NULL,
  `user_id` int NOT NULL,
  `invoice_number` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL,
  `timezone` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `total` double NOT NULL,
  `tax` double NOT NULL,
  `currency` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `due_days` int NOT NULL,
  `vat` double NOT NULL,
  `invoice_filename` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payment_date` date DEFAULT NULL,
  `comment` longtext COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_76C38E372DA68207` (`invoice_number`),
  UNIQUE KEY `UNIQ_76C38E372323B33D` (`invoice_filename`),
  KEY `IDX_76C38E37A76ED395` (`user_id`),
  KEY `IDX_76C38E379395C3F3` (`customer_id`),
  CONSTRAINT `FK_76C38E379395C3F3` FOREIGN KEY (`customer_id`) REFERENCES `kimai2_customers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_76C38E37A76ED395` FOREIGN KEY (`user_id`) REFERENCES `kimai2_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_invoices`
--

LOCK TABLES `kimai2_invoices` WRITE;
/*!40000 ALTER TABLE `kimai2_invoices` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_invoices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_invoices_meta`
--

DROP TABLE IF EXISTS `kimai2_invoices_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_invoices_meta` (
  `id` int NOT NULL AUTO_INCREMENT,
  `invoice_id` int NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci,
  `visible` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_7EDC37D92989F1FD5E237E06` (`invoice_id`,`name`),
  KEY `IDX_7EDC37D92989F1FD` (`invoice_id`),
  CONSTRAINT `FK_7EDC37D92989F1FD` FOREIGN KEY (`invoice_id`) REFERENCES `kimai2_invoices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_invoices_meta`
--

LOCK TABLES `kimai2_invoices_meta` WRITE;
/*!40000 ALTER TABLE `kimai2_invoices_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_invoices_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_projects`
--

DROP TABLE IF EXISTS `kimai2_projects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_projects` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_id` int NOT NULL,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `order_number` tinytext COLLATE utf8mb4_unicode_ci,
  `comment` text COLLATE utf8mb4_unicode_ci,
  `visible` tinyint(1) NOT NULL,
  `budget` double NOT NULL DEFAULT '0',
  `color` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `time_budget` int NOT NULL DEFAULT '0',
  `order_date` datetime DEFAULT NULL,
  `start` datetime DEFAULT NULL,
  `end` datetime DEFAULT NULL,
  `timezone` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `budget_type` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `billable` tinyint(1) NOT NULL DEFAULT '1',
  `invoice_text` longtext COLLATE utf8mb4_unicode_ci,
  `global_activities` tinyint(1) NOT NULL DEFAULT '1',
  `number` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL COMMENT '(DC2Type:datetime_immutable)',
  PRIMARY KEY (`id`),
  KEY `IDX_407F12069395C3F3` (`customer_id`),
  KEY `IDX_407F12069395C3F37AB0E8595E237E06` (`customer_id`,`visible`,`name`),
  KEY `IDX_407F12069395C3F37AB0E859BF396750` (`customer_id`,`visible`,`id`),
  CONSTRAINT `FK_407F12069395C3F3` FOREIGN KEY (`customer_id`) REFERENCES `kimai2_customers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_projects`
--

LOCK TABLES `kimai2_projects` WRITE;
/*!40000 ALTER TABLE `kimai2_projects` DISABLE KEYS */;
INSERT INTO `kimai2_projects` VALUES (1,1,'Server',NULL,NULL,1,0,NULL,0,NULL,NULL,NULL,'Europe/Brussels',NULL,1,NULL,1,'0002','2026-03-07 17:42:45'),(2,1,'User poll',NULL,NULL,1,0,NULL,0,NULL,NULL,NULL,'Europe/Brussels',NULL,1,NULL,1,'0003','2026-03-08 06:00:23');
/*!40000 ALTER TABLE `kimai2_projects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_projects_comments`
--

DROP TABLE IF EXISTS `kimai2_projects_comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_projects_comments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `project_id` int NOT NULL,
  `created_by_id` int NOT NULL,
  `message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL,
  `pinned` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `IDX_29A23638166D1F9C` (`project_id`),
  KEY `IDX_29A23638B03A8386` (`created_by_id`),
  CONSTRAINT `FK_29A23638166D1F9C` FOREIGN KEY (`project_id`) REFERENCES `kimai2_projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_29A23638B03A8386` FOREIGN KEY (`created_by_id`) REFERENCES `kimai2_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_projects_comments`
--

LOCK TABLES `kimai2_projects_comments` WRITE;
/*!40000 ALTER TABLE `kimai2_projects_comments` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_projects_comments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_projects_meta`
--

DROP TABLE IF EXISTS `kimai2_projects_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_projects_meta` (
  `id` int NOT NULL AUTO_INCREMENT,
  `project_id` int NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci,
  `visible` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_50536EF2166D1F9C5E237E06` (`project_id`,`name`),
  KEY `IDX_50536EF2166D1F9C` (`project_id`),
  CONSTRAINT `FK_50536EF2166D1F9C` FOREIGN KEY (`project_id`) REFERENCES `kimai2_projects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_projects_meta`
--

LOCK TABLES `kimai2_projects_meta` WRITE;
/*!40000 ALTER TABLE `kimai2_projects_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_projects_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_projects_rates`
--

DROP TABLE IF EXISTS `kimai2_projects_rates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_projects_rates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `project_id` int DEFAULT NULL,
  `rate` double NOT NULL,
  `fixed` tinyint(1) NOT NULL,
  `internal_rate` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_41535D55A76ED395166D1F9C` (`user_id`,`project_id`),
  KEY `IDX_41535D55A76ED395` (`user_id`),
  KEY `IDX_41535D55166D1F9C` (`project_id`),
  CONSTRAINT `FK_41535D55166D1F9C` FOREIGN KEY (`project_id`) REFERENCES `kimai2_projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_41535D55A76ED395` FOREIGN KEY (`user_id`) REFERENCES `kimai2_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_projects_rates`
--

LOCK TABLES `kimai2_projects_rates` WRITE;
/*!40000 ALTER TABLE `kimai2_projects_rates` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_projects_rates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_projects_teams`
--

DROP TABLE IF EXISTS `kimai2_projects_teams`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_projects_teams` (
  `project_id` int NOT NULL,
  `team_id` int NOT NULL,
  PRIMARY KEY (`project_id`,`team_id`),
  KEY `IDX_9345D431166D1F9C` (`project_id`),
  KEY `IDX_9345D431296CD8AE` (`team_id`),
  CONSTRAINT `FK_9345D431166D1F9C` FOREIGN KEY (`project_id`) REFERENCES `kimai2_projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_9345D431296CD8AE` FOREIGN KEY (`team_id`) REFERENCES `kimai2_teams` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_projects_teams`
--

LOCK TABLES `kimai2_projects_teams` WRITE;
/*!40000 ALTER TABLE `kimai2_projects_teams` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_projects_teams` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_roles`
--

DROP TABLE IF EXISTS `kimai2_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `roles_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_roles`
--

LOCK TABLES `kimai2_roles` WRITE;
/*!40000 ALTER TABLE `kimai2_roles` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_roles_permissions`
--

DROP TABLE IF EXISTS `kimai2_roles_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_roles_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_id` int NOT NULL,
  `permission` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `allowed` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `role_permission` (`role_id`,`permission`),
  KEY `IDX_D263A3B8D60322AC` (`role_id`),
  CONSTRAINT `FK_D263A3B8D60322AC` FOREIGN KEY (`role_id`) REFERENCES `kimai2_roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_roles_permissions`
--

LOCK TABLES `kimai2_roles_permissions` WRITE;
/*!40000 ALTER TABLE `kimai2_roles_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_roles_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_sessions`
--

DROP TABLE IF EXISTS `kimai2_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_sessions` (
  `id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `data` blob NOT NULL,
  `time` int unsigned NOT NULL,
  `lifetime` int unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_sessions`
--

LOCK TABLES `kimai2_sessions` WRITE;
/*!40000 ALTER TABLE `kimai2_sessions` DISABLE KEYS */;
INSERT INTO `kimai2_sessions` VALUES ('0oo8mr4ol9kdiqisrsnql63igj',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772908838;s:1:\"c\";i:1772908838;s:1:\"l\";i:0;}',1772908838,1773513638),('0p7185t6v2kv9pk4c60pl1drlm',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"zahnLgAcEvRbjZSgX-MvE8kn91mLz_Jxgq7dtfJgi4c\";}_sf2_meta|a:3:{s:1:\"u\";i:1772901002;s:1:\"c\";i:1772901002;s:1:\"l\";i:0;}',1772901002,1773505802),('11uo0fff5qh88e9uge2s485u8b',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"_3WW15ZEAZ4ruqj6rRpzo3QE7flA6r4YoNstWatpKa0\";}_sf2_meta|a:3:{s:1:\"u\";i:1772904638;s:1:\"c\";i:1772904638;s:1:\"l\";i:0;}',1772904638,1773509438),('19u3ge5s6uebr7eqcked6fit1n',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"JW-9UqbhT17EIFZ1ZrZijFEjzzD4bAKD3ie1JPvFNfg\";}_sf2_meta|a:3:{s:1:\"u\";i:1772904622;s:1:\"c\";i:1772904621;s:1:\"l\";i:0;}',1772904622,1773509422),('1dv69c6euk4u57puat58ihaa9s',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"E-2Qe_1JCZjjtmlsbaNTjrsefvZJfxL72nH_O_HyRTU\";}_sf2_meta|a:3:{s:1:\"u\";i:1772975181;s:1:\"c\";i:1772975181;s:1:\"l\";i:0;}',1772975181,1773579981),('1qan3m6dm3g6sd1almeg73lq52',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"qB663jBhHTss3fhruB1ulD1zJLLUg4q5JuoYupjNb54\";}_sf2_meta|a:3:{s:1:\"u\";i:1772903485;s:1:\"c\";i:1772903485;s:1:\"l\";i:0;}',1772903485,1773508285),('1uicb326g6ntkcguvn5rgk7ovi',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"jMW5F7PvugaZdOqif9_qP6C5pqMIeoS56nROsUFmcBg\";}_sf2_meta|a:3:{s:1:\"u\";i:1772929784;s:1:\"c\";i:1772929784;s:1:\"l\";i:0;}',1772929784,1773534584),('2e912p5fvp0jfvhjts363bloj7',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"-S1CSvRwn6H5eZvDEI6E07ran45jElr2dL3qInuaYZA\";}_sf2_meta|a:3:{s:1:\"u\";i:1772901001;s:1:\"c\";i:1772901001;s:1:\"l\";i:0;}',1772901001,1773505801),('2rclrli9iclfaqolr6hi5nh68l',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772990448;s:1:\"c\";i:1772990448;s:1:\"l\";i:0;}',1772990448,1773595248),('2tr03rv4uj05ddqmsl0p7otdlt',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772963661;s:1:\"c\";i:1772963661;s:1:\"l\";i:0;}',1772963661,1773568461),('31lqb9nn659ea6ibmr35c19ecd',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"0uEVB6F9-WEEZ2aiBuo6h76Lp4odJziZrsN6vc9PxtU\";}_sf2_meta|a:3:{s:1:\"u\";i:1772906802;s:1:\"c\";i:1772906802;s:1:\"l\";i:0;}',1772906802,1773511602),('325e2lr3on9s8dtukiftds32t9',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"VDtAaTBSQwnXtkUXFqeC0JRvpyyLi1b0bSn0c_m3hOM\";}_sf2_meta|a:3:{s:1:\"u\";i:1773075280;s:1:\"c\";i:1773075280;s:1:\"l\";i:0;}',1773075280,1773680080),('34pl9fo15sdckjbuukroaplaq9',_binary '_sf2_attributes|a:3:{s:34:\"_security.secured_area.target_path\";s:39:\"https://time.edumusik.net/en/dashboard/\";s:24:\"_csrf/https-authenticate\";s:43:\"vnet1QHVFyCm4WfJ9Nd-WH5eLp1h6U1pR9Kdsv5g9xQ\";s:26:\"_csrf/https-password_reset\";s:43:\"seRnRIc5fqXinAZgQiWOQX8O5yofSr7Sy-ixeuX7ba8\";}_sf2_meta|a:3:{s:1:\"u\";i:1772904636;s:1:\"c\";i:1772904629;s:1:\"l\";i:0;}',1772904636,1773509436),('36r5b4htq3trfa2kokerad6ig0',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"kXoDw0RST-n0rMPt5SmvIyfXxHkjbsTPJKfU3LJ1ZVI\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900224;s:1:\"c\";i:1772900219;s:1:\"l\";i:0;}',1772900224,1773505024),('3dqb9ugc7p9e19509bin3irf8d',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772916465;s:1:\"c\";i:1772916465;s:1:\"l\";i:0;}',1772916465,1773521265),('3hbo17o6e036vlrunmtcopjc49',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"aSx-RC8oR9PjBMpgs-92TQ8yuJAVChu-2shO7jlXZn8\";}_sf2_meta|a:3:{s:1:\"u\";i:1772916732;s:1:\"c\";i:1772916732;s:1:\"l\";i:0;}',1772916732,1773521532),('3ii8sscmpti14ab4g97mo0hi7f',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"eLfrbyr0Xd4BXfum8htcDSkjx0vvGtn5sbz_ygDpJJ4\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900996;s:1:\"c\";i:1772900996;s:1:\"l\";i:0;}',1772900996,1773505796),('3k60i48s2rm67pquql5ou14q8u',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"Iazf_s8F-tOsvNG2r7na_SeSwFFUH1UR6f1vYPdeVmk\";}_sf2_meta|a:3:{s:1:\"u\";i:1772963890;s:1:\"c\";i:1772963890;s:1:\"l\";i:0;}',1772963890,1773568690),('3ko8s154dk470623qje6u1dotl',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772904638;s:1:\"c\";i:1772904638;s:1:\"l\";i:0;}',1772904638,1773509438),('3llfhjtjoukg6hjrn2g6cca61b',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772901002;s:1:\"c\";i:1772901002;s:1:\"l\";i:0;}',1772901002,1773505802),('3odvk61jfbuv53kk21aq5ld6bs',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"Kj-ZVIOZsufsogo0y9CQBcVINZEUcAghJbZIW2HG8C8\";}_sf2_meta|a:3:{s:1:\"u\";i:1772909897;s:1:\"c\";i:1772909897;s:1:\"l\";i:0;}',1772909897,1773514697),('3rt6oifgaip7he8hbgi8soi2h8',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772946335;s:1:\"c\";i:1772946335;s:1:\"l\";i:0;}',1772946335,1773551135),('56dhko6d3fv9ki1rd9u9lvslm8',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"-x-Og36klnDcMlVJtAiYXsLaJglCgPIiZMa3x7-eV80\";}_sf2_meta|a:3:{s:1:\"u\";i:1772990053;s:1:\"c\";i:1772990053;s:1:\"l\";i:0;}',1772990053,1773594853),('5oegflr55gd8pfkdfadhk9khg2',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"0NqokiHMA6WJ1m6ZwQXNa_CEgZ-rKn8pKyMsL37Msjk\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900995;s:1:\"c\";i:1772900995;s:1:\"l\";i:0;}',1772900995,1773505795),('6i6q9ciehevllm92v2s17r1mev',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772989297;s:1:\"c\";i:1772989297;s:1:\"l\";i:0;}',1772989297,1773594097),('77li60kch66f376hmvp8s8ipkk',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"O0Duh0zDKwTA7T8lKspsEiblne6MH9-IeQX2ezfEgWQ\";}_sf2_meta|a:3:{s:1:\"u\";i:1772909892;s:1:\"c\";i:1772909892;s:1:\"l\";i:0;}',1772909892,1773514692),('78drc7jlifi50825pdhh13ehi2',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"L5FxKr1yoDQ4vwSB9uRehqBsUUvgGcnghuceEl7mgaA\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900233;s:1:\"c\";i:1772900233;s:1:\"l\";i:0;}',1772900233,1773505033),('79p35bb99q3lk76h1id8rf8m5e',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"aPyy14ctj1sNnv87td8EaxlV8nyZQojqkxmTQNUfNMU\";}_sf2_meta|a:3:{s:1:\"u\";i:1772908838;s:1:\"c\";i:1772908838;s:1:\"l\";i:0;}',1772908838,1773513638),('7iji8pt0lpjc0979pe8hd6ghgq',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"LCMNlXukmg4z4ptG0jDsRaAZcr_K8xU4FY8JFts_5gQ\";}_sf2_meta|a:3:{s:1:\"u\";i:1772905556;s:1:\"c\";i:1772905556;s:1:\"l\";i:0;}',1772905556,1773510356),('7tn4h53ni5dmb98f9kj9dadlm6',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772929784;s:1:\"c\";i:1772929784;s:1:\"l\";i:0;}',1772929784,1773534584),('8kcuvut0ts369k8i4f8cc26duk',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772916732;s:1:\"c\";i:1772916732;s:1:\"l\";i:0;}',1772916732,1773521532),('8osj1kc8hsrfhq44lej8281d8o',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1773075280;s:1:\"c\";i:1773075280;s:1:\"l\";i:0;}',1773075280,1773680080),('99vs4ck4pa90vh3315273phhsk',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"oSnNUeHPdqLrIku5CXBhITnJ64dvdcsy1Xhsko6A2x8\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900848;s:1:\"c\";i:1772900848;s:1:\"l\";i:0;}',1772900848,1773505648),('9mnq74d318mh1h046uda96kjgo',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"q80-wnyVy2EFqce-Wr7oxhr5xoXzkHfv0IgkpfnS2RA\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900909;s:1:\"c\";i:1772900908;s:1:\"l\";i:0;}',1772900909,1773505709),('a09ufbgs47qt7j6bggt8bqrs3g',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"un0ZTSLl425u9X3fk9BlaVAhxCgOC-1EsV27Jn3nQ3Y\";}_sf2_meta|a:3:{s:1:\"u\";i:1772904622;s:1:\"c\";i:1772904621;s:1:\"l\";i:0;}',1772904622,1773509422),('a696mea07vvu76ks404217pkit',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"sE9xjn4QQHK8OrR9-sN-xhcihe8Cg-BC4bYlweUQvyw\";}_sf2_meta|a:3:{s:1:\"u\";i:1772989230;s:1:\"c\";i:1772989230;s:1:\"l\";i:0;}',1772989230,1773594030),('aepnqvu7pu8oup45iop3sn476s',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"hrWb1JvSuIuNFGMxusIq5lg10q6r3GZEfp5dv_aemIk\";}_sf2_meta|a:3:{s:1:\"u\";i:1772946335;s:1:\"c\";i:1772946335;s:1:\"l\";i:0;}',1772946335,1773551135),('arq18gqojo7lpdu0qpbvu78ecs',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772958799;s:1:\"c\";i:1772958799;s:1:\"l\";i:0;}',1772958799,1773563599),('au1mjc4cch68tlns9qnkfejnkb',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"1PUOG1H7rUSNONP1yZhpg7zFK0SXJCQuVBhuhhzdI-4\";}_sf2_meta|a:3:{s:1:\"u\";i:1773040686;s:1:\"c\";i:1773040686;s:1:\"l\";i:0;}',1773040686,1773645486),('b1jrbtr2gbmapgcf0pegdnft31',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772926034;s:1:\"c\";i:1772926034;s:1:\"l\";i:0;}',1772926034,1773530834),('bbbslddj7lj9qi5sc6ej3f2tf2',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772903807;s:1:\"c\";i:1772903807;s:1:\"l\";i:0;}',1772903807,1773508607),('bj4ks2rb3jarl2irvptbian53v',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1773022896;s:1:\"c\";i:1773022896;s:1:\"l\";i:0;}',1773022896,1773627696),('ce87jdo1p5ar9r25h97hb6ods7',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"IERhn2C-zkZOmf8hlpeKeZpqN6T3d1VldZwAf97Ad8U\";}_sf2_meta|a:3:{s:1:\"u\";i:1772903807;s:1:\"c\";i:1772903807;s:1:\"l\";i:0;}',1772903807,1773508607),('d308m6gc7lq6b1mq2381m49onp',_binary '_sf2_attributes|a:3:{s:34:\"_security.secured_area.target_path\";s:39:\"https://time.edumusik.net/en/dashboard/\";s:24:\"_csrf/https-authenticate\";s:43:\"_1OIPR1DW7i-77wCDQPGFmArd7InMohPBIYLFn44s2s\";s:26:\"_csrf/https-password_reset\";s:43:\"CUVsxuNbpWXtUym0byjeZdyyTAVdURW-AAHUUVqjQYo\";}_sf2_meta|a:3:{s:1:\"u\";i:1772908156;s:1:\"c\";i:1772908140;s:1:\"l\";i:0;}',1772908156,1773512956),('e1polcpb8fhcieik1lun8vk4ar',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"-LJvd9K106yVw1SJZh_epSne2X2elv0nHqnmOanPnUg\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900215;s:1:\"c\";i:1772900215;s:1:\"l\";i:0;}',1772900215,1773505015),('efu081bnr37djt4kno090t7uff',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"z70rGNMA_4IuZADSOpc-wNNEGfBfHyg9mqws4zQihvo\";}_sf2_meta|a:3:{s:1:\"u\";i:1772926034;s:1:\"c\";i:1772926034;s:1:\"l\";i:0;}',1772926034,1773530834),('ejld0mn22mfbb20f5p7f930lqm',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772990053;s:1:\"c\";i:1772990053;s:1:\"l\";i:0;}',1772990053,1773594853),('es2lo446pii314ijhnjk00ofjv',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"hdhb1STHAEHaYyOtYeliZcKx2wqqHTVeQCEqBG8kews\";}_sf2_meta|a:3:{s:1:\"u\";i:1772908135;s:1:\"c\";i:1772908132;s:1:\"l\";i:0;}',1772908135,1773512935),('f0kcp5qsc4bj4sa8mhtq878k7b',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772901001;s:1:\"c\";i:1772901001;s:1:\"l\";i:0;}',1772901001,1773505801),('f0s7d1l4vtjpjcub9pia1s98ta',_binary '_sf2_attributes|a:3:{s:34:\"_security.secured_area.target_path\";s:39:\"https://time.edumusik.net/en/dashboard/\";s:24:\"_csrf/https-authenticate\";s:43:\"QXeU-y8bpYfEji3Tp_OjVOjFfI-z9KHJ4q1o_aQBcq0\";s:26:\"_csrf/https-password_reset\";s:43:\"x2DkExsmlCe6yKP-UokxPFEI9WbIjO0d44nwq_eUZGo\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900256;s:1:\"c\";i:1772900240;s:1:\"l\";i:0;}',1772900256,1773505056),('feshj4ol6hmcmhqksggi1o9mpj',_binary '_sf2_attributes|a:3:{s:34:\"_security.secured_area.target_path\";s:39:\"https://time.edumusik.net/en/dashboard/\";s:24:\"_csrf/https-authenticate\";s:43:\"SqeoTEYMU4LzDqNHpU0Ljt9HVWHocymj6zgUFwYqns8\";s:26:\"_csrf/https-password_reset\";s:43:\"HcBRG_mdAQuNBn3m7q2OJmH422eMkqLoVn4wAywzrcM\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900912;s:1:\"c\";i:1772900911;s:1:\"l\";i:0;}',1772900912,1773505712),('fpji18uthiutk9s93r1ncg2r7f',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"O_0eUgByVuK6C9ULNU4eBEzOkQSgVC9tUpBG0IgMCZY\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900896;s:1:\"c\";i:1772900896;s:1:\"l\";i:0;}',1772900896,1773505696),('fv9su6kbea5ibj9qthh2untu95',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"WtRftWla_zGzrOD40X7dOOzpSCSayHjoWu0Ox-hdRLE\";}_sf2_meta|a:3:{s:1:\"u\";i:1772990221;s:1:\"c\";i:1772990221;s:1:\"l\";i:0;}',1772990221,1773595021),('g646qjm4v73okhe45q7tbe95lc',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"C9DBqgDnDBEKlepby1leFIs27xMHlHy2CvrX5UhpVWk\";}_sf2_meta|a:3:{s:1:\"u\";i:1772991931;s:1:\"c\";i:1772991930;s:1:\"l\";i:0;}',1772991931,1773596731),('g791d1dqrh651uc622n6j4m6b8',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"XXS_i5ViSg-7pTOuW3unxe5BxYm15pxy9prPgzr6YRw\";}_sf2_meta|a:3:{s:1:\"u\";i:1772901427;s:1:\"c\";i:1772901427;s:1:\"l\";i:0;}',1772901427,1773506227),('gce1o8vuumoh6sp00pgk8uoqhe',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:39:\"https://time.edumusik.net/en/timesheet/\";s:24:\"_csrf/https-authenticate\";s:43:\"rycgA-ha4d_uj6oL5MtERVWtRlV_g8CasaZPHXzTOpU\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900322;s:1:\"c\";i:1772900322;s:1:\"l\";i:0;}',1772900322,1773505122),('h0vu5n2gtv9g1rihk2et5j8a0s',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1773089304;s:1:\"c\";i:1773089304;s:1:\"l\";i:0;}',1773089304,1773694104),('h39gb7bqs48l6rk7dktp5s90kr',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"pMn0hbnH7OeGrBBCS7EYZB2xhpwcal0QqHnCb4QoRTg\";}_sf2_meta|a:3:{s:1:\"u\";i:1772903671;s:1:\"c\";i:1772903671;s:1:\"l\";i:0;}',1772903671,1773508471),('hapgdgfrv82f3jpc264p7041ed',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900996;s:1:\"c\";i:1772900996;s:1:\"l\";i:0;}',1772900996,1773505796),('hpb657epbd2upmpv42bofk7gl0',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772990354;s:1:\"c\";i:1772990354;s:1:\"l\";i:0;}',1772990354,1773595154),('i9f3op0kapbsa4ii296jhm5ele',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"4jMtmIHhBZv8ndglOid0ibNNiv2qOISOhCubsbQfEYg\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900212;s:1:\"c\";i:1772900208;s:1:\"l\";i:0;}',1772900212,1773505012),('ik1arsdeeqs13r28rdfpbbrb02',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"iV4_1s6eMeWZBpMT9B25PiwSETNLx3ATih6tgd4hHGk\";}_sf2_meta|a:3:{s:1:\"u\";i:1772916466;s:1:\"c\";i:1772916466;s:1:\"l\";i:0;}',1772916466,1773521266),('irdi3moe7ndbpkpru6p9dtt5l9',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"vADNWxg6N74XKoJPv4ohVmRtwwTPSykAUcce1nF8Xak\";}_sf2_meta|a:3:{s:1:\"u\";i:1772930171;s:1:\"c\";i:1772930171;s:1:\"l\";i:0;}',1772930171,1773534971),('k2dfofhtnv0btv54n9kd0diio2',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772963889;s:1:\"c\";i:1772963889;s:1:\"l\";i:0;}',1772963889,1773568689),('k8461rtttgtapqgkju85rvl0m1',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900215;s:1:\"c\";i:1772900215;s:1:\"l\";i:0;}',1772900215,1773505015),('k8gg0hp2npa0v7fn6a8jjv20tg',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"0DFDphIwg9Sld6-Ufq8V2brNSdmWIhdci7k7_F0pAvw\";}_sf2_meta|a:3:{s:1:\"u\";i:1773022896;s:1:\"c\";i:1773022896;s:1:\"l\";i:0;}',1773022896,1773627696),('krk611375nv0qs2dlskh36k2u2',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"-SNMcGBB4lvtUm9xCuh5GEJraQ9mGk8by3QapjkGQuU\";}_sf2_meta|a:3:{s:1:\"u\";i:1772989297;s:1:\"c\";i:1772989297;s:1:\"l\";i:0;}',1772989297,1773594097),('ktt06ct2hiclu0b0u3a7i65lf0',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772989230;s:1:\"c\";i:1772989230;s:1:\"l\";i:0;}',1772989230,1773594030),('ktvq49aud533ld30pr57s645n2',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"bNebBkd4TmoNDz8Ep2um6LgRm1RVpN-SoRTVgqYrTgc\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900498;s:1:\"c\";i:1772900498;s:1:\"l\";i:0;}',1772900498,1773505298),('kvq1s6ac6163ejdgkjodprqouu',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"Fz8MmlC-0FLq1f2Ayd0fYJbQirK1jNvSQryKHYTxBXk\";}_sf2_meta|a:3:{s:1:\"u\";i:1772904727;s:1:\"c\";i:1772904727;s:1:\"l\";i:0;}',1772904727,1773509527),('l1k7bncn6cchf5ggkoj2m661gt',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"fZ-y9PUgVoST_GA3Y2CMRE6cNYOtic6m3TSS7tQnm8A\";}_sf2_meta|a:3:{s:1:\"u\";i:1773034312;s:1:\"c\";i:1773034311;s:1:\"l\";i:0;}',1773034312,1773639112),('l4vtuihipmobt9d4mqsid8aogm',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900208;s:1:\"c\";i:1772900208;s:1:\"l\";i:0;}',1772900208,1773505008),('l7ndta6ps0iucgo7prmkvj0h41',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772901001;s:1:\"c\";i:1772901001;s:1:\"l\";i:0;}',1772901001,1773505801),('lg70i02k3e69u30efa4j69c6mj',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"a4y4gIUNm094uDtZ4_0yWaspizyUR4P2OJ9L9v3fXT8\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900909;s:1:\"c\";i:1772900908;s:1:\"l\";i:0;}',1772900909,1773505709),('m9mhb223cb814o1jkfenkve63p',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"asrsE5zz1OpyZj0Xw8GmRhFzR1u0x-VwhT9ghsmKMeU\";}_sf2_meta|a:3:{s:1:\"u\";i:1772904622;s:1:\"c\";i:1772904621;s:1:\"l\";i:0;}',1772904622,1773509422),('meftajql9dbsvkiaajpqkl3c2b',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"ZozraViYZcWpaL1oRJuH6CB7491juLb2JPJi0YuBFHs\";}_sf2_meta|a:3:{s:1:\"u\";i:1772963662;s:1:\"c\";i:1772963662;s:1:\"l\";i:0;}',1772963662,1773568462),('mlar17ljfhl6o4im2en78ibbav',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1773002703;s:1:\"c\";i:1773002703;s:1:\"l\";i:0;}',1773002703,1773607503),('mvhkj9c6o625ubgoltd6p3io4b',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"Wl19ehdmOQ2qpGVIEY01OE9niATgUxPJlxLBu9d5y14\";}_sf2_meta|a:3:{s:1:\"u\";i:1772907476;s:1:\"c\";i:1772907476;s:1:\"l\";i:0;}',1772907476,1773512276),('n4ei5gr86mhbpf436hv1uc0olm',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"F7b8gJXEjAnHAmxc3lRpOxUTuQOL_A2GlimL5Ytwk5k\";}_sf2_meta|a:3:{s:1:\"u\";i:1773094062;s:1:\"c\";i:1773094060;s:1:\"l\";i:0;}',1773094062,1773698862),('o7d5lc5cb6upcom7nqks9geont',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"77dwOLx1-Q_eF55IJKBk3xIGb2EgSg6VH_INbYH0l-U\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900208;s:1:\"c\";i:1772900208;s:1:\"l\";i:0;}',1772900208,1773505008),('ofcjfsmg7tbdn4h39dcgru5tir',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"-_zSAA3objm6ROYTybtNllZa6slBhIG8Ha5WVYC62b4\";}_sf2_meta|a:3:{s:1:\"u\";i:1772939859;s:1:\"c\";i:1772939859;s:1:\"l\";i:0;}',1772939859,1773544659),('on6si0n4cfqb2qble77mevl0mn',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"NdvcDBSLAndYVItFe7iuU0aRctEYmCj8kYMsNfVFEJg\";}_sf2_meta|a:3:{s:1:\"u\";i:1772958800;s:1:\"c\";i:1772958800;s:1:\"l\";i:0;}',1772958800,1773563600),('ouuojul89ab35kkg71b1l1keic',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772905555;s:1:\"c\";i:1772905555;s:1:\"l\";i:0;}',1772905555,1773510355),('p6bq7g505ffabgrjiv2c6ga5nh',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"Mx_v7k7Tp0Y373QrN1kfZEQYRYc5En86YMEDX7tDWYk\";}_sf2_meta|a:3:{s:1:\"u\";i:1773002558;s:1:\"c\";i:1773002552;s:1:\"l\";i:0;}',1773002558,1773607358),('p9re0llgtqrf3h3joee3tqk8e5',_binary '_sf2_attributes|a:9:{s:23:\"_security.last_username\";s:20:\"stephan@edumusik.com\";s:22:\"_security_secured_area\";s:420:\"O:74:\"Symfony\\Component\\Security\\Core\\Authentication\\Token\\UsernamePasswordToken\":3:{i:0;N;i:1;s:12:\"secured_area\";i:2;a:5:{i:0;O:15:\"App\\Entity\\User\":5:{s:2:\"id\";i:1;s:8:\"username\";s:5:\"admin\";s:7:\"enabled\";b:1;s:5:\"email\";s:20:\"stephan@edumusik.com\";s:8:\"password\";s:60:\"$2y$13$FGpcqTNdJ695VxpVgzGdxuo1OtEzDudp9sa/OmV1RgdtkvWSIYtZO\";}i:1;b:1;i:2;N;i:3;a:0:{}i:4;a:2:{i:0;s:16:\"ROLE_SUPER_ADMIN\";i:1;s:9:\"ROLE_USER\";}}}\";s:16:\"_csrf/https-form\";s:43:\"W87jaF40Wc_1_NZSDsiLU8I-ei-9vyUbciqm2C-O9_8\";s:18:\"_csrf/https-search\";s:43:\"1gGSWmyngd3yR61jot5JaKGYtcStFBYyu2KpIM326Tk\";s:28:\"_csrf/https-datatable_update\";s:43:\"sikseun-PHRdkEUTIDfzdGh90dVCiCDxahorqA1aZ1Q\";s:38:\"_csrf/https-edit_system_configurations\";s:43:\"QX89aUgtYZeRUuN02EQncr7YJJJFImmf_YA-bm5y7EQ\";s:34:\"_csrf/https-admin_invoice_template\";s:43:\"6JXoVVBuXDHkuh3ObV4iseivQ1hf_YRY1GJGq06zYjs\";s:32:\"_csrf/https-timesheet_quick_edit\";s:43:\"taQrefCCkbVydsjJgsD6Tn4L8TTTzrvQszYYzIYAW1Q\";s:32:\"_csrf/https-entities_multiupdate\";s:43:\"d616yf4Ee_b1yEGViC76sIorSix-dHB0pv9IQNjAT-M\";}_sf2_meta|a:3:{s:1:\"u\";i:1772981955;s:1:\"c\";i:1772900290;s:1:\"l\";i:0;}',1772981956,1773586756),('q095sslcqlginv2qbjks6bebdt',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"gl7Z2fhhUGPVtmKQZnkNo2jwb8u6x42G--2Rs9Oajds\";}_sf2_meta|a:3:{s:1:\"u\";i:1772920972;s:1:\"c\";i:1772920970;s:1:\"l\";i:0;}',1772920972,1773525772),('qh5m8ld3vjj99bpcb8dl0k8pr9',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772900995;s:1:\"c\";i:1772900995;s:1:\"l\";i:0;}',1772900995,1773505795),('qialff30098lps6jdub64m5s85',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"JZKHuf1-UFeByg6Ibquagq-U4cl8bDb16wl22ekdLJo\";}_sf2_meta|a:3:{s:1:\"u\";i:1772908838;s:1:\"c\";i:1772908838;s:1:\"l\";i:0;}',1772908838,1773513638),('qjaoir008dh8qb5ne1cfdbqmkf',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"pHnl3t9BLPfLf7B1DnEwm2WXjYZtGjIvEJSa-5Hnne0\";}_sf2_meta|a:3:{s:1:\"u\";i:1772943455;s:1:\"c\";i:1772943455;s:1:\"l\";i:0;}',1772943455,1773548255),('qjv73l996dkdhkjt84q1tfcpac',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"j273CjrpylxNMn5hTTwFhnkFIaC7ebntym9wpMh2gVE\";}_sf2_meta|a:3:{s:1:\"u\";i:1772901678;s:1:\"c\";i:1772901678;s:1:\"l\";i:0;}',1772901678,1773506478),('qpgg3u0mnmkerdkdg9397rf1ap',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772904727;s:1:\"c\";i:1772904727;s:1:\"l\";i:0;}',1772904727,1773509527),('qrfkrlk37n7uri1hldqs97k5va',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1773014288;s:1:\"c\";i:1773014288;s:1:\"l\";i:0;}',1773014288,1773619088),('r9puae21jt4ha0kbdu2bfajg8g',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772990221;s:1:\"c\";i:1772990221;s:1:\"l\";i:0;}',1772990221,1773595021),('rjt8m9e7qvfcf4idl4sc20jnkp',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"CY_OdP_evN8F0I2CU96RsLHrKi_goMrINPNF0aYPSZw\";}_sf2_meta|a:3:{s:1:\"u\";i:1772901678;s:1:\"c\";i:1772901678;s:1:\"l\";i:0;}',1772901678,1773506478),('rlmu73ds1sv49cdpjir4o29gnu',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"Wm12Ffy9eiTTbp-KDRSKN1ltcWWNBUBnUq5mvkdWiv8\";}_sf2_meta|a:3:{s:1:\"u\";i:1773089304;s:1:\"c\";i:1773089304;s:1:\"l\";i:0;}',1773089304,1773694104),('rn0fncmf85hto7fdlrum0t2fc1',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"IHB1SgK3rUA-xTNHbVkqrrUMc_eRX8s_fM4oKUqG-sY\";}_sf2_meta|a:3:{s:1:\"u\";i:1772901398;s:1:\"c\";i:1772901398;s:1:\"l\";i:0;}',1772901398,1773506198),('rpbdsfqh91et847m0o0jknm0ac',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"--ml6nb9J-ySCU2VPCWQdP-0TM9GzR7qM1vQrBbkSdo\";}_sf2_meta|a:3:{s:1:\"u\";i:1773002704;s:1:\"c\";i:1773002704;s:1:\"l\";i:0;}',1773002704,1773607504),('ssnu9r4n6r4mev48e6if1to8oc',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772901398;s:1:\"c\";i:1772901398;s:1:\"l\";i:0;}',1772901398,1773506198),('t4mat9of78l6j5uu03m3eg9gh1',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"Q9lYZxPNi-4b-drI60dqWf_cBm2PWtOktGV8nt8wBKU\";}_sf2_meta|a:3:{s:1:\"u\";i:1772901677;s:1:\"c\";i:1772901677;s:1:\"l\";i:0;}',1772901677,1773506477),('t7l7d8kg9a6t30op0tnd6u2hbn',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:39:\"https://time.edumusik.net/en/timesheet/\";s:24:\"_csrf/https-authenticate\";s:43:\"TsMUQZzOXhkBczr80AiBKl3GrE2KEpff93yAM8dRCPs\";}_sf2_meta|a:3:{s:1:\"u\";i:1772989352;s:1:\"c\";i:1772989352;s:1:\"l\";i:0;}',1772989352,1773594152),('tdfq9in1ghk2de9htp2v45aco0',_binary '_sf2_attributes|a:16:{s:23:\"_security.last_username\";s:20:\"stephan@edumusik.com\";s:22:\"_security_secured_area\";s:420:\"O:74:\"Symfony\\Component\\Security\\Core\\Authentication\\Token\\UsernamePasswordToken\":3:{i:0;N;i:1;s:12:\"secured_area\";i:2;a:5:{i:0;O:15:\"App\\Entity\\User\":5:{s:2:\"id\";i:1;s:8:\"username\";s:5:\"admin\";s:7:\"enabled\";b:1;s:5:\"email\";s:20:\"stephan@edumusik.com\";s:8:\"password\";s:60:\"$2y$13$FGpcqTNdJ695VxpVgzGdxuo1OtEzDudp9sa/OmV1RgdtkvWSIYtZO\";}i:1;b:1;i:2;N;i:3;a:0:{}i:4;a:2:{i:0;s:16:\"ROLE_SUPER_ADMIN\";i:1;s:9:\"ROLE_USER\";}}}\";s:18:\"_csrf/https-search\";s:43:\"BBUaM1bCsVfrx_OHEEGFWtJoC4DrxerGTZ_NlHa4oYo\";s:28:\"_csrf/https-datatable_update\";s:43:\"Rg8oviy9-EN4cZoQHnkBylXoUXd0DGxTZvhAaRaJsC8\";s:38:\"_csrf/https-edit_system_configurations\";s:43:\"qQhCNVe1kQmSAxfdbMEGrlqhP4b9eQZiJsfItk4qb6w\";s:36:\"_csrf/https-edit_user_password_token\";s:43:\"YAHCkv06G69RAueKdvOdYFy4IVerPOdgaxBAoY5dtzE\";s:29:\"_csrf/https-access_token_form\";s:43:\"n4ofsdLyUy6i30scAlujhfqp4ItSgwkvz48Fcb4IzSM\";s:31:\"_csrf/https-admin_customer_edit\";s:43:\"GOMKcsu5Xgl9UrnMcuVF9RJ9pWmg7HOREtYN-Gi9Ccs\";s:34:\"_csrf/https-admin_customer_comment\";s:43:\"T6aP4UDcrBOPB1xKt0grZUEYkFPbaIUVvSkSBg-OYwA\";s:36:\"_csrf/https-admin_customer_rate_edit\";s:43:\"srqAIzT80JNM1PwpjIe3BNGa-zBvwtBWt7AvMu729pc\";s:30:\"_csrf/https-admin_project_edit\";s:43:\"UCAKi0HK6-J-GAoDNjf61V6F7YXx2VVvftkye9KXr9s\";s:33:\"_csrf/https-admin_project_comment\";s:43:\"ftj95ofal-yV8Lff6mA5gvc9G5ohQ5lKKbq4Vc6QP3o\";s:29:\"_csrf/https-project.duplicate\";s:43:\"kqDRIJkBi-g5nOsMyWlkY0ZrcYN05X1x6bFWrzgsCI8\";s:31:\"_csrf/https-admin_activity_edit\";s:43:\"NTFvYiYzevGccaewrN5aDzgClwuGrdfWou_huMCjqj8\";s:32:\"_csrf/https-entities_multiupdate\";s:43:\"n6FJlYwYnZQQWCw5AJz4upyPOE1i0Y34G1o9FLeY7Cw\";s:26:\"_csrf/https-timesheet_edit\";s:43:\"JARXfHS_eAb6ZBbhStZ0LdytyFs96AEa-oQ2Z55pkeY\";}_sf2_meta|a:3:{s:1:\"u\";i:1773044690;s:1:\"c\";i:1772904248;s:1:\"l\";i:0;}',1773044691,1773649491),('ticj6kg188ht7s0u2gcgfa0ti6',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"Lv5Vd5xMS5CuklLse7489oyzxzWRlOpxHw3aGVvvi-Q\";}_sf2_meta|a:3:{s:1:\"u\";i:1772901001;s:1:\"c\";i:1772901001;s:1:\"l\";i:0;}',1772901001,1773505801),('tt83569b5jefki4kr3l3i2k4t8',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"b2AWyRTriu061CFky-U9cz80DMxZzdCqqAeutTE62IU\";}_sf2_meta|a:3:{s:1:\"u\";i:1772990448;s:1:\"c\";i:1772990448;s:1:\"l\";i:0;}',1772990448,1773595248),('u1k00agnbk2oj2j73qs16ujfdg',_binary '_sf2_attributes|a:2:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";s:24:\"_csrf/https-authenticate\";s:43:\"LdvizrcAEZksIPuS0RwjfR_25Yfcb8JA4tx8kESkci0\";}_sf2_meta|a:3:{s:1:\"u\";i:1772908135;s:1:\"c\";i:1772908132;s:1:\"l\";i:0;}',1772908135,1773512935),('ua24mt69ddgn1k1jrn03mjgrfq',_binary '_sf2_attributes|a:1:{s:24:\"_csrf/https-authenticate\";s:43:\"h9328Ws0G6K0D15JuS5_TQqi52OLU0bA-2RXtOd5HNw\";}_sf2_meta|a:3:{s:1:\"u\";i:1773014289;s:1:\"c\";i:1773014289;s:1:\"l\";i:0;}',1773014289,1773619089),('ul4rvrikvdnh8tio7ujd86rcqc',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772908838;s:1:\"c\";i:1772908838;s:1:\"l\";i:0;}',1772908838,1773513638),('un0spta3n2q91peqge1vh1s3ua',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772906802;s:1:\"c\";i:1772906802;s:1:\"l\";i:0;}',1772906802,1773511602),('uvld8ql1ku1hd0bm0g65iikknu',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772904772;s:1:\"c\";i:1772904772;s:1:\"l\";i:0;}',1772904772,1773509572),('v87589ds0vq6usi3363sfuqdpd',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772975181;s:1:\"c\";i:1772975181;s:1:\"l\";i:0;}',1772975181,1773579981),('vtao65f7ns7dsnsd81f4d486i5',_binary '_sf2_attributes|a:1:{s:34:\"_security.secured_area.target_path\";s:37:\"https://time.edumusik.net/en/homepage\";}_sf2_meta|a:3:{s:1:\"u\";i:1772939859;s:1:\"c\";i:1772939859;s:1:\"l\";i:0;}',1772939859,1773544659);
/*!40000 ALTER TABLE `kimai2_sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_tags`
--

DROP TABLE IF EXISTS `kimai2_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_tags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `color` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `visible` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_27CAF54C5E237E06` (`name`),
  KEY `IDX_27CAF54C7AB0E859` (`visible`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_tags`
--

LOCK TABLES `kimai2_tags` WRITE;
/*!40000 ALTER TABLE `kimai2_tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_teams`
--

DROP TABLE IF EXISTS `kimai2_teams`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_teams` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `color` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_3BEDDC7F5E237E06` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_teams`
--

LOCK TABLES `kimai2_teams` WRITE;
/*!40000 ALTER TABLE `kimai2_teams` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_teams` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_timesheet`
--

DROP TABLE IF EXISTS `kimai2_timesheet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_timesheet` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user` int NOT NULL,
  `activity_id` int NOT NULL,
  `project_id` int NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime DEFAULT NULL,
  `duration` int DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `rate` double NOT NULL,
  `fixed_rate` double DEFAULT NULL,
  `hourly_rate` double DEFAULT NULL,
  `exported` tinyint(1) NOT NULL DEFAULT '0',
  `timezone` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `internal_rate` double DEFAULT NULL,
  `billable` tinyint(1) DEFAULT '1',
  `category` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'work',
  `modified_at` datetime DEFAULT NULL,
  `date_tz` date NOT NULL,
  `break` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `IDX_4F60C6B18D93D649` (`user`),
  KEY `IDX_4F60C6B181C06096` (`activity_id`),
  KEY `IDX_4F60C6B1166D1F9C` (`project_id`),
  KEY `IDX_4F60C6B18D93D649502DF587` (`user`,`start_time`),
  KEY `IDX_4F60C6B1502DF587` (`start_time`),
  KEY `IDX_4F60C6B1502DF58741561401` (`start_time`,`end_time`),
  KEY `IDX_4F60C6B1502DF587415614018D93D649` (`start_time`,`end_time`,`user`),
  KEY `IDX_4F60C6B1BDF467148D93D649` (`date_tz`,`user`),
  KEY `IDX_4F60C6B1415614018D93D649` (`end_time`,`user`),
  KEY `IDX_TIMESHEET_TICKTAC` (`end_time`,`user`,`start_time`),
  KEY `IDX_TIMESHEET_RECENT_ACTIVITIES` (`user`,`project_id`,`activity_id`),
  KEY `IDX_TIMESHEET_RESULT_STATS` (`user`,`id`,`duration`),
  CONSTRAINT `FK_4F60C6B1166D1F9C` FOREIGN KEY (`project_id`) REFERENCES `kimai2_projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_4F60C6B181C06096` FOREIGN KEY (`activity_id`) REFERENCES `kimai2_activities` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_4F60C6B18D93D649` FOREIGN KEY (`user`) REFERENCES `kimai2_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_timesheet`
--

LOCK TABLES `kimai2_timesheet` WRITE;
/*!40000 ALTER TABLE `kimai2_timesheet` DISABLE KEYS */;
INSERT INTO `kimai2_timesheet` VALUES (1,1,1,1,'2026-02-23 10:00:00','2026-02-23 11:00:00',3600,'Brussels',40,NULL,40,0,'Europe/Brussels',40,1,'work','2026-03-07 17:49:07','2026-02-23',0),(2,1,2,1,'2026-03-08 06:00:00','2026-03-08 09:00:00',10800,'Portal',120,NULL,40,0,'Europe/Brussels',120,1,'work','2026-03-09 08:13:45','2026-03-08',0),(3,1,2,1,'2026-03-02 08:00:00','2026-03-02 10:00:00',7200,'Install Nextcloud Coolify',80,NULL,40,0,'Europe/Brussels',80,1,'work','2026-03-09 08:15:06','2026-03-02',0),(4,1,3,1,'2026-03-08 09:00:00','2026-03-08 10:00:00',3600,'Document progress',40,NULL,40,0,'Europe/Brussels',40,1,'work','2026-03-09 08:16:42','2026-03-08',0);
/*!40000 ALTER TABLE `kimai2_timesheet` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_timesheet_meta`
--

DROP TABLE IF EXISTS `kimai2_timesheet_meta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_timesheet_meta` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timesheet_id` int NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci,
  `visible` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_CB606CBAABDD46BE5E237E06` (`timesheet_id`,`name`),
  KEY `IDX_CB606CBAABDD46BE` (`timesheet_id`),
  CONSTRAINT `FK_CB606CBAABDD46BE` FOREIGN KEY (`timesheet_id`) REFERENCES `kimai2_timesheet` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_timesheet_meta`
--

LOCK TABLES `kimai2_timesheet_meta` WRITE;
/*!40000 ALTER TABLE `kimai2_timesheet_meta` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_timesheet_meta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_timesheet_tags`
--

DROP TABLE IF EXISTS `kimai2_timesheet_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_timesheet_tags` (
  `timesheet_id` int NOT NULL,
  `tag_id` int NOT NULL,
  PRIMARY KEY (`timesheet_id`,`tag_id`),
  KEY `IDX_E3284EFEABDD46BE` (`timesheet_id`),
  KEY `IDX_E3284EFEBAD26311` (`tag_id`),
  CONSTRAINT `FK_732EECA9ABDD46BE` FOREIGN KEY (`timesheet_id`) REFERENCES `kimai2_timesheet` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_732EECA9BAD26311` FOREIGN KEY (`tag_id`) REFERENCES `kimai2_tags` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_timesheet_tags`
--

LOCK TABLES `kimai2_timesheet_tags` WRITE;
/*!40000 ALTER TABLE `kimai2_timesheet_tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_timesheet_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_user_preferences`
--

DROP TABLE IF EXISTS `kimai2_user_preferences`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_user_preferences` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_8D08F631A76ED3955E237E06` (`user_id`,`name`),
  KEY `IDX_8D08F631A76ED395` (`user_id`),
  CONSTRAINT `FK_8D08F631A76ED395` FOREIGN KEY (`user_id`) REFERENCES `kimai2_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_user_preferences`
--

LOCK TABLES `kimai2_user_preferences` WRITE;
/*!40000 ALTER TABLE `kimai2_user_preferences` DISABLE KEYS */;
INSERT INTO `kimai2_user_preferences` VALUES (1,1,'timezone','Europe/Brussels'),(2,1,'language','en'),(3,1,'skin','default'),(4,1,'hourly_rate','0'),(5,1,'internal_rate',NULL),(6,1,'locale','en'),(7,1,'first_weekday','monday'),(8,1,'update_browser_title','1'),(9,1,'calendar_initial_view','month'),(10,1,'login_initial_view','timesheet'),(11,1,'favorite_routes',''),(12,1,'daily_stats',''),(13,1,'export_decimal',''),(14,1,'__wizards__','intro,profile'),(15,1,'_latest_approval',NULL),(16,2,'timezone','UTC'),(17,2,'language','en'),(18,2,'skin','auto');
/*!40000 ALTER TABLE `kimai2_user_preferences` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_users`
--

DROP TABLE IF EXISTS `kimai2_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(180) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(180) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `alias` varchar(60) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `registration_date` datetime DEFAULT NULL,
  `title` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `avatar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `roles` longtext COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '(DC2Type:array)',
  `last_login` datetime DEFAULT NULL,
  `confirmation_token` varchar(180) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password_requested_at` datetime DEFAULT NULL,
  `api_token` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `auth` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `color` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `account` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `totp_secret` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `totp_enabled` tinyint(1) NOT NULL DEFAULT '0',
  `system_account` tinyint(1) NOT NULL DEFAULT '0',
  `supervisor_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_B9AC5BCEF85E0677` (`username`),
  UNIQUE KEY `UNIQ_B9AC5BCEE7927C74` (`email`),
  UNIQUE KEY `UNIQ_B9AC5BCEC05FB297` (`confirmation_token`),
  KEY `IDX_B9AC5BCE19E9AC5F` (`supervisor_id`),
  CONSTRAINT `FK_B9AC5BCE19E9AC5F` FOREIGN KEY (`supervisor_id`) REFERENCES `kimai2_users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_users`
--

LOCK TABLES `kimai2_users` WRITE;
/*!40000 ALTER TABLE `kimai2_users` DISABLE KEYS */;
INSERT INTO `kimai2_users` VALUES (1,'admin','stephan@edumusik.com','$2y$13$FGpcqTNdJ695VxpVgzGdxuo1OtEzDudp9sa/OmV1RgdtkvWSIYtZO',NULL,1,'2026-03-07 16:16:14',NULL,NULL,'a:1:{i:0;s:16:\"ROLE_SUPER_ADMIN\";}','2026-03-08 09:32:42',NULL,NULL,NULL,'kimai',NULL,NULL,NULL,0,0,NULL),(2,'Georg Jürgens','georg.juergens@ecswe.eu','$2y$13$V5fiTEWK0DogVMJtpNDRz.mcaKA1kACaWelWXxq.XoaxYaLj.DCDS',NULL,1,'2026-03-08 09:26:04',NULL,NULL,'a:1:{i:0;s:10:\"ROLE_ADMIN\";}',NULL,NULL,NULL,NULL,'kimai',NULL,NULL,NULL,0,0,NULL);
/*!40000 ALTER TABLE `kimai2_users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_users_teams`
--

DROP TABLE IF EXISTS `kimai2_users_teams`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_users_teams` (
  `user_id` int NOT NULL,
  `team_id` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `teamlead` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_B5E92CF8A76ED395296CD8AE` (`user_id`,`team_id`),
  KEY `IDX_B5E92CF8A76ED395` (`user_id`),
  KEY `IDX_B5E92CF8296CD8AE` (`team_id`),
  CONSTRAINT `FK_B5E92CF8296CD8AE` FOREIGN KEY (`team_id`) REFERENCES `kimai2_teams` (`id`) ON DELETE CASCADE,
  CONSTRAINT `FK_B5E92CF8A76ED395` FOREIGN KEY (`user_id`) REFERENCES `kimai2_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_users_teams`
--

LOCK TABLES `kimai2_users_teams` WRITE;
/*!40000 ALTER TABLE `kimai2_users_teams` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_users_teams` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kimai2_working_times`
--

DROP TABLE IF EXISTS `kimai2_working_times`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kimai2_working_times` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `approved_by` int DEFAULT NULL,
  `date` date NOT NULL,
  `expected` int NOT NULL,
  `actual` int NOT NULL,
  `approved_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQ_F95E4933A76ED395AA9E377A` (`user_id`,`date`),
  KEY `IDX_F95E4933A76ED395` (`user_id`),
  KEY `IDX_F95E49334EA3CB3D` (`approved_by`),
  CONSTRAINT `FK_F95E49334EA3CB3D` FOREIGN KEY (`approved_by`) REFERENCES `kimai2_users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `FK_F95E4933A76ED395` FOREIGN KEY (`user_id`) REFERENCES `kimai2_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kimai2_working_times`
--

LOCK TABLES `kimai2_working_times` WRITE;
/*!40000 ALTER TABLE `kimai2_working_times` DISABLE KEYS */;
/*!40000 ALTER TABLE `kimai2_working_times` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `migration_versions`
--

DROP TABLE IF EXISTS `migration_versions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `migration_versions` (
  `version` varchar(191) COLLATE utf8mb3_unicode_ci NOT NULL,
  `executed_at` datetime DEFAULT NULL,
  `execution_time` int DEFAULT NULL,
  PRIMARY KEY (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `migration_versions`
--

LOCK TABLES `migration_versions` WRITE;
/*!40000 ALTER TABLE `migration_versions` DISABLE KEYS */;
INSERT INTO `migration_versions` VALUES ('DoctrineMigrations\\Version20180701120000','2026-03-07 16:15:58',265),('DoctrineMigrations\\Version20180715160326','2026-03-07 16:15:59',175),('DoctrineMigrations\\Version20180730044139','2026-03-07 16:15:59',49),('DoctrineMigrations\\Version20180805183527','2026-03-07 16:15:59',56),('DoctrineMigrations\\Version20180903202256','2026-03-07 16:15:59',64),('DoctrineMigrations\\Version20180905190737','2026-03-07 16:15:59',348),('DoctrineMigrations\\Version20180924111853','2026-03-07 16:15:59',45),('DoctrineMigrations\\Version20181031220003','2026-03-07 16:16:00',263),('DoctrineMigrations\\Version20190124004014','2026-03-07 16:16:00',47),('DoctrineMigrations\\Version20190201150324','2026-03-07 16:16:00',31),('DoctrineMigrations\\Version20190219200020','2026-03-07 16:16:00',1),('DoctrineMigrations\\Version20190305152308','2026-03-07 16:16:00',132),('DoctrineMigrations\\Version20190321181243','2026-03-07 16:16:00',10),('DoctrineMigrations\\Version20190502161758','2026-03-07 16:16:00',71),('DoctrineMigrations\\Version20190510205245','2026-03-07 16:16:00',38),('DoctrineMigrations\\Version20190605171157','2026-03-07 16:16:00',82),('DoctrineMigrations\\Version20190617100845','2026-03-07 16:16:00',229),('DoctrineMigrations\\Version20190706224211','2026-03-07 16:16:00',135),('DoctrineMigrations\\Version20190706224219','2026-03-07 16:16:01',120),('DoctrineMigrations\\Version20190729162655','2026-03-07 16:16:01',79),('DoctrineMigrations\\Version20190730123324','2026-03-07 16:16:01',283),('DoctrineMigrations\\Version20190813162649','2026-03-07 16:16:01',62),('DoctrineMigrations\\Version20191024100951','2026-03-07 16:16:01',60),('DoctrineMigrations\\Version20191108151534','2026-03-07 16:16:01',83),('DoctrineMigrations\\Version20191113132640','2026-03-07 16:16:01',24),('DoctrineMigrations\\Version20191116110124','2026-03-07 16:16:01',63),('DoctrineMigrations\\Version20191204120823','2026-03-07 16:16:01',46),('DoctrineMigrations\\Version20200109102138','2026-03-07 16:16:01',161),('DoctrineMigrations\\Version20200125123942','2026-03-07 16:16:02',70),('DoctrineMigrations\\Version20200204124425','2026-03-07 16:16:02',60),('DoctrineMigrations\\Version20200205115243','2026-03-07 16:16:02',319),('DoctrineMigrations\\Version20200205115244','2026-03-07 16:16:02',168),('DoctrineMigrations\\Version20200308171950','2026-03-07 16:16:02',175),('DoctrineMigrations\\Version20200323163038','2026-03-07 16:16:02',189),('DoctrineMigrations\\Version20200323163039','2026-03-07 16:16:03',0),('DoctrineMigrations\\Version20200413133226','2026-03-07 16:16:03',57),('DoctrineMigrations\\Version20200524142042','2026-03-07 16:16:03',34),('DoctrineMigrations\\Version20200705152310','2026-03-07 16:16:03',90),('DoctrineMigrations\\Version20200725213424','2026-03-07 16:16:03',147),('DoctrineMigrations\\Version20210316224358','2026-03-07 16:16:03',117),('DoctrineMigrations\\Version20210320162820','2026-03-07 16:16:03',57),('DoctrineMigrations\\Version20210405105611','2026-03-07 16:16:03',26),('DoctrineMigrations\\Version20210605154245','2026-03-07 16:16:03',103),('DoctrineMigrations\\Version20210704111542','2026-03-07 16:16:03',136),('DoctrineMigrations\\Version20210717211144','2026-03-07 16:16:03',111),('DoctrineMigrations\\Version20210719123928','2026-03-07 16:16:03',217),('DoctrineMigrations\\Version20210727104955','2026-03-07 16:16:04',183),('DoctrineMigrations\\Version20210802152259','2026-03-07 16:16:04',67),('DoctrineMigrations\\Version20210802152814','2026-03-07 16:16:04',15),('DoctrineMigrations\\Version20210802160837','2026-03-07 16:16:04',106),('DoctrineMigrations\\Version20210802174318','2026-03-07 16:16:04',60),('DoctrineMigrations\\Version20210802174319','2026-03-07 16:16:04',1),('DoctrineMigrations\\Version20210802174320','2026-03-07 16:16:04',110),('DoctrineMigrations\\Version20211008092010','2026-03-07 16:16:04',39),('DoctrineMigrations\\Version20211230163612','2026-03-07 16:16:04',91),('DoctrineMigrations\\Version20220101204501','2026-03-07 16:16:04',124),('DoctrineMigrations\\Version20220315224645','2026-03-07 16:16:05',175),('DoctrineMigrations\\Version20220404150236','2026-03-07 16:16:05',58),('DoctrineMigrations\\Version20220531145920','2026-03-07 16:16:05',132),('DoctrineMigrations\\Version20220722125847','2026-03-07 16:16:05',68),('DoctrineMigrations\\Version20230126002049','2026-03-07 16:16:05',403),('DoctrineMigrations\\Version20230126002050','2026-03-07 16:16:05',97),('DoctrineMigrations\\Version20230327143628','2026-03-07 16:16:05',173),('DoctrineMigrations\\Version20230606125948','2026-03-07 16:16:06',75),('DoctrineMigrations\\Version20230819090536','2026-03-07 16:16:06',252),('DoctrineMigrations\\Version20231130000719','2026-03-07 16:16:06',1),('DoctrineMigrations\\Version20240214061246','2026-03-07 16:16:06',104),('DoctrineMigrations\\Version20240326125247','2026-03-07 16:16:06',75),('DoctrineMigrations\\Version20240920105524','2026-03-07 16:16:06',1),('DoctrineMigrations\\Version20240926111739','2026-03-07 16:16:06',213),('DoctrineMigrations\\Version20250608143244','2026-03-07 16:16:06',60),('DoctrineMigrations\\Version20251031142000','2026-03-07 16:16:06',212),('DoctrineMigrations\\Version20251031143000','2026-03-07 16:16:07',66),('DoctrineMigrations\\Version20251214160001','2026-03-07 16:16:07',79);
/*!40000 ALTER TABLE `migration_versions` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-10 17:59:29
