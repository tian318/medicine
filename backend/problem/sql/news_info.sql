
DROP TABLE IF EXISTS `news_info1`;
CREATE TABLE `news_info1` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `title` varchar(255) DEFAULT NULL COMMENT '新闻标题',
  `publish_time` datetime DEFAULT NULL COMMENT '发布时间',
  `herb_name` varchar(100) DEFAULT NULL COMMENT '中药材品种',
  `content` text COMMENT '新闻内容',
  `news_type` varchar(50) DEFAULT NULL COMMENT '新闻类型',
  `recorded_at` datetime DEFAULT NULL COMMENT '记录时间',
  `market_name` varchar(100) DEFAULT NULL COMMENT '市场名称',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='中药材新闻资讯表';

