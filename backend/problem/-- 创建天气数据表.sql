-- Active: 1741936584685@@127.0.0.1@5432@postgres
-- 创建天气数据表
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    location VARCHAR(100) NOT NULL,       -- 地点名称
    latitude DECIMAL(9, 6) NOT NULL,      -- 纬度
    longitude DECIMAL(9, 6) NOT NULL,     -- 经度
    date DATE NOT NULL,                   -- 日期
    temperature DECIMAL(5, 2),            -- 平均温度(°C)
    temperature_min DECIMAL(5, 2),        -- 最低温度(°C)
    temperature_max DECIMAL(5, 2),        -- 最高温度(°C)
    precipitation DECIMAL(6, 2),          -- 降水量(mm)
    humidity DECIMAL(5, 2),               -- 相对湿度(%)
    wind_speed DECIMAL(5, 2),             -- 风速(km/h)
    sunshine_duration DECIMAL(5, 2),      -- 日照时长(小时)
    recorded_at TIMESTAMPTZ NOT NULL,     -- 数据记录时间
    UNIQUE(location, date)
);

-- 创建索引
CREATE INDEX ON weather_data (location, date);
CREATE INDEX ON weather_data (date);


-- 创建地理位置映射表
CREATE TABLE IF NOT EXISTS location_mapping (
    id SERIAL PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL UNIQUE,  -- 地点名称
    latitude DECIMAL(9, 6) NOT NULL,             -- 纬度
    longitude DECIMAL(9, 6) NOT NULL,            -- 经度
    province VARCHAR(50),                        -- 省份
    city VARCHAR(50),                            -- 城市
    is_market BOOLEAN DEFAULT FALSE,             -- 是否为市场
    created_at TIMESTAMPTZ DEFAULT NOW()         -- 创建时间
);

-- 插入一些常见的中药材市场和产地
INSERT INTO location_mapping (location_name, latitude, longitude, province, city, is_market)
VALUES 
    ('亳州', 33.8447, 115.7787, '安徽省', '亳州市', TRUE),
    ('安国', 38.4185, 115.3266, '河北省', '保定市', TRUE),
    ('成都', 30.5728, 104.0668, '四川省', '成都市', TRUE),
    ('玉林', 22.6292, 110.1496, '广西壮族自治区', '玉林市', TRUE),
    ('广州', 23.1291, 113.2644, '广东省', '广州市', TRUE),
    ('昆明', 25.0389, 102.7183, '云南省', '昆明市', TRUE),
    ('重庆', 29.5647, 106.5501, '重庆市', '重庆市', TRUE),
    ('西安', 34.3416, 108.9398, '陕西省', '西安市', TRUE),
    ('武汉', 30.5928, 114.3055, '湖北省', '武汉市', TRUE),
    ('四川', 30.6510, 104.0760, '四川省', NULL, FALSE),
    ('云南', 25.0453, 102.7097, '云南省', NULL, FALSE),
    ('广西', 22.8152, 108.3669, '广西壮族自治区', NULL, FALSE),
    ('陕西', 34.2652, 108.9541, '陕西省', NULL, FALSE),
    ('甘肃', 36.0611, 103.8343, '甘肃省', NULL, FALSE),
    ('河北', 38.0428, 114.5149, '河北省', NULL, FALSE)
ON CONFLICT (location_name) DO NOTHING;



ALTER TABLE weather_data
    ALTER COLUMN temperature TYPE NUMERIC(7,2),
    ALTER COLUMN temperature_min TYPE NUMERIC(7,2),
    ALTER COLUMN temperature_max TYPE NUMERIC(7,2),
    ALTER COLUMN precipitation TYPE NUMERIC(7,2),
    ALTER COLUMN humidity TYPE NUMERIC(7,2),
    ALTER COLUMN wind_speed TYPE NUMERIC(7,2),
    ALTER COLUMN sunshine_duration TYPE NUMERIC(7,2);