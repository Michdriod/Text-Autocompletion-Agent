-- ============================================
-- Quick Setup: PostgreSQL Tables for Testing
-- ============================================
-- Just copy and paste this entire file into your PostgreSQL client (psql, pgAdmin, etc.)

-- Create the incidents table
CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'low',
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_to VARCHAR(100)
);

-- Insert sample incident data
INSERT INTO incidents (title, description, severity, status) VALUES
('Database connection timeout', 'Users are experiencing intermittent timeouts when connecting to the main database. The issue started around 3 PM EST and is affecting approximately 15% of users. Initial investigation suggests potential network congestion between web servers and database cluster.', 'high', 'open'),
('Login button not responding', 'Multiple users report that the login button on the mobile app becomes unresponsive after entering credentials. The issue appears to be specific to iOS devices running version 15.x. Temporary workaround: close and reopen the app.', 'medium', 'in_progress'),
('Dashboard loading slowly', 'The analytics dashboard is taking 30+ seconds to load. This is significantly slower than the usual 2-3 second load time. Issue is reproducible across all browsers. May be related to recent addition of real-time data widgets.', 'low', 'open'),
('Payment processing errors', 'Several customers reported failed payment transactions this morning. Error code 502 appearing at checkout. Payment gateway logs show timeout responses. Issue may be on payment processor side. Escalated to vendor.', 'critical', 'in_progress'),
('Mobile app crashes on startup', 'Android users on version 13 experiencing immediate crash on app launch. Crash logs indicate memory allocation error in splash screen module. Rollback to previous version deployed as emergency fix.', 'high', 'resolved');

-- Create read-only user
CREATE USER readonly_user WITH PASSWORD 'changeme123';

-- Grant permissions
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON incidents TO readonly_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO readonly_user;

-- Verify setup
SELECT 'Setup complete! You now have ' || COUNT(*) || ' sample incidents.' FROM incidents;

-- Display sample data
SELECT id, title, LEFT(description, 50) || '...' as description_preview FROM incidents;
