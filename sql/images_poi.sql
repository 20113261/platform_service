CREATE TABLE IF NOT EXISTS `%s` (
  `id`  BIGINT NOT NULL AUTO_INCREMENT,
  `file_name` varchar(100) NOT NULL DEFAULT 'NULL',
  `source` varchar(30) NOT NULL DEFAULT 'NULL',
  `sid` varchar(100) NOT NULL DEFAULT 'NULL',
  `url` text,
  `pic_size` varchar(60) NOT NULL DEFAULT 'NULL',
  `bucket_name` varchar(128) NOT NULL DEFAULT '',
  `url_md5` varchar(1024) NOT NULL DEFAULT 'NULL',
  `pic_md5` varchar(64) NOT NULL DEFAULT '',
  `use` varchar(10) NOT NULL DEFAULT 'NULL',
  `part` varchar(32) NOT NULL DEFAULT 'NULL',
  `date` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `s_sid_md5` (`source`, `sid`,`pic_md5`),
  KEY `file_name` (`file_name`),
  KEY `date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;