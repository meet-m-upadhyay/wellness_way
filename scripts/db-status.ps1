# Quick database status and table overview
Write-Host "🔍 WellnessWay Database Status" -ForegroundColor Green

# Check if container is running
$containerStatus = docker ps --filter "name=wellnessway-db" --format "table {{.Names}}\t{{.Status}}"
Write-Host "`n📦 Container Status:"
Write-Host $containerStatus

# Connect and show basic info
Write-Host "`n📊 Database Overview:"
docker exec wellnessway-db psql -U wellnessway -d wellnessway_db -c "
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
"

Write-Host "`n📈 Table Row Counts:"
docker exec wellnessway-db psql -U wellnessway -d wellnessway_db -c "
SELECT 
    'users' as table_name, 
    COUNT(*) as row_count 
FROM users
UNION ALL
SELECT 
    'health_context_documents' as table_name, 
    COUNT(*) as row_count 
FROM health_context_documents
UNION ALL
SELECT 
    'diet_plans' as table_name, 
    COUNT(*) as row_count 
FROM diet_plans;
"

Write-Host "`n🔗 Connection Info:"
Write-Host "Host: localhost"
Write-Host "Port: 5432"
Write-Host "Database: wellnessway_db"
Write-Host "Username: wellnessway"
Write-Host "Password: password"