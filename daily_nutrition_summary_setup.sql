-- Daily Nutrition Summary Table
-- This table stores aggregated nutrition data for each user per day
-- Similar to user_nutrition_summary but with historical daily records

CREATE TABLE IF NOT EXISTS daily_nutrition_summary (
    id SERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL,
    date DATE NOT NULL,
    total_calories DECIMAL(10,2) DEFAULT 0,
    total_protein_g DECIMAL(10,2) DEFAULT 0,
    total_carbs_g DECIMAL(10,2) DEFAULT 0,
    total_fat_g DECIMAL(10,2) DEFAULT 0,
    meals_logged_count INTEGER DEFAULT 0,
    -- User targets for reference (stored per day in case they change)
    calorie_target DECIMAL(10,2),
    protein_target_g DECIMAL(10,2),
    carbs_target_g DECIMAL(10,2),
    fat_target_g DECIMAL(10,2),
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Unique constraint to prevent duplicate entries per user per day
    UNIQUE(user_telegram_id, date)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_daily_nutrition_user_date ON daily_nutrition_summary(user_telegram_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_nutrition_date ON daily_nutrition_summary(date DESC);

-- Function to upsert daily nutrition summary
CREATE OR REPLACE FUNCTION update_daily_nutrition_summary(
    p_user_telegram_id BIGINT,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS void AS $$
DECLARE
    user_targets RECORD;
    daily_totals RECORD;
BEGIN
    -- Get user targets
    SELECT calorie_target, protein_target_g, fat_target_g, carbs_target_g
    INTO user_targets
    FROM users
    WHERE user_id = p_user_telegram_id;

    -- Calculate daily totals from nutrition_logs
    SELECT
        COALESCE(SUM(total_calories), 0) as total_calories,
        COALESCE(SUM(protein_g), 0) as total_protein_g,
        COALESCE(SUM(carbs_g), 0) as total_carbs_g,
        COALESCE(SUM(fat_g), 0) as total_fat_g,
        COUNT(*) as meals_count
    INTO daily_totals
    FROM nutrition_logs
    WHERE user_telegram_id = p_user_telegram_id
    AND DATE(logged_at AT TIME ZONE 'UTC') = p_date;

    -- Upsert daily summary
    INSERT INTO daily_nutrition_summary (
        user_telegram_id,
        date,
        total_calories,
        total_protein_g,
        total_carbs_g,
        total_fat_g,
        meals_logged_count,
        calorie_target,
        protein_target_g,
        carbs_target_g,
        fat_target_g,
        updated_at
    )
    VALUES (
        p_user_telegram_id,
        p_date,
        daily_totals.total_calories,
        daily_totals.total_protein_g,
        daily_totals.total_carbs_g,
        daily_totals.total_fat_g,
        daily_totals.meals_count,
        user_targets.calorie_target,
        user_targets.protein_target_g,
        user_targets.carbs_target_g,
        user_targets.fat_target_g,
        NOW()
    )
    ON CONFLICT (user_telegram_id, date)
    DO UPDATE SET
        total_calories = EXCLUDED.total_calories,
        total_protein_g = EXCLUDED.total_protein_g,
        total_carbs_g = EXCLUDED.total_carbs_g,
        total_fat_g = EXCLUDED.total_fat_g,
        meals_logged_count = EXCLUDED.meals_logged_count,
        calorie_target = EXCLUDED.calorie_target,
        protein_target_g = EXCLUDED.protein_target_g,
        carbs_target_g = EXCLUDED.carbs_target_g,
        fat_target_g = EXCLUDED.fat_target_g,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update daily summary when nutrition_logs are inserted/updated
CREATE OR REPLACE FUNCTION trigger_update_daily_nutrition_summary()
RETURNS TRIGGER AS $$
BEGIN
    -- Update for the date of the new/updated nutrition log
    PERFORM update_daily_nutrition_summary(
        COALESCE(NEW.user_telegram_id, OLD.user_telegram_id),
        DATE(COALESCE(NEW.logged_at, OLD.logged_at) AT TIME ZONE 'UTC')
    );

    -- If the date changed in an update, also update the old date
    IF TG_OP = 'UPDATE' AND DATE(OLD.logged_at AT TIME ZONE 'UTC') != DATE(NEW.logged_at AT TIME ZONE 'UTC') THEN
        PERFORM update_daily_nutrition_summary(
            OLD.user_telegram_id,
            DATE(OLD.logged_at AT TIME ZONE 'UTC')
        );
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS nutrition_logs_daily_summary_trigger ON nutrition_logs;
CREATE TRIGGER nutrition_logs_daily_summary_trigger
    AFTER INSERT OR UPDATE OR DELETE ON nutrition_logs
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_daily_nutrition_summary();

-- Function to backfill historical daily summaries
CREATE OR REPLACE FUNCTION backfill_daily_nutrition_summaries(
    p_user_telegram_id BIGINT DEFAULT NULL,
    p_days_back INTEGER DEFAULT 30
)
RETURNS void AS $$
DECLARE
    user_id_to_process BIGINT;
    day_offset INTEGER;
    target_date DATE;
BEGIN
    -- If specific user provided, process only that user
    -- Otherwise process all users
    FOR user_id_to_process IN
        SELECT CASE
            WHEN p_user_telegram_id IS NOT NULL THEN p_user_telegram_id
            ELSE user_id
        END as user_id
        FROM users
        WHERE p_user_telegram_id IS NULL OR user_id = p_user_telegram_id
    LOOP
        -- Process each day going back p_days_back days
        FOR day_offset IN 0..p_days_back-1 LOOP
            target_date := CURRENT_DATE - day_offset;
            PERFORM update_daily_nutrition_summary(user_id_to_process, target_date);
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create a view for easy querying of recent daily summaries
CREATE OR REPLACE VIEW recent_daily_nutrition_summary AS
SELECT
    dns.*,
    u.username,
    -- Calculate percentages of targets achieved
    CASE WHEN dns.calorie_target > 0 THEN ROUND((dns.total_calories / dns.calorie_target) * 100, 1) ELSE 0 END as calories_percentage,
    CASE WHEN dns.protein_target_g > 0 THEN ROUND((dns.total_protein_g / dns.protein_target_g) * 100, 1) ELSE 0 END as protein_percentage,
    CASE WHEN dns.carbs_target_g > 0 THEN ROUND((dns.total_carbs_g / dns.carbs_target_g) * 100, 1) ELSE 0 END as carbs_percentage,
    CASE WHEN dns.fat_target_g > 0 THEN ROUND((dns.total_fat_g / dns.fat_target_g) * 100, 1) ELSE 0 END as fat_percentage
FROM daily_nutrition_summary dns
LEFT JOIN users u ON dns.user_telegram_id = u.user_id
WHERE dns.date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY dns.user_telegram_id, dns.date DESC;