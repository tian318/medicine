CREATE TABLE IF NOT EXISTS news_info (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    publish_time TIMESTAMP,
    herb_name VARCHAR(100),
    content TEXT,
    news_type VARCHAR(20) DEFAULT 'origin',  -- 新增列：标记资讯类型，origin为产地资讯，market为市场资讯
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE news_info 
ADD COLUMN IF NOT EXISTS market_name VARCHAR(100);