"""
AI Usage Monitoring and Cost Tracking Service

This service tracks OpenAI API usage, costs, and performance metrics
for monitoring and optimization purposes.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from uuid import UUID, uuid4
import json
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


@dataclass
class AIUsageMetrics:
    """Data class for AI usage metrics"""
    request_id: str
    user_id: Optional[UUID]
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    response_time_ms: int
    request_type: str  # 'weekly_plan', 'daily_plan', 'regenerate_meal', etc.
    success: bool
    error_message: Optional[str]
    timestamp: datetime


class AIMonitoringService:
    """Service for monitoring AI usage and costs"""
    
    # OpenAI pricing (as of 2024 - update as needed)
    MODEL_PRICING = {
        "gpt-4": {
            "input": 0.03,   # per 1K tokens
            "output": 0.06   # per 1K tokens
        },
        "gpt-4-turbo": {
            "input": 0.01,
            "output": 0.03
        },
        "gpt-3.5-turbo": {
            "input": 0.0015,
            "output": 0.002
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
        self._ensure_monitoring_table()
    
    def _ensure_monitoring_table(self):
        """Create AI monitoring table if it doesn't exist"""
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS ai_usage_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                request_id VARCHAR(255) NOT NULL,
                user_id UUID,
                model VARCHAR(50) NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                cost_usd DECIMAL(10, 6) NOT NULL,
                response_time_ms INTEGER NOT NULL,
                request_type VARCHAR(50) NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS ix_ai_usage_logs_timestamp ON ai_usage_logs(timestamp);
            CREATE INDEX IF NOT EXISTS ix_ai_usage_logs_user_id ON ai_usage_logs(user_id);
            CREATE INDEX IF NOT EXISTS ix_ai_usage_logs_request_type ON ai_usage_logs(request_type);
            CREATE INDEX IF NOT EXISTS ix_ai_usage_logs_success ON ai_usage_logs(success);
            """
            
            self.db.execute(text(create_table_sql))
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to create AI monitoring table: {e}")
            self.db.rollback()
    
    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for AI request based on token usage"""
        if model not in self.MODEL_PRICING:
            logger.warning(f"Unknown model {model}, using gpt-4 pricing")
            model = "gpt-4"
        
        pricing = self.MODEL_PRICING[model]
        
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]
        
        return round(input_cost + output_cost, 6)
    
    def log_ai_request(self, metrics: AIUsageMetrics) -> None:
        """Log AI request metrics to database"""
        try:
            insert_sql = """
            INSERT INTO ai_usage_logs (
                request_id, user_id, model, prompt_tokens, completion_tokens,
                total_tokens, cost_usd, response_time_ms, request_type,
                success, error_message, timestamp
            ) VALUES (
                :request_id, :user_id, :model, :prompt_tokens, :completion_tokens,
                :total_tokens, :cost_usd, :response_time_ms, :request_type,
                :success, :error_message, :timestamp
            )
            """
            
            self.db.execute(text(insert_sql), {
                "request_id": metrics.request_id,
                "user_id": str(metrics.user_id) if metrics.user_id else None,
                "model": metrics.model,
                "prompt_tokens": metrics.prompt_tokens,
                "completion_tokens": metrics.completion_tokens,
                "total_tokens": metrics.total_tokens,
                "cost_usd": metrics.cost_usd,
                "response_time_ms": metrics.response_time_ms,
                "request_type": metrics.request_type,
                "success": metrics.success,
                "error_message": metrics.error_message,
                "timestamp": metrics.timestamp
            })
            
            self.db.commit()
            
            logger.info(f"Logged AI request {metrics.request_id}: "
                       f"{metrics.total_tokens} tokens, ${metrics.cost_usd:.4f}")
            
        except Exception as e:
            logger.error(f"Failed to log AI request metrics: {e}")
            self.db.rollback()
    
    def get_usage_summary(self, 
                         user_id: Optional[UUID] = None,
                         days: int = 30) -> Dict[str, Any]:
        """Get AI usage summary for the specified period"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            base_query = """
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_requests,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost,
                AVG(response_time_ms) as avg_response_time,
                request_type,
                model
            FROM ai_usage_logs 
            WHERE timestamp >= :start_date
            """
            
            params = {"start_date": start_date}
            
            if user_id:
                base_query += " AND user_id = :user_id"
                params["user_id"] = str(user_id)
            
            # Overall summary
            overall_query = base_query + " GROUP BY request_type, model ORDER BY total_cost DESC"
            results = self.db.execute(text(overall_query), params).fetchall()
            
            # Total summary
            total_query = base_query.replace("request_type, model", "").replace("GROUP BY request_type, model", "")
            total_result = self.db.execute(text(total_query), params).fetchone()
            
            # Daily breakdown
            daily_query = """
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as requests,
                SUM(total_tokens) as tokens,
                SUM(cost_usd) as cost
            FROM ai_usage_logs 
            WHERE timestamp >= :start_date
            """
            
            if user_id:
                daily_query += " AND user_id = :user_id"
            
            daily_query += " GROUP BY DATE(timestamp) ORDER BY date DESC"
            daily_results = self.db.execute(text(daily_query), params).fetchall()
            
            return {
                "period_days": days,
                "user_id": str(user_id) if user_id else "all_users",
                "total_summary": {
                    "total_requests": total_result[0] if total_result else 0,
                    "successful_requests": total_result[1] if total_result else 0,
                    "success_rate": (total_result[1] / total_result[0] * 100) if total_result and total_result[0] > 0 else 0,
                    "total_tokens": total_result[2] if total_result else 0,
                    "total_cost_usd": float(total_result[3]) if total_result else 0.0,
                    "avg_response_time_ms": float(total_result[4]) if total_result else 0.0
                },
                "by_request_type": [
                    {
                        "request_type": row[5],
                        "model": row[6],
                        "requests": row[0],
                        "successful_requests": row[1],
                        "success_rate": (row[1] / row[0] * 100) if row[0] > 0 else 0,
                        "total_tokens": row[2],
                        "total_cost_usd": float(row[3]),
                        "avg_response_time_ms": float(row[4])
                    }
                    for row in results
                ],
                "daily_breakdown": [
                    {
                        "date": str(row[0]),
                        "requests": row[1],
                        "tokens": row[2],
                        "cost_usd": float(row[3])
                    }
                    for row in daily_results
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage summary: {e}")
            return {
                "error": str(e),
                "period_days": days,
                "user_id": str(user_id) if user_id else "all_users"
            }
    
    def get_cost_alerts(self, 
                       daily_limit: float = 10.0,
                       monthly_limit: float = 100.0) -> List[Dict[str, Any]]:
        """Check for cost alerts based on usage limits"""
        alerts = []
        
        try:
            # Check daily usage
            today = datetime.utcnow().date()
            daily_query = """
            SELECT SUM(cost_usd) as daily_cost
            FROM ai_usage_logs 
            WHERE DATE(timestamp) = :today
            """
            
            daily_result = self.db.execute(text(daily_query), {"today": today}).fetchone()
            daily_cost = float(daily_result[0]) if daily_result and daily_result[0] else 0.0
            
            if daily_cost > daily_limit:
                alerts.append({
                    "type": "daily_limit_exceeded",
                    "message": f"Daily cost limit exceeded: ${daily_cost:.2f} > ${daily_limit:.2f}",
                    "current_cost": daily_cost,
                    "limit": daily_limit,
                    "severity": "high"
                })
            elif daily_cost > daily_limit * 0.8:
                alerts.append({
                    "type": "daily_limit_warning",
                    "message": f"Daily cost approaching limit: ${daily_cost:.2f} (80% of ${daily_limit:.2f})",
                    "current_cost": daily_cost,
                    "limit": daily_limit,
                    "severity": "medium"
                })
            
            # Check monthly usage
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_query = """
            SELECT SUM(cost_usd) as monthly_cost
            FROM ai_usage_logs 
            WHERE timestamp >= :month_start
            """
            
            monthly_result = self.db.execute(text(monthly_query), {"month_start": month_start}).fetchone()
            monthly_cost = float(monthly_result[0]) if monthly_result and monthly_result[0] else 0.0
            
            if monthly_cost > monthly_limit:
                alerts.append({
                    "type": "monthly_limit_exceeded",
                    "message": f"Monthly cost limit exceeded: ${monthly_cost:.2f} > ${monthly_limit:.2f}",
                    "current_cost": monthly_cost,
                    "limit": monthly_limit,
                    "severity": "high"
                })
            elif monthly_cost > monthly_limit * 0.8:
                alerts.append({
                    "type": "monthly_limit_warning",
                    "message": f"Monthly cost approaching limit: ${monthly_cost:.2f} (80% of ${monthly_limit:.2f})",
                    "current_cost": monthly_cost,
                    "limit": monthly_limit,
                    "severity": "medium"
                })
            
        except Exception as e:
            logger.error(f"Failed to check cost alerts: {e}")
            alerts.append({
                "type": "monitoring_error",
                "message": f"Failed to check cost limits: {str(e)}",
                "severity": "low"
            })
        
        return alerts
    
    def get_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get AI performance metrics for the specified period"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = """
            SELECT 
                request_type,
                COUNT(*) as total_requests,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_requests,
                AVG(response_time_ms) as avg_response_time,
                MIN(response_time_ms) as min_response_time,
                MAX(response_time_ms) as max_response_time,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms) as median_response_time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time
            FROM ai_usage_logs 
            WHERE timestamp >= :start_date
            GROUP BY request_type
            ORDER BY total_requests DESC
            """
            
            results = self.db.execute(text(query), {"start_date": start_date}).fetchall()
            
            return {
                "period_days": days,
                "performance_by_type": [
                    {
                        "request_type": row[0],
                        "total_requests": row[1],
                        "successful_requests": row[2],
                        "success_rate": (row[2] / row[1] * 100) if row[1] > 0 else 0,
                        "avg_response_time_ms": float(row[3]) if row[3] else 0,
                        "min_response_time_ms": row[4] if row[4] else 0,
                        "max_response_time_ms": row[5] if row[5] else 0,
                        "median_response_time_ms": float(row[6]) if row[6] else 0,
                        "p95_response_time_ms": float(row[7]) if row[7] else 0
                    }
                    for row in results
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e), "period_days": days}


# Global monitoring service instance
_monitoring_service_instance = None

def get_monitoring_service(db: Session) -> AIMonitoringService:
    """Get or create AI monitoring service instance"""
    return AIMonitoringService(db)