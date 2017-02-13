CREATE TABLE `hotel_id_total_test` (
  `hotel_id` varchar(128) NOT NULL DEFAULT '',
  `city` varchar(128) NOT NULL DEFAULT '',
  `country` varchar(64) NOT NULL DEFAULT '',
  `finished_key` varchar(32) NOT NULL DEFAULT '',
  PRIMARY KEY (`hotel_id`,`country`,`city`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `hotelinfo_1010` (
  `hotel_name` varchar(512) NOT NULL DEFAULT 'NULL',
  `hotel_name_en` varchar(512) NOT NULL DEFAULT 'NULL',
  `source` varchar(64) NOT NULL DEFAULT 'NULL',
  `source_id` varchar(128) NOT NULL DEFAULT '',
  `brand_name` varchar(512) NOT NULL DEFAULT 'NULL',
  `map_info` varchar(512) NOT NULL DEFAULT 'NULL',
  `address` varchar(512) NOT NULL DEFAULT 'NULL',
  `city` varchar(512) NOT NULL DEFAULT 'NULL',
  `country` varchar(512) NOT NULL DEFAULT 'NULL',
  `city_id` varchar(11) NOT NULL DEFAULT 'NULL',
  `postal_code` varchar(512) NOT NULL DEFAULT 'NULL',
  `star` varchar(20) NOT NULL DEFAULT 'NULL',
  `grade` varchar(256) NOT NULL DEFAULT 'NULL',
  `review_num` varchar(20) NOT NULL DEFAULT 'NULL',
  `has_wifi` varchar(20) NOT NULL DEFAULT 'NULL',
  `is_wifi_free` varchar(20) NOT NULL DEFAULT 'NULL',
  `has_parking` varchar(20) NOT NULL DEFAULT 'NULL',
  `is_parking_free` varchar(20) NOT NULL DEFAULT 'NULL',
  `service` text,
  `img_items` text,
  `description` text,
  `accepted_cards` varchar(512) NOT NULL DEFAULT 'NULL',
  `check_in_time` varchar(128) NOT NULL DEFAULT 'NULL',
  `check_out_time` varchar(128) NOT NULL DEFAULT 'NULL',
  `hotel_url` varchar(1024) DEFAULT NULL,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `continent` varchar(20) NOT NULL DEFAULT 'NULL',
  PRIMARY KEY (`source`,`source_id`,`city_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

