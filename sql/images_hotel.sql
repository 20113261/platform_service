CREATE TABLE `%s` (
  `id`  BIGINT NOT NULL AUTO_INCREMENT,
  `source` varchar(20) NOT NULL,
  `source_id` varchar(64) NOT NULL DEFAULT '',
  `pic_url` text,
  `pic_md5` varchar(64) NOT NULL DEFAULT '',
  `part` varchar(10) NOT NULL DEFAULT '',
  `hotel_id` varchar(20) NOT NULL,
  `status` varchar(10) NOT NULL DEFAULT '-1',
  `update_date` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `size` varchar(40) DEFAULT '',
  `flag` varchar(10) DEFAULT '1',
  `file_md5` varchar(32) NOT NULL DEFAULT '',
  UNIQUE KEY `s_sid_md5` (`source`,`source_id`,`file_md5`),
  KEY `pic_md5` (`pic_md5`),
  KEY `pic_md5_2` (`pic_md5`,`file_md5`),
  KEY `flag` (`flag`),
  KEY `update_date` (`update_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;