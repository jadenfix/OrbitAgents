"""
Crawler Scheduler
Cron-based scheduler for automated MLS data crawling every 4 hours.
"""

import asyncio
from datetime import datetime, timezone
from croniter import croniter
import signal
import sys

import structlog

from config import settings
from mls_crawler import mls_crawler

logger = structlog.get_logger(__name__)


class CrawlerScheduler:
    """
    Cron-based scheduler for automated crawl jobs.
    Runs crawl jobs on a configurable schedule (default: every 4 hours).
    """
    
    def __init__(self):
        self.running = False
        self.current_task = None
        self.cron = croniter(settings.crawler_cron, datetime.now(timezone.utc))
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Received shutdown signal", signal=signum)
        self.stop()
    
    async def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        logger.info(
            "Starting crawler scheduler",
            cron_expression=settings.crawler_cron,
            next_run=self.cron.get_next(datetime).isoformat()
        )
        
        try:
            await self._run_scheduler_loop()
        except Exception as e:
            logger.error("Scheduler error", error=str(e))
            raise
        finally:
            self.running = False
            logger.info("Scheduler stopped")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            logger.info("Cancelled current crawl task")
    
    async def _run_scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                # Calculate time until next scheduled run
                now = datetime.now(timezone.utc)
                next_run = self.cron.get_next(datetime)
                sleep_duration = (next_run - now).total_seconds()
                
                logger.info(
                    "Waiting for next scheduled run",
                    next_run=next_run.isoformat(),
                    sleep_seconds=sleep_duration
                )
                
                # Wait until next scheduled time
                if sleep_duration > 0:
                    await asyncio.sleep(sleep_duration)
                
                if not self.running:
                    break
                
                # Execute crawl job
                await self._execute_scheduled_crawl()
                
            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                logger.error("Error in scheduler loop", error=str(e))
                # Wait a bit before retrying to avoid tight loops
                await asyncio.sleep(60)
    
    async def _execute_scheduled_crawl(self):
        """Execute a scheduled crawl job."""
        logger.info("Starting scheduled crawl job")
        
        try:
            # Create crawl task
            self.current_task = asyncio.create_task(
                mls_crawler.run_crawl_job()
            )
            
            # Wait for completion
            job_status = await self.current_task
            
            logger.info(
                "Scheduled crawl job completed",
                job_id=job_status.job_id,
                status=job_status.status,
                fetched=job_status.total_fetched,
                processed=job_status.total_processed,
                saved=job_status.total_saved,
                indexed=job_status.total_indexed,
                errors=job_status.total_errors
            )
            
            # Update next run time
            self.cron.get_next()
            
        except asyncio.CancelledError:
            logger.info("Scheduled crawl job was cancelled")
            raise
        except Exception as e:
            logger.error("Scheduled crawl job failed", error=str(e))
            # Don't raise - let scheduler continue
        finally:
            self.current_task = None
    
    def get_next_run_time(self) -> datetime:
        """Get the next scheduled run time."""
        # Create a copy to avoid modifying the main cron iterator
        temp_cron = croniter(settings.crawler_cron, datetime.now(timezone.utc))
        return temp_cron.get_next(datetime)
    
    def get_schedule_info(self) -> dict:
        """Get information about the current schedule."""
        next_run = self.get_next_run_time()
        now = datetime.now(timezone.utc)
        time_until_next = (next_run - now).total_seconds()
        
        return {
            'cron_expression': settings.crawler_cron,
            'next_run': next_run.isoformat(),
            'time_until_next_seconds': time_until_next,
            'running': self.running,
            'current_task_active': self.current_task is not None and not self.current_task.done()
        }


async def run_scheduler():
    """Run the crawler scheduler as a standalone process."""
    logger.info("Starting Orbit MLS Crawler Scheduler")
    
    # Configure structured logging for standalone mode
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    if not settings.enable_scheduler:
        logger.info("Scheduler is disabled in configuration")
        return
    
    scheduler = CrawlerScheduler()
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        scheduler.stop()
    except Exception as e:
        logger.error("Scheduler failed", error=str(e))
        raise
    finally:
        # Clean up resources
        await mls_crawler.close()
        logger.info("Scheduler shutdown complete")


if __name__ == "__main__":
    asyncio.run(run_scheduler()) 