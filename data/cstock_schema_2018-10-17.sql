-- MySQL dump 10.13  Distrib 5.1.41, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: cstock
-- ------------------------------------------------------
-- Server version	5.1.41-3ubuntu12.10

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alerts_notification`
--

DROP TABLE IF EXISTS `alerts_notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `alerts_notification` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uid` varchar(256) NOT NULL,
  `created_on` datetime NOT NULL,
  `escalated_on` datetime NOT NULL,
  `modified_on` datetime NOT NULL,
  `text` longtext NOT NULL,
  `url` longtext,
  `alert_type` varchar(256) NOT NULL,
  `originating_location_id` int(11) DEFAULT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `is_open` tinyint(1) NOT NULL,
  `escalation_level` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `alerts_notification_9cbea417` (`originating_location_id`),
  KEY `alerts_notification_5d52dd10` (`owner_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `alerts_notificationcomment`
--

DROP TABLE IF EXISTS `alerts_notificationcomment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `alerts_notificationcomment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notification_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `date` datetime NOT NULL,
  `text` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `alerts_notificationcomment_ca24cde3` (`notification_id`),
  KEY `alerts_notificationcomment_fbfc09f1` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `alerts_notificationvisibility`
--

DROP TABLE IF EXISTS `alerts_notificationvisibility`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `alerts_notificationvisibility` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notif_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `esc_level` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `alerts_notificationvisibility_1bdf9063` (`notif_id`),
  KEY `alerts_notificationvisibility_fbfc09f1` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auditcare_fieldaccess`
--

DROP TABLE IF EXISTS `auditcare_fieldaccess`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auditcare_fieldaccess` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auditcare_modelauditevent`
--

DROP TABLE IF EXISTS `auditcare_modelauditevent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auditcare_modelauditevent` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `permission_id_refs_id_a7792de1` (`permission_id`)
) ENGINE=MyISAM AUTO_INCREMENT=60 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_message`
--

DROP TABLE IF EXISTS `auth_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id_refs_id_9af0b65a` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`)
) ENGINE=MyISAM AUTO_INCREMENT=245 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(75) NOT NULL,
  `password` varchar(128) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=MyISAM AUTO_INCREMENT=508 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `group_id_refs_id_f0ee9890` (`group_id`)
) ENGINE=MyISAM AUTO_INCREMENT=770 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `permission_id_refs_id_67e79cb` (`permission_id`)
) ENGINE=MyISAM AUTO_INCREMENT=498 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `celery_taskmeta`
--

DROP TABLE IF EXISTS `celery_taskmeta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `celery_taskmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_id` varchar(255) NOT NULL,
  `status` varchar(50) NOT NULL,
  `result` longtext,
  `date_done` datetime NOT NULL,
  `traceback` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2677 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `celery_tasksetmeta`
--

DROP TABLE IF EXISTS `celery_tasksetmeta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `celery_tasksetmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `taskset_id` varchar(255) NOT NULL,
  `result` longtext NOT NULL,
  `date_done` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `taskset_id` (`taskset_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id_refs_id_c8665aa` (`user_id`),
  KEY `content_type_id_refs_id_288599e6` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=849 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=MyISAM AUTO_INCREMENT=82 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY (`session_key`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_site`
--

DROP TABLE IF EXISTS `django_site`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_site` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djcelery_crontabschedule`
--

DROP TABLE IF EXISTS `djcelery_crontabschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_crontabschedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `minute` varchar(64) NOT NULL,
  `hour` varchar(64) NOT NULL,
  `day_of_week` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djcelery_intervalschedule`
--

DROP TABLE IF EXISTS `djcelery_intervalschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_intervalschedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `every` int(11) NOT NULL,
  `period` varchar(24) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djcelery_periodictask`
--

DROP TABLE IF EXISTS `djcelery_periodictask`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_periodictask` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `task` varchar(200) NOT NULL,
  `interval_id` int(11) DEFAULT NULL,
  `crontab_id` int(11) DEFAULT NULL,
  `args` longtext NOT NULL,
  `kwargs` longtext NOT NULL,
  `queue` varchar(200) DEFAULT NULL,
  `exchange` varchar(200) DEFAULT NULL,
  `routing_key` varchar(200) DEFAULT NULL,
  `expires` datetime DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `last_run_at` datetime DEFAULT NULL,
  `total_run_count` int(10) unsigned NOT NULL,
  `date_changed` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `interval_id_refs_id_f2054349` (`interval_id`),
  KEY `crontab_id_refs_id_ebff5e74` (`crontab_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djcelery_periodictasks`
--

DROP TABLE IF EXISTS `djcelery_periodictasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_periodictasks` (
  `ident` smallint(6) NOT NULL,
  `last_update` datetime NOT NULL,
  PRIMARY KEY (`ident`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djcelery_taskstate`
--

DROP TABLE IF EXISTS `djcelery_taskstate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_taskstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `state` varchar(64) NOT NULL,
  `task_id` varchar(36) NOT NULL,
  `name` varchar(200) DEFAULT NULL,
  `tstamp` datetime NOT NULL,
  `args` longtext,
  `kwargs` longtext,
  `eta` datetime DEFAULT NULL,
  `expires` datetime DEFAULT NULL,
  `result` longtext,
  `traceback` longtext,
  `runtime` double DEFAULT NULL,
  `worker_id` int(11) DEFAULT NULL,
  `hidden` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `worker_id_refs_id_4e3453a` (`worker_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djcelery_workerstate`
--

DROP TABLE IF EXISTS `djcelery_workerstate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_workerstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(255) NOT NULL,
  `last_heartbeat` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `hostname` (`hostname`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djkombu_message`
--

DROP TABLE IF EXISTS `djkombu_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djkombu_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `visible` tinyint(1) NOT NULL,
  `sent_at` datetime DEFAULT NULL,
  `payload` longtext NOT NULL,
  `queue_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `queue_id_refs_id_13f7812d` (`queue_id`)
) ENGINE=MyISAM AUTO_INCREMENT=6931740 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djkombu_queue`
--

DROP TABLE IF EXISTS `djkombu_queue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djkombu_queue` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `email_reports_dailyreportsubscription`
--

DROP TABLE IF EXISTS `email_reports_dailyreportsubscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `email_reports_dailyreportsubscription` (
  `reportsubscription_ptr_id` int(11) NOT NULL,
  `hours` int(11) NOT NULL,
  PRIMARY KEY (`reportsubscription_ptr_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `email_reports_reportsubscription`
--

DROP TABLE IF EXISTS `email_reports_reportsubscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `email_reports_reportsubscription` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `report` varchar(100) NOT NULL,
  `_view_args` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `email_reports_reportsubscription_users`
--

DROP TABLE IF EXISTS `email_reports_reportsubscription_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `email_reports_reportsubscription_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `reportsubscription_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `reportsubscription_id` (`reportsubscription_id`,`user_id`),
  KEY `email_reports_reportsubscription_users_ac755651` (`reportsubscription_id`),
  KEY `email_reports_reportsubscription_users_fbfc09f1` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `email_reports_schedulablereport`
--

DROP TABLE IF EXISTS `email_reports_schedulablereport`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `email_reports_schedulablereport` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `view_name` varchar(100) NOT NULL,
  `display_name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `email_reports_weeklyreportsubscription`
--

DROP TABLE IF EXISTS `email_reports_weeklyreportsubscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `email_reports_weeklyreportsubscription` (
  `reportsubscription_ptr_id` int(11) NOT NULL,
  `hours` int(11) NOT NULL,
  `day_of_week` int(11) NOT NULL,
  PRIMARY KEY (`reportsubscription_ptr_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `locations_location`
--

DROP TABLE IF EXISTS `locations_location`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `locations_location` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `point_id` int(11) DEFAULT NULL,
  `type_id` varchar(50) DEFAULT NULL,
  `parent_type_id` int(11) DEFAULT NULL,
  `parent_id` int(10) unsigned DEFAULT NULL,
  `name` varchar(100) NOT NULL,
  `code` varchar(100) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `point_id_refs_id_1a944377` (`point_id`),
  KEY `type_id_refs_slug_6eefe411` (`type_id`),
  KEY `parent_type_id_refs_id_29aec8a8` (`parent_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=10352 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `locations_locationtype`
--

DROP TABLE IF EXISTS `locations_locationtype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `locations_locationtype` (
  `name` varchar(100) NOT NULL,
  `slug` varchar(50) NOT NULL,
  PRIMARY KEY (`slug`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `locations_point`
--

DROP TABLE IF EXISTS `locations_point`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `locations_point` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `latitude` decimal(13,10) NOT NULL,
  `longitude` decimal(13,10) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_contactrole`
--

DROP TABLE IF EXISTS `logistics_contactrole`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_contactrole` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(30) NOT NULL,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=MyISAM AUTO_INCREMENT=10 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_contactrole_responsibilities`
--

DROP TABLE IF EXISTS `logistics_contactrole_responsibilities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_contactrole_responsibilities` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `contactrole_id` int(11) NOT NULL,
  `responsibility_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `logistics_contactrole_resp_contactrole_id_6153dec0a95b55ae_uniq` (`contactrole_id`,`responsibility_id`),
  KEY `logistics_contactrole_responsibilities_530ed7a9` (`contactrole_id`),
  KEY `logistics_contactrole_responsibilities_60082da4` (`responsibility_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_defaultmonthlyconsumption`
--

DROP TABLE IF EXISTS `logistics_defaultmonthlyconsumption`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_defaultmonthlyconsumption` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_type_id` varchar(50) NOT NULL,
  `product_id` int(11) NOT NULL,
  `default_monthly_consumption` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `supply_point_type_id` (`supply_point_type_id`,`product_id`),
  KEY `logistics_defaultmonthlyconsumption_2951ffb4` (`supply_point_type_id`),
  KEY `logistics_defaultmonthlyconsumption_bb420c12` (`product_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_historicalstockcache`
--

DROP TABLE IF EXISTS `logistics_historicalstockcache`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_historicalstockcache` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `product_id` int(11) DEFAULT NULL,
  `year` int(10) unsigned NOT NULL,
  `month` int(10) unsigned NOT NULL,
  `stock` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `logistics_historicalstockcache_a850ae62` (`supply_point_id`),
  KEY `logistics_historicalstockcache_bb420c12` (`product_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_logisticsprofile`
--

DROP TABLE IF EXISTS `logistics_logisticsprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_logisticsprofile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `location_id` int(11) DEFAULT NULL,
  `supply_point_id` int(11) DEFAULT NULL,
  `designation` varchar(255) DEFAULT NULL,
  `organization_id` int(11),
  `can_view_hsa_level_data` tinyint(1) NOT NULL,
  `can_view_facility_level_data` tinyint(1) NOT NULL,
  `current_dashboard_base_level` varchar(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `logistics_logisticsprofile_319d859` (`location_id`),
  KEY `logistics_logisticsprofile_a850ae62` (`supply_point_id`),
  KEY `logistics_logisticsprofile_97d7cd8d` (`organization_id`)
) ENGINE=MyISAM AUTO_INCREMENT=509 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_nagrecord`
--

DROP TABLE IF EXISTS `logistics_nagrecord`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_nagrecord` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `report_date` datetime NOT NULL DEFAULT '2011-06-11 10:49:19',
  `warning` int(11) NOT NULL DEFAULT '1',
  `nag_type` varchar(30) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `logistics_nagrecord_a850ae62` (`supply_point_id`)
) ENGINE=MyISAM AUTO_INCREMENT=96333 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_product`
--

DROP TABLE IF EXISTS `logistics_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_product` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `units` varchar(100) NOT NULL,
  `sms_code` varchar(10) NOT NULL,
  `description` varchar(255) NOT NULL,
  `product_code` varchar(100) DEFAULT NULL,
  `type_id` int(11) NOT NULL,
  `average_monthly_consumption` int(10) unsigned DEFAULT NULL,
  `emergency_order_level` int(10) unsigned DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sms_code` (`sms_code`),
  KEY `logistics_product_777d41c8` (`type_id`),
  KEY `logistics_product_52094d6e` (`name`),
  KEY `logistics_product_e01be369` (`is_active`)
) ENGINE=MyISAM AUTO_INCREMENT=38 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_product_equivalents`
--

DROP TABLE IF EXISTS `logistics_product_equivalents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_product_equivalents` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `from_product_id` int(11) NOT NULL,
  `to_product_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `logistics_product_equival_from_product_id_5a8200c32d338909_uniq` (`from_product_id`,`to_product_id`),
  KEY `logistics_product_equivalents_c884f964` (`from_product_id`),
  KEY `logistics_product_equivalents_5bd7a0dd` (`to_product_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_productreport`
--

DROP TABLE IF EXISTS `logistics_productreport`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_productreport` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product_id` int(11) NOT NULL,
  `report_type_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  `report_date` datetime NOT NULL DEFAULT '2011-06-11 12:49:17',
  `message_id` int(11) DEFAULT NULL,
  `supply_point_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `logistics_productreport_bb420c12` (`product_id`),
  KEY `logistics_productreport_3d4f9c7e` (`report_type_id`),
  KEY `logistics_productreport_38373776` (`message_id`),
  KEY `logistics_productreport_a850ae62` (`supply_point_id`),
  KEY `logistics_productreport_145b7fb9` (`report_date`)
) ENGINE=MyISAM AUTO_INCREMENT=3253113 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_productreporttype`
--

DROP TABLE IF EXISTS `logistics_productreporttype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_productreporttype` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `code` varchar(10) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_productstock`
--

DROP TABLE IF EXISTS `logistics_productstock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_productstock` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `quantity` int(11) DEFAULT NULL,
  `product_id` int(11) NOT NULL,
  `days_stocked_out` int(11) NOT NULL DEFAULT '0',
  `last_modified` datetime NOT NULL,
  `manual_monthly_consumption` int(10) unsigned DEFAULT NULL,
  `auto_monthly_consumption` int(10) unsigned DEFAULT NULL,
  `use_auto_consumption` tinyint(1) NOT NULL,
  `supply_point_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `logistics_productstock_supply_point_id_28d4fe708c2bc571_uniq` (`supply_point_id`,`product_id`),
  KEY `logistics_productstock_bb420c12` (`product_id`),
  KEY `logistics_productstock_a850ae62` (`supply_point_id`),
  KEY `logistics_productstock_e01be369` (`is_active`),
  KEY `logistics_productstock_2eba1ab0` (`quantity`),
  KEY `logistics_productstock_41b436a5` (`days_stocked_out`)
) ENGINE=MyISAM AUTO_INCREMENT=107941 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_producttype`
--

DROP TABLE IF EXISTS `logistics_producttype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_producttype` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `code` varchar(10) NOT NULL,
  `base_level` varchar(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_requisitionreport`
--

DROP TABLE IF EXISTS `logistics_requisitionreport`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_requisitionreport` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `submitted` tinyint(1) NOT NULL DEFAULT '0',
  `report_date` datetime NOT NULL DEFAULT '2011-06-11 12:49:17',
  `message_id` int(11) NOT NULL,
  `supply_point_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `logistics_requisitionreport_38373776` (`message_id`),
  KEY `logistics_requisitionreport_a850ae62` (`supply_point_id`),
  KEY `logistics_requisitionreport_145b7fb9` (`report_date`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_responsibility`
--

DROP TABLE IF EXISTS `logistics_responsibility`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_responsibility` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(30) NOT NULL,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_stockrequest`
--

DROP TABLE IF EXISTS `logistics_stockrequest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_stockrequest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product_id` int(11) NOT NULL,
  `supply_point_id` int(11) NOT NULL,
  `status` varchar(20) NOT NULL,
  `response_status` varchar(20) NOT NULL,
  `is_emergency` tinyint(1) NOT NULL DEFAULT '0',
  `requested_on` datetime NOT NULL,
  `responded_on` datetime DEFAULT NULL,
  `received_on` datetime DEFAULT NULL,
  `requested_by_id` int(11) DEFAULT NULL,
  `responded_by_id` int(11) DEFAULT NULL,
  `received_by_id` int(11) DEFAULT NULL,
  `amount_requested` int(10) unsigned DEFAULT NULL,
  `amount_approved` int(10) unsigned DEFAULT NULL,
  `amount_received` int(10) unsigned DEFAULT NULL,
  `canceled_for_id` int(11) DEFAULT NULL,
  `balance` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `logistics_stockrequest_bb420c12` (`product_id`),
  KEY `logistics_stockrequest_a850ae62` (`supply_point_id`),
  KEY `logistics_stockrequest_87861524` (`requested_by_id`),
  KEY `logistics_stockrequest_3e2d4be0` (`responded_by_id`),
  KEY `logistics_stockrequest_b5d7e504` (`received_by_id`),
  KEY `logistics_stockrequest_8167cb09` (`canceled_for_id`),
  KEY `logistics_stockrequest_f95b0817` (`requested_on`),
  KEY `logistics_stockrequest_2f2e6ab3` (`responded_on`),
  KEY `logistics_stockrequest_d5f494f7` (`received_on`)
) ENGINE=MyISAM AUTO_INCREMENT=1737560 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_stocktransaction`
--

DROP TABLE IF EXISTS `logistics_stocktransaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_stocktransaction` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  `beginning_balance` int(11) NOT NULL,
  `ending_balance` int(11) NOT NULL,
  `date` datetime NOT NULL DEFAULT '2011-06-11 12:49:17',
  `product_report_id` int(11) DEFAULT NULL,
  `supply_point_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `logistics_stocktransaction_bb420c12` (`product_id`),
  KEY `logistics_stocktransaction_85b4b958` (`product_report_id`),
  KEY `logistics_stocktransaction_a850ae62` (`supply_point_id`),
  KEY `logistics_stocktransaction_2eba1ab0` (`quantity`)
) ENGINE=MyISAM AUTO_INCREMENT=3166504 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_stocktransfer`
--

DROP TABLE IF EXISTS `logistics_stocktransfer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_stocktransfer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `giver_id` int(11) DEFAULT NULL,
  `giver_unknown` varchar(200) NOT NULL,
  `receiver_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `amount` int(10) unsigned DEFAULT NULL,
  `status` varchar(10) NOT NULL,
  `initiated_on` datetime DEFAULT NULL,
  `closed_on` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `logistics_stocktransfer_81588a32` (`giver_id`),
  KEY `logistics_stocktransfer_6828e8a9` (`receiver_id`),
  KEY `logistics_stocktransfer_bb420c12` (`product_id`)
) ENGINE=MyISAM AUTO_INCREMENT=19279 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_supplypoint`
--

DROP TABLE IF EXISTS `logistics_supplypoint`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_supplypoint` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  `type_id` varchar(50) NOT NULL,
  `created_at` datetime NOT NULL,
  `code` varchar(100) NOT NULL,
  `last_reported` datetime DEFAULT NULL,
  `location_id` int(11) NOT NULL,
  `supplied_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `logistics_supplypoint_777d41c8` (`type_id`),
  KEY `logistics_supplypoint_319d859` (`location_id`),
  KEY `logistics_supplypoint_88d7ba0d` (`supplied_by_id`),
  KEY `logistics_supplypoint_34d728db` (`active`)
) ENGINE=MyISAM AUTO_INCREMENT=10352 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_supplypoint_groups`
--

DROP TABLE IF EXISTS `logistics_supplypoint_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_supplypoint_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supplypoint_id` int(11) NOT NULL,
  `supplypointgroup_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `logistics_supplypoint_groups_8b4ad83e` (`supplypoint_id`),
  KEY `logistics_supplypoint_groups_c093d6aa` (`supplypointgroup_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_supplypointgroup`
--

DROP TABLE IF EXISTS `logistics_supplypointgroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_supplypointgroup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(30) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_supplypointtype`
--

DROP TABLE IF EXISTS `logistics_supplypointtype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_supplypointtype` (
  `name` varchar(100) NOT NULL,
  `code` varchar(50) NOT NULL,
  PRIMARY KEY (`code`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logistics_supplypointwarehouserecord`
--

DROP TABLE IF EXISTS `logistics_supplypointwarehouserecord`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logistics_supplypointwarehouserecord` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `create_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `logistics_supplypointwarehouserecord_a850ae62` (`supply_point_id`)
) ENGINE=MyISAM AUTO_INCREMENT=10347 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_alert`
--

DROP TABLE IF EXISTS `malawi_alert`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_alert` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `num_hsas` int(10) unsigned NOT NULL DEFAULT '0',
  `have_stockouts` int(10) unsigned NOT NULL DEFAULT '0',
  `eo_with_resupply` int(10) unsigned NOT NULL DEFAULT '0',
  `eo_without_resupply` int(10) unsigned NOT NULL DEFAULT '0',
  `total_requests` int(10) unsigned NOT NULL DEFAULT '0',
  `reporting_receipts` int(10) unsigned NOT NULL DEFAULT '0',
  `without_products_managed` int(10) unsigned NOT NULL DEFAULT '0',
  `eo_total` int(10) unsigned NOT NULL,
  `order_readys` int(10) unsigned NOT NULL,
  `products_requested` int(10) unsigned NOT NULL,
  `products_approved` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `malawi_alert_a850ae62` (`supply_point_id`)
) ENGINE=MyISAM AUTO_INCREMENT=10071 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_calculatedconsumption`
--

DROP TABLE IF EXISTS `malawi_calculatedconsumption`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_calculatedconsumption` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `create_date` datetime NOT NULL,
  `update_date` datetime NOT NULL,
  `product_id` int(11) NOT NULL,
  `calculated_consumption` int(10) unsigned NOT NULL DEFAULT '0',
  `time_stocked_out` bigint(20) NOT NULL DEFAULT '0',
  `time_with_data` bigint(20) NOT NULL,
  `time_needing_data` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `malawi_consumption_a850ae62` (`supply_point_id`),
  KEY `malawi_consumption_bb420c12` (`product_id`)
) ENGINE=MyISAM AUTO_INCREMENT=13467317 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_currentconsumption`
--

DROP TABLE IF EXISTS `malawi_currentconsumption`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_currentconsumption` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `create_date` datetime NOT NULL,
  `update_date` datetime NOT NULL,
  `product_id` int(11) NOT NULL,
  `total` int(10) unsigned NOT NULL DEFAULT '0',
  `current_daily_consumption` double NOT NULL DEFAULT '0',
  `stock_on_hand` bigint(20) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `malawi_currentconsumption_a850ae62` (`supply_point_id`),
  KEY `malawi_currentconsumption_bb420c12` (`product_id`)
) ENGINE=MyISAM AUTO_INCREMENT=208410 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_historicalstock`
--

DROP TABLE IF EXISTS `malawi_historicalstock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_historicalstock` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `create_date` datetime NOT NULL,
  `update_date` datetime NOT NULL,
  `date` datetime NOT NULL,
  `product_id` int(11) NOT NULL,
  `stock` bigint(20) NOT NULL DEFAULT '0',
  `total` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `malawi_historicalstock_a850ae62` (`supply_point_id`),
  KEY `malawi_historicalstock_bb420c12` (`product_id`)
) ENGINE=MyISAM AUTO_INCREMENT=13466031 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_orderfulfillment`
--

DROP TABLE IF EXISTS `malawi_orderfulfillment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_orderfulfillment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `create_date` datetime NOT NULL,
  `update_date` datetime NOT NULL,
  `product_id` int(11) NOT NULL,
  `total` int(10) unsigned NOT NULL DEFAULT '0',
  `quantity_requested` int(10) unsigned NOT NULL DEFAULT '0',
  `quantity_received` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `malawi_orderfulfillment_a850ae62` (`supply_point_id`),
  KEY `malawi_orderfulfillment_bb420c12` (`product_id`)
) ENGINE=MyISAM AUTO_INCREMENT=13256447 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_orderrequest`
--

DROP TABLE IF EXISTS `malawi_orderrequest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_orderrequest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `create_date` datetime NOT NULL,
  `update_date` datetime NOT NULL,
  `product_id` int(11) NOT NULL,
  `total` int(10) unsigned NOT NULL DEFAULT '0',
  `emergency` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `malawi_orderrequest_a850ae62` (`supply_point_id`),
  KEY `malawi_orderrequest_bb420c12` (`product_id`)
) ENGINE=MyISAM AUTO_INCREMENT=13256447 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_organization`
--

DROP TABLE IF EXISTS `malawi_organization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_organization` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=17 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_organization_managed_supply_points`
--

DROP TABLE IF EXISTS `malawi_organization_managed_supply_points`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_organization_managed_supply_points` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `organization_id` int(11) NOT NULL,
  `supplypoint_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `malawi_organization_manag_organization_id_21eabdf926961c3b_uniq` (`organization_id`,`supplypoint_id`),
  KEY `malawi_organization_managed_supply_points_97d7cd8d` (`organization_id`),
  KEY `malawi_organization_managed_supply_points_8b4ad83e` (`supplypoint_id`)
) ENGINE=MyISAM AUTO_INCREMENT=83 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_productavailabilitydata`
--

DROP TABLE IF EXISTS `malawi_productavailabilitydata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_productavailabilitydata` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `create_date` datetime NOT NULL,
  `update_date` datetime NOT NULL,
  `product_id` int(11) NOT NULL,
  `total` int(10) unsigned NOT NULL DEFAULT '0',
  `managed` int(10) unsigned NOT NULL DEFAULT '0',
  `with_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `under_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `good_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `over_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `without_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `without_data` int(10) unsigned NOT NULL DEFAULT '0',
  `managed_and_with_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `managed_and_under_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `managed_and_good_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `managed_and_over_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `managed_and_without_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `managed_and_without_data` int(10) unsigned NOT NULL DEFAULT '0',
  `emergency_stock` int(10) unsigned NOT NULL,
  `managed_and_emergency_stock` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `malawi_productavailabilitydata_a850ae62` (`supply_point_id`),
  KEY `malawi_productavailabilitydata_bb420c12` (`product_id`)
) ENGINE=MyISAM AUTO_INCREMENT=13466031 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_productavailabilitydatasummary`
--

DROP TABLE IF EXISTS `malawi_productavailabilitydatasummary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_productavailabilitydatasummary` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `create_date` datetime NOT NULL,
  `update_date` datetime NOT NULL,
  `total` int(10) unsigned NOT NULL DEFAULT '0',
  `any_managed` int(10) unsigned NOT NULL DEFAULT '0',
  `any_without_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `any_with_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `any_under_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `any_over_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `any_good_stock` int(10) unsigned NOT NULL DEFAULT '0',
  `any_without_data` int(10) unsigned NOT NULL DEFAULT '0',
  `any_emergency_stock` int(10) unsigned NOT NULL,
  `base_level` varchar(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `malawi_productavailabilitydatasummary_a850ae62` (`supply_point_id`)
) ENGINE=MyISAM AUTO_INCREMENT=624954 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_refrigeratormalfunction`
--

DROP TABLE IF EXISTS `malawi_refrigeratormalfunction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_refrigeratormalfunction` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `reported_on` datetime NOT NULL,
  `malfunction_reason` varchar(1) NOT NULL,
  `responded_on` datetime DEFAULT NULL,
  `sent_to_id` int(11) DEFAULT NULL,
  `resolved_on` datetime DEFAULT NULL,
  `reported_by_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `malawi_refrigeratormalfunction_a850ae62` (`supply_point_id`),
  KEY `malawi_refrigeratormalfunction_e9ba6c99` (`reported_on`),
  KEY `malawi_refrigeratormalfunction_6f8dbefd` (`sent_to_id`),
  KEY `malawi_refrigeratormalfunction_7fa05aac` (`reported_by_id`)
) ENGINE=MyISAM AUTO_INCREMENT=116 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_reportingrate`
--

DROP TABLE IF EXISTS `malawi_reportingrate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_reportingrate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `create_date` datetime NOT NULL,
  `update_date` datetime NOT NULL,
  `total` int(10) unsigned NOT NULL DEFAULT '0',
  `reported` int(10) unsigned NOT NULL DEFAULT '0',
  `on_time` int(10) unsigned NOT NULL DEFAULT '0',
  `complete` int(10) unsigned NOT NULL DEFAULT '0',
  `base_level` varchar(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `malawi_reportingrate_a850ae62` (`supply_point_id`)
) ENGINE=MyISAM AUTO_INCREMENT=624954 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `malawi_timetracker`
--

DROP TABLE IF EXISTS `malawi_timetracker`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `malawi_timetracker` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `create_date` datetime NOT NULL,
  `update_date` datetime NOT NULL,
  `type` varchar(10) NOT NULL,
  `total` int(10) unsigned NOT NULL DEFAULT '0',
  `time_in_seconds` bigint(20) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `malawi_timetracker_a850ae62` (`supply_point_id`)
) ENGINE=MyISAM AUTO_INCREMENT=584215 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `messagelog_message`
--

DROP TABLE IF EXISTS `messagelog_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `messagelog_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `contact_id` int(11) DEFAULT NULL,
  `connection_id` int(11) DEFAULT NULL,
  `direction` varchar(1) NOT NULL,
  `date` datetime NOT NULL,
  `text` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=3532576 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `outreach_outreachmessage`
--

DROP TABLE IF EXISTS `outreach_outreachmessage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `outreach_outreachmessage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `sent_by_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `outreach_outreachmessage_992c08ed` (`sent_by_id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `outreach_outreachquota`
--

DROP TABLE IF EXISTS `outreach_outreachquota`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `outreach_outreachquota` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `amount` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rapidsms_app`
--

DROP TABLE IF EXISTS `rapidsms_app`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rapidsms_app` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `module` varchar(100) NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `module` (`module`)
) ENGINE=MyISAM AUTO_INCREMENT=45 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rapidsms_backend`
--

DROP TABLE IF EXISTS `rapidsms_backend`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rapidsms_backend` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rapidsms_connection`
--

DROP TABLE IF EXISTS `rapidsms_connection`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rapidsms_connection` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `backend_id` int(11) NOT NULL,
  `identity` varchar(100) NOT NULL,
  `contact_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `rapidsms_connection_backend_id_7afca29d244ebb6f_uniq` (`backend_id`,`identity`),
  KEY `rapidsms_connection_32d72771` (`backend_id`),
  KEY `rapidsms_connection_170b8823` (`contact_id`)
) ENGINE=MyISAM AUTO_INCREMENT=41102 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rapidsms_contact`
--

DROP TABLE IF EXISTS `rapidsms_contact`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rapidsms_contact` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `language` varchar(6) NOT NULL,
  `role_id` int(11) DEFAULT NULL,
  `needs_reminders` tinyint(1) NOT NULL DEFAULT '1',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `supply_point_id` int(11) DEFAULT NULL,
  `is_approved` tinyint(1) NOT NULL,
  `organization_id` int(11),
  PRIMARY KEY (`id`),
  KEY `rapidsms_contact_bf07f040` (`role_id`),
  KEY `rapidsms_contact_a850ae62` (`supply_point_id`),
  KEY `rapidsms_contact_97d7cd8d` (`organization_id`)
) ENGINE=MyISAM AUTO_INCREMENT=9979 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rapidsms_contact_commodities`
--

DROP TABLE IF EXISTS `rapidsms_contact_commodities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rapidsms_contact_commodities` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `contact_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `rapidsms_contact_commodities_contact_id_57dfb8dc4436cb1f_uniq` (`contact_id`,`product_id`),
  KEY `rapidsms_contact_commodities_170b8823` (`contact_id`),
  KEY `rapidsms_contact_commodities_bb420c12` (`product_id`)
) ENGINE=MyISAM AUTO_INCREMENT=119737 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rapidsms_deliveryreport`
--

DROP TABLE IF EXISTS `rapidsms_deliveryreport`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rapidsms_deliveryreport` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action` varchar(255) NOT NULL,
  `report_id` varchar(255) NOT NULL,
  `number` varchar(255) NOT NULL,
  `report` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `registration_registrationprofile`
--

DROP TABLE IF EXISTS `registration_registrationprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `registration_registrationprofile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `activation_key` varchar(40) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reports_dailyreportsubscription`
--

DROP TABLE IF EXISTS `reports_dailyreportsubscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reports_dailyreportsubscription` (
  `reportsubscription_ptr_id` int(11) NOT NULL,
  `hours` int(11) NOT NULL,
  PRIMARY KEY (`reportsubscription_ptr_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reports_reportsubscription`
--

DROP TABLE IF EXISTS `reports_reportsubscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reports_reportsubscription` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `report` varchar(100) NOT NULL,
  `_view_args` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reports_reportsubscription_users`
--

DROP TABLE IF EXISTS `reports_reportsubscription_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reports_reportsubscription_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `reportsubscription_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `reportsubscription_id` (`reportsubscription_id`,`user_id`),
  KEY `user_id_refs_id_f6f6b544` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reports_weeklyreportsubscription`
--

DROP TABLE IF EXISTS `reports_weeklyreportsubscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reports_weeklyreportsubscription` (
  `reportsubscription_ptr_id` int(11) NOT NULL,
  `hours` int(11) NOT NULL,
  `day_of_week` int(11) NOT NULL,
  PRIMARY KEY (`reportsubscription_ptr_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `scheduler_eventschedule`
--

DROP TABLE IF EXISTS `scheduler_eventschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `scheduler_eventschedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `callback` varchar(255) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `callback_args` longtext,
  `callback_kwargs` longtext,
  `months` longtext,
  `days_of_month` longtext,
  `days_of_week` longtext,
  `hours` longtext,
  `minutes` longtext,
  `start_time` datetime DEFAULT NULL,
  `end_time` datetime DEFAULT NULL,
  `last_ran` datetime DEFAULT NULL,
  `count` int(11) DEFAULT NULL,
  `active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `scheduler_executionrecord`
--

DROP TABLE IF EXISTS `scheduler_executionrecord`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `scheduler_executionrecord` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `schedule_id` int(11) NOT NULL,
  `runtime` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `scheduler_executionrecord_10d3e039` (`schedule_id`)
) ENGINE=MyISAM AUTO_INCREMENT=4779 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `scheduler_failedexecutionrecord`
--

DROP TABLE IF EXISTS `scheduler_failedexecutionrecord`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `scheduler_failedexecutionrecord` (
  `executionrecord_ptr_id` int(11) NOT NULL,
  `message` longtext NOT NULL,
  PRIMARY KEY (`executionrecord_ptr_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `south_migrationhistory`
--

DROP TABLE IF EXISTS `south_migrationhistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `south_migrationhistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_name` varchar(255) NOT NULL,
  `migration` varchar(255) NOT NULL,
  `applied` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=56 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `taggit_tag`
--

DROP TABLE IF EXISTS `taggit_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taggit_tag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `slug` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slug` (`slug`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `taggit_taggeditem`
--

DROP TABLE IF EXISTS `taggit_taggeditem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taggit_taggeditem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tag_id` int(11) NOT NULL,
  `object_id` int(11) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `taggit_taggeditem_3747b463` (`tag_id`),
  KEY `taggit_taggeditem_829e37fd` (`object_id`),
  KEY `taggit_taggeditem_e4470c6e` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=464764 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tanzania_adhocreport`
--

DROP TABLE IF EXISTS `tanzania_adhocreport`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tanzania_adhocreport` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `recipients` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tanzania_adhocreport_a850ae62` (`supply_point_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tanzania_deliverygroupreport`
--

DROP TABLE IF EXISTS `tanzania_deliverygroupreport`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tanzania_deliverygroupreport` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  `report_date` datetime NOT NULL DEFAULT '2015-03-11 00:00:00',
  `message_id` int(11) NOT NULL,
  `delivery_group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tanzania_deliverygroupreport_a850ae62` (`supply_point_id`),
  KEY `tanzania_deliverygroupreport_38373776` (`message_id`),
  KEY `tanzania_deliverygroupreport_9c2b681e` (`delivery_group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tanzania_supplypointnote`
--

DROP TABLE IF EXISTS `tanzania_supplypointnote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tanzania_supplypointnote` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supply_point_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `text` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tanzania_supplypointnote_a850ae62` (`supply_point_id`),
  KEY `tanzania_supplypointnote_fbfc09f1` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tanzania_supplypointstatus`
--

DROP TABLE IF EXISTS `tanzania_supplypointstatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tanzania_supplypointstatus` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `status_type` varchar(50) NOT NULL,
  `status_value` varchar(50) NOT NULL,
  `status_date` datetime NOT NULL DEFAULT '2015-03-11 18:22:18',
  `supply_point_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tanzania_supplypointstatus_a850ae62` (`supply_point_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `warehouse_reportrun`
--

DROP TABLE IF EXISTS `warehouse_reportrun`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `warehouse_reportrun` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `start` datetime NOT NULL,
  `end` datetime NOT NULL,
  `start_run` datetime NOT NULL,
  `end_run` datetime DEFAULT NULL,
  `complete` tinyint(1) NOT NULL,
  `has_error` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=4121 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2018-10-17  9:38:54
