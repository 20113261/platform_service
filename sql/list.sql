CREATE TABLE IF NOT EXISTS `%s` (
 `source` varchar(24) NOT NULL,
 `source_id` varchar(256) NOT NULL,
 `city_id` varchar(16) NOT NULL,
 `country_id` varchar(16) NOT NULL,
 `hotel_url` text NOT NULL,
 `utime` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
 PRIMARY KEY (`source`,`source_id`,`city_id`,`country_id`),
 KEY `city_id` (`city_id`),
 KEY `country_id` (`country_id`),
 KEY `source` (`source`),
 KEY `utime` (`utime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;