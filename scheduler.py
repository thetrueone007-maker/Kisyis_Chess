#!/usr/bin/env python3
"""
Scheduler for automated chess video generation
Runs the pipeline automatically at scheduled times
"""

import schedule
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path
from main_pipeline import ChessTikTokPipeline


class VideoScheduler:
    """Automated scheduler for chess video generation"""

    def __init__(self, videos_per_day: int = 10, config: dict = None):
        """
        Initialize scheduler

        Args:
            videos_per_day: Number of videos to generate per day
            config: Pipeline configuration
        """
        self.videos_per_day = videos_per_day
        self.config = config
        self.pipeline = ChessTikTokPipeline(config)

        # Setup logging
        self._setup_logging()

        # Calculate schedule
        self.batch_size = max(1, videos_per_day // 4)  # Spread across 4 runs per day
        self.logger.info(f"Scheduler initialized: {videos_per_day} videos/day")
        self.logger.info(f"Batch size: {self.batch_size} videos per run")

    def _setup_logging(self):
        """Configure logging"""
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger('VideoScheduler')

    def generate_batch_job(self):
        """Job function to generate a batch of videos"""
        self.logger.info("="*70)
        self.logger.info(f"Starting scheduled batch: {self.batch_size} videos")
        self.logger.info("="*70)

        try:
            self.pipeline.generate_batch(
                count=self.batch_size,
                mix_ratio=0.5  # 50/50 mix
            )
            self.logger.info("[OK] Batch completed successfully")

        except Exception as e:
            self.logger.error(f"[ERROR] Batch failed: {e}", exc_info=True)

    def setup_schedule(self):
        """Configure the schedule based on videos_per_day"""
        schedule.clear()

        if self.videos_per_day >= 20:
            # Very aggressive: every 2 hours
            self.logger.info("Schedule: Every 2 hours (20+ videos/day)")
            schedule.every(2).hours.do(self.generate_batch_job)

        elif self.videos_per_day >= 12:
            # Aggressive: 4 times a day
            self.logger.info("Schedule: 4 times per day (12-20 videos/day)")
            schedule.every().day.at("08:00").do(self.generate_batch_job)
            schedule.every().day.at("12:00").do(self.generate_batch_job)
            schedule.every().day.at("16:00").do(self.generate_batch_job)
            schedule.every().day.at("20:00").do(self.generate_batch_job)

        elif self.videos_per_day >= 6:
            # Moderate: 3 times a day
            self.logger.info("Schedule: 3 times per day (6-12 videos/day)")
            schedule.every().day.at("09:00").do(self.generate_batch_job)
            schedule.every().day.at("14:00").do(self.generate_batch_job)
            schedule.every().day.at("19:00").do(self.generate_batch_job)

        else:
            # Light: twice a day
            self.logger.info("Schedule: 2 times per day (2-6 videos/day)")
            schedule.every().day.at("10:00").do(self.generate_batch_job)
            schedule.every().day.at("18:00").do(self.generate_batch_job)

        # Show next run times
        self._show_next_runs()

    def _show_next_runs(self):
        """Display upcoming scheduled runs"""
        jobs = schedule.get_jobs()
        self.logger.info(f"\nScheduled jobs: {len(jobs)}")
        for i, job in enumerate(jobs[:5], 1):
            next_run = schedule.next_run()
            self.logger.info(f"  {i}. Next run: {next_run}")

    def run_once(self):
        """Run a single batch immediately (for testing)"""
        self.logger.info("Running single batch (testing mode)")
        self.generate_batch_job()

    def run_forever(self):
        """Start the scheduler and run forever"""
        self.logger.info("\n" + "="*70)
        self.logger.info("[START] VIDEO SCHEDULER STARTED")
        self.logger.info("="*70)
        self.logger.info(f"Target: {self.videos_per_day} videos per day")
        self.logger.info("Press Ctrl+C to stop\n")

        self.setup_schedule()

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            self.logger.info("\n\n[STOP]  Scheduler stopped by user")
            self.logger.info("="*70)

    def run_daemon(self):
        """Run as a background daemon (for production)"""
        import daemon
        import daemon.pidfile

        pid_file = Path("/tmp/chess_video_scheduler.pid")

        with daemon.DaemonContext(
            pidfile=daemon.pidfile.PIDLockFile(str(pid_file)),
            working_directory=str(Path.cwd()),
            umask=0o002,
        ):
            self.logger.info("Running as daemon...")
            self.run_forever()


def main():
    parser = argparse.ArgumentParser(
        description="Automated Chess Video Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 10 videos per day
  python scheduler.py --videos-per-day 10

  # Run a single batch now (testing)
  python scheduler.py --once

  # Run 20 videos per day as a background daemon
  python scheduler.py --videos-per-day 20 --daemon

  # Custom configuration
  python scheduler.py --config config.json --videos-per-day 15
        """
    )

    parser.add_argument(
        '--videos-per-day',
        type=int,
        default=10,
        help='Number of videos to generate per day (default: 10)'
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='Run a single batch immediately and exit (for testing)'
    )

    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as a background daemon'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration JSON file'
    )

    args = parser.parse_args()

    # Load config
    config = None
    if args.config:
        import json
        with open(args.config) as f:
            config = json.load(f)

    # Create scheduler
    scheduler = VideoScheduler(
        videos_per_day=args.videos_per_day,
        config=config
    )

    # Run based on mode
    if args.once:
        scheduler.run_once()
    elif args.daemon:
        try:
            scheduler.run_daemon()
        except ImportError:
            print("[ERROR] python-daemon not installed")
            print("   Install: pip install python-daemon")
            print("   Or run without --daemon flag")
    else:
        scheduler.run_forever()


if __name__ == "__main__":
    main()
