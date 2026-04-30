-- 创建价格来源枚举类型
CREATE TYPE price_source AS ENUM ('origin', 'market');

-- 创建中药材价格表
CREATE TABLE IF NOT EXISTS herb_prices (
    id SERIAL,
    herb_name VARCHAR(100) NOT NULL,      -- 名称
    specification VARCHAR(100),            -- 规格
    location VARCHAR(100),                -- 市场/产地
    price DECIMAL(10, 2) NOT NULL,        -- 近期价格
    trend VARCHAR(20),                    -- 走势
    week_change VARCHAR(20),              -- 周涨跌
    month_change VARCHAR(20),             -- 月涨跌
    year_change VARCHAR(20),              -- 年涨跌
    source price_source NOT NULL,         -- 数据来源
    recorded_at TIMESTAMPTZ NOT NULL,      -- 记录时间
    PRIMARY KEY (id, recorded_at)
);

-- 将表转换为超表(hypertable)
SELECT create_hypertable('herb_prices', 'recorded_at');

-- 创建索引
CREATE INDEX ON herb_prices (herb_name, recorded_at DESC);
CREATE INDEX ON herb_prices (source, recorded_at DESC);
CREATE INDEX ON herb_prices (location, recorded_at DESC);