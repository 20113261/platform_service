CREATE TABLE IF NOT EXISTS `%s` (
  `id`          BIGINT(20) AUTO_INCREMENT NOT NULL,
  `source`      VARCHAR(20)               NOT NULL,
  `source_id`   VARCHAR(64)               NOT NULL DEFAULT '',
  `pic_url`     TEXT,
  `pic_md5`     VARCHAR(64)               NOT NULL DEFAULT '',
  `part`        VARCHAR(10)               NOT NULL DEFAULT '',
  `hotel_id`    VARCHAR(20)               NOT NULL,
  `status`      VARCHAR(10)               NOT NULL DEFAULT '-1',
  `update_date` TIMESTAMP(6)              NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `size`        VARCHAR(40)                        DEFAULT '',
  `flag`        VARCHAR(10)                        DEFAULT '1',
  `file_md5`    VARCHAR(32)               NOT NULL DEFAULT '',
  `info`        JSON,
  UNIQUE KEY `s_sid_md5` (`source`, `source_id`, `file_md5`),
  KEY `_ix_id`(`id`),
  KEY `_ix_s_sid`(`source`, `source_id`),
  KEY `_ix_pic_md5` (`pic_md5`),
  KEY `_ix_pic_md5_2` (`pic_md5`, `file_md5`),
  KEY `_ix_flag` (`flag`),
  KEY `_ix_update_date` (`update_date`)
)
  ENGINE = InnoDB
  AUTO_INCREMENT = 121015905
  DEFAULT CHARSET = utf8
  PARTITION BY KEY (`source`, `source_id`)
  PARTITIONS 16;