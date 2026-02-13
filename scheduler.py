#!/usr/bin/env python3
"""
Scheduler for automated chess video generation
Runs the pipeline automatically at scheduled times
Supports individual content-type aware uploads (puzzle vs game)
"""

import schedule
import time
import random
import argparse
import logging
from datetime import datetime
from pathlib import Path
from main_pipeline import ChessTikTokPipeline


class VideoScheduler:
    """Automated scheduler for chess video generation"""

    # Default schedule: 5 posts/day at peak TikTok engagement times
    DEFAULT_SCHEDULE = [
        {"time": "07:00", "type": "puzzle"},   # Morning scroll
        {"time": "10:30", "type": "game"},      # Mid-morning break
        {"time": "13:00", "type": "auto"},      # Lunch break (peak)
        {"time": "17:00", "type": "game"},      # After work/school (peak)
        {"time": "20:30", "type": "puzzle"},    # Evening prime time
    ]

    def __init__(self, videos_per_day: int = 5, config: dict = None,
                 schedule_times: list = None, jitter_minutes: int = 15):
        """
        Initialize scheduler

        Args:
            videos_per_day: Number of videos to generate per day
            config: Pipeline configuration
            schedule_times: Custom schedule (list of dicts with 'time' and 'type')
            jitter_minutes: Random jitter ± minutes for anti-detection
        """
        self.videos_per_day = videos_per_day
        self.config = config or {}
        self.jitter_minutes = jitter_minutes
        self.schedule_times = schedule_times or self.DEFAULT_SCHEDULE

        # Ensure auto-upload is enabled
        if self.config:
            self.config['enable_auto_upload'] = True
        else:
            self.config = {'enable_auto_upload': True}

        self.pipeline = ChessTikTokPipeline(self.config)

        # Setup logging
        self._setup_logging()

        self.logger.info(f"Scheduler initialized: {videos_per_day} videos/day")
        self.logger.info(f"Schedule: {len(self.schedule_times)} time slots")
        self.logger.info(f"Jitter: +/- {jitter_minutes} minutes")

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

    def generate_single_job(self, content_type="auto"):
        """
        Generate and upload a single video.

        Args:
            content_type: 'game', 'puzzle', or 'auto'
        """
        # Add random jitter
        jitter_sec = random.randint(0, self.jitter_minutes * 60)
        if jitter_sec > 0:
            self.logger.info(f"[WAIT] Jitter delay: {jitter_sec // 60}m {jitter_sec % 60}s")
            time.sleep(jitter_sec)

        self.logger.info("=" * 70)
        self.logger.info(f"[START] Generating single {content_type} content")
        self.logger.info("=" * 70)

        try:
            video_path = self.pipeline.generate_single_content(content_type=content_type)

            if video_path:
                self.logger.info(f"[OK] Content generated: {video_path}")
            else:
                self.logger.warning("[WARN] Content generation failed")

        except Exception as e:
            self.logger.error(f"[ERROR] Job failed: {e}", exc_info=True)

    def generate_batch_job(self):
        """Job function to generate a batch of videos (legacy mode)"""
        self.logger.info("=" * 70)
        self.logger.info(f"Starting scheduled batch: {self.batch_size} videos")
        self.logger.info("=" * 70)

        try:
            self.pipeline.generate_batch(
                count=self.batch_size,
                mix_ratio=0.5
            )
            self.logger.info("[OK] Batch completed successfully")

        except Exception as e:
            self.logger.error(f"[ERROR] Batch failed: {e}", exc_info=True)

    def setup_schedule(self):
        """Configure the schedule based on videos_per_day"""
        schedule.clear()

        if self.videos_per_day <= 5 and len(self.schedule_times) >= self.videos_per_day:
            # Individual content-type aware scheduling (preferred for 5/day)
            self.logger.info(f"Schedule: {self.videos_per_day} individual posts/day")
            for slot in self.schedule_times[:self.videos_per_day]:
                t = slot['time']
                ct = slot.get('type', 'auto')
                schedule.every().day.at(t).do(self.generate_single_job, content_type=ct)
                self.logger.info(f"  - {t} -> {ct}")

        elif self.videos_per_day >= 20:
            self.batch_size = max(1, self.videos_per_day // 12)
            self.logger.info(f"Schedule: Every 2 hours, batch={self.batch_size}")
            schedule.every(2).hours.do(self.generate_batch_job)

        elif self.videos_per_day >= 12:
            self.batch_size = max(1, self.videos_per_day // 4)
            self.logger.info(f"Schedule: 4x/day, batch={self.batch_size}")
            schedule.every().day.at("08:00").do(self.generate_batch_job)
            schedule.every().day.at("12:00").do(self.generate_batch_job)
            schedule.every().day.at("16:00").do(self.generate_batch_job)
            schedule.every().day.at("20:00").do(self.generate_batch_job)

        elif self.videos_per_day >= 6:
            self.batch_size = max(1, self.videos_per_day // 3)
            self.logger.info(f"Schedule: 3x/day, batch={self.batch_size}")
            schedule.every().day.at("09:00").do(self.generate_batch_job)
            schedule.every().day.at("14:00").do(self.generate_batch_job)
            schedule.every().day.at("19:00").do(self.generate_batch_job)

        else:
            # 2-5 videos: use individual scheduling
            self.logger.info(f"Schedule: {self.videos_per_day} individual posts/day")
            for slot in self.schedule_times[:self.videos_per_day]:
                t = slot['time']
                ct = slot.get('type', 'auto')
                schedule.every().day.at(t).do(self.generate_single_job, content_type=ct)
                self.logger.info(f"  - {t} -> {ct}")

        self._show_next_runs()

    def _show_next_runs(self):
        """Display upcoming scheduled runs"""
        jobs = schedule.get_jobs()
        self.logger.info(f"\nScheduled jobs: {len(jobs)}")
        next_time = schedule.next_run()
        if next_time:
            self.logger.info(f"  Next run: {next_time}")

    def run_once(self, content_type="auto"):
        """Run a single content generation immediately (for testing)"""
        self.logger.info(f"Running single {content_type} (testing mode)")
        self.generate_single_job(content_type=content_type)

    def run_forever(self):
        """Start the scheduler and run forever"""
        self.logger.info("\n" + "=" * 70)
        self.logger.info("[START] VIDEO SCHEDULER STARTED")
        self.logger.info("=" * 70)
        self.logger.info(f"Target: {self.videos_per_day} videos per day")
        self.logger.info("Press Ctrl+C to stop\n")

        self.setup_schedule()

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)

        except KeyboardInterrupt:
            self.logger.info("\n\n[STOP] Scheduler stopped by user")
            self.logger.info("=" * 70)
            # Clean up TikTok uploader
            if hasattr(self.pipeline, '_tiktok_uploader'):
                try:
                    self.pipeline._tiktok_uploader.close()
                except:
                    pass

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
  # Default: 5 videos per day (2 puzzles, 3 GM games)
  python scheduler.py

  # Run a single video now (testing)
  python scheduler.py --once

  # Run a single puzzle video now
  python scheduler.py --once --type puzzle

  # Custom number of videos per day
  python scheduler.py --videos-per-day 8

  # Custom configuration
  python scheduler.py --config config.json
        """
    )

    parser.add_argument(
        '--videos-per-day',
        type=int,
        default=5,
        help='Number of videos to generate per day (default: 5)'
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='Run a single content generation immediately and exit'
    )

    parser.add_argument(
        '--type',
        type=str,
        choices=['game', 'puzzle', 'auto'],
        default='auto',
        help='Content type for --once mode (default: auto)'
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

    parser.add_argument(
        '--jitter',
        type=int,
        default=15,
        help='Random jitter in minutes for anti-detection (default: 15)'
    )

    args = parser.parse_args()

    # Load config
    config = None
    if args.config:
        import json
        with open(args.config) as f:
            config = json.load(f)

    scheduler = VideoScheduler(
        videos_per_day=args.videos_per_day,
        config=config,
        jitter_minutes=args.jitter
    )

    if args.once:
        scheduler.run_once(content_type=args.type)
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
