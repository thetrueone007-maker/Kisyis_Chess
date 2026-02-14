#!/usr/bin/env python3
"""
TikTok video manager and uploader
Prepares videos and metadata for TikTok posting
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import subprocess

# Import ffmpeg path finder
try:
    from ffmpeg_path import FFMPEG_PATH
except ImportError:
    FFMPEG_PATH = FFMPEG_PATH


class TikTokVideoPrep:
    """Prepare videos for TikTok upload"""

    # TikTok video specifications
    SPECS = {
        'max_duration': 180,  # 3 minutes (TikTok allows up to 10min, but shorter is better)
        'recommended_duration': 60,  # 1 minute is ideal for engagement
        'min_duration': 3,
        'aspect_ratio': '9:16',  # Vertical
        'resolution': {
            'width': 1080,   # TikTok recommended
            'height': 1920
        },
        'fps': [30, 60],  # Supported FPS
        'video_codec': 'h264',
        'audio_codec': 'aac',
        'max_file_size': 287 * 1024 * 1024,  # 287 MB
    }

    def __init__(self, output_dir: Path = None):
        self.output_dir = Path(output_dir) if output_dir else Path("./tiktok_ready")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.output_dir / "upload_queue.json"
        self.upload_queue = self._load_queue()

    def _load_queue(self) -> List[Dict]:
        """Load upload queue from disk"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return []

    def _save_queue(self):
        """Save upload queue to disk"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.upload_queue, f, indent=2)

    def optimize_for_tiktok(self, input_video: Path, output_name: str = None) -> Path:
        """
        Optimize video for TikTok specifications

        Args:
            input_video: Source video file
            output_name: Output filename (auto-generated if None)

        Returns:
            Path to optimized video
        """
        if output_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"tiktok_{timestamp}.mp4"

        output_path = self.output_dir / output_name

        # Get video duration for fade effect
        duration_cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(input_video)
        ]

        try:
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration = float(duration_result.stdout.strip())
            fade_start = max(0, duration - 0.6)  # Start fade 0.6s before end
        except:
            fade_start = 0
            duration = 0

        # Build video filter with fade to black at the end
        video_filter = (
            f'scale={self.SPECS["resolution"]["width"]}:{self.SPECS["resolution"]["height"]}:'
            f'force_original_aspect_ratio=decrease,'
            f'pad={self.SPECS["resolution"]["width"]}:{self.SPECS["resolution"]["height"]}:'
            f'(ow-iw)/2:(oh-ih)/2,'
            f'fade=t=out:st={fade_start:.2f}:d=0.6:color=black'
        )

        # FFmpeg command to optimize for TikTok
        cmd = [
            FFMPEG_PATH, '-y',
            '-i', str(input_video),
            # Video settings
            '-c:v', 'libx264',
            '-profile:v', 'high',
            '-level', '4.2',
            '-pix_fmt', 'yuv420p',
            '-vf', video_filter,
            '-r', '60',  # 60 FPS for smooth playback
            '-crf', '18',  # High quality
            '-preset', 'slow',
            '-movflags', '+faststart',
            # Audio settings
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '48000',
            '-ac', '2',
            str(output_path)
        ]

        try:
            print(f"Optimizing for TikTok: {input_video.name}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"[ERROR] Optimization failed: {result.stderr}")
                return None

            file_size = output_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)

            print(f"[OK] Optimized: {output_path.name} ({file_size_mb:.1f} MB)")

            if file_size > self.SPECS['max_file_size']:
                print(f"[WARN]  Warning: File size ({file_size_mb:.1f} MB) exceeds TikTok limit (287 MB)")

            return output_path

        except Exception as e:
            print(f"[ERROR] Error optimizing video: {e}")
            return None

    def add_to_upload_queue(self, video_path: Path, title: str,
                           hashtags: List[str], description: str = ""):
        """
        Add video to upload queue with metadata

        Args:
            video_path: Path to optimized video
            title: Video title
            hashtags: List of hashtags
            description: Video description
        """
        metadata = {
            'video_path': str(video_path),
            'title': title,
            'description': description,
            'hashtags': hashtags,
            'created_at': datetime.now().isoformat(),
            'uploaded': False,
            'upload_time': None
        }

        self.upload_queue.append(metadata)
        self._save_queue()

        print(f"[OK] Added to upload queue: {title}")
        print(f"   Hashtags: {' '.join(hashtags[:5])}")

    def get_next_to_upload(self) -> Optional[Dict]:
        """Get next video in queue that hasn't been uploaded"""
        for item in self.upload_queue:
            if not item['uploaded']:
                return item
        return None

    def mark_as_uploaded(self, video_path: str):
        """Mark a video as uploaded"""
        for item in self.upload_queue:
            if item['video_path'] == video_path:
                item['uploaded'] = True
                item['upload_time'] = datetime.now().isoformat()
                break
        self._save_queue()

    def generate_caption(self, title: str, description: str, hashtags: List[str]) -> str:
        """Generate TikTok caption from metadata"""
        caption_parts = []

        if title:
            caption_parts.append(title)

        if description:
            caption_parts.append(description)

        # Add hashtags (TikTok allows up to 100 characters in search hashtags)
        if hashtags:
            caption_parts.append(' '.join(hashtags[:10]))  # Limit to 10 hashtags

        caption = '\n\n'.join(caption_parts)

        # TikTok caption limit is 2200 characters
        if len(caption) > 2200:
            caption = caption[:2197] + "..."

        return caption

    def show_upload_instructions(self):
        """Display manual upload instructions"""
        next_video = self.get_next_to_upload()

        if not next_video:
            print("[OK] Upload queue is empty!")
            return

        caption = self.generate_caption(
            next_video['title'],
            next_video['description'],
            next_video['hashtags']
        )

        print("\n" + "="*70)
        print("TIKTOK UPLOAD INSTRUCTIONS")
        print("="*70)
        print(f"\n Video: {next_video['video_path']}")
        print(f"\n[NOTE] Caption (copy this):")
        print("-"*70)
        print(caption)
        print("-"*70)
        print("\n Upload Steps:")
        print("  1. Open TikTok app or web (https://www.tiktok.com/upload)")
        print(f"  2. Select video: {next_video['video_path']}")
        print("  3. Paste the caption above")
        print("  4. Add cover image (optional)")
        print("  5. Post!")
        print("\n[IDEA] After uploading, run:")
        print(f"     manager.mark_as_uploaded('{next_video['video_path']}')")
        print("="*70 + "\n")

    def export_for_automation(self, output_file: Path = None):
        """
        Export upload queue in format suitable for automation tools

        Can be used with tools like:
        - TikTok-Uploader (unofficial)
        - Browser automation (Selenium/Playwright)
        """
        if output_file is None:
            output_file = self.output_dir / "automation_queue.json"

        automation_data = []
        for item in self.upload_queue:
            if not item['uploaded']:
                automation_data.append({
                    'video': item['video_path'],
                    'description': self.generate_caption(
                        item['title'],
                        item['description'],
                        item['hashtags']
                    ),
                    'hashtags': item['hashtags'][:10]
                })

        with open(output_file, 'w') as f:
            json.dump(automation_data, f, indent=2)

        print(f"[OK] Exported {len(automation_data)} videos for automation: {output_file}")
        return output_file


class TikTokAnalytics:
    """Track performance metrics (manual logging)"""

    def __init__(self, analytics_file: Path = None):
        self.analytics_file = Path(analytics_file) if analytics_file else Path("tiktok_analytics.json")
        self.data = self._load_analytics()

    def _load_analytics(self) -> Dict:
        if self.analytics_file.exists():
            with open(self.analytics_file, 'r') as f:
                return json.load(f)
        return {'videos': []}

    def _save_analytics(self):
        with open(self.analytics_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def log_video_stats(self, video_path: str, views: int = 0,
                       likes: int = 0, comments: int = 0, shares: int = 0):
        """Manually log video statistics"""
        stats = {
            'video': video_path,
            'timestamp': datetime.now().isoformat(),
            'views': views,
            'likes': likes,
            'comments': comments,
            'shares': shares,
            'engagement_rate': (likes + comments + shares) / max(views, 1) * 100
        }

        self.data['videos'].append(stats)
        self._save_analytics()
        print(f"[OK] Logged stats for {Path(video_path).name}: {views} views, {likes} likes")

    def show_summary(self):
        """Show analytics summary"""
        if not self.data['videos']:
            print("No analytics data yet")
            return

        total_views = sum(v['views'] for v in self.data['videos'])
        total_likes = sum(v['likes'] for v in self.data['videos'])
        avg_engagement = sum(v['engagement_rate'] for v in self.data['videos']) / len(self.data['videos'])

        print("\n" + "="*60)
        print("TIKTOK ANALYTICS SUMMARY")
        print("="*60)
        print(f"Total Videos: {len(self.data['videos'])}")
        print(f"Total Views: {total_views:,}")
        print(f"Total Likes: {total_likes:,}")
        print(f"Avg Engagement Rate: {avg_engagement:.2f}%")
        print("="*60 + "\n")


if __name__ == "__main__":
    print("TikTok Manager")
    print("="*60)

    prep = TikTokVideoPrep()

    print(f"\nOutput directory: {prep.output_dir.absolute()}")
    print(f"Upload queue: {len(prep.upload_queue)} video(s)")

    if prep.upload_queue:
        print("\nNext to upload:")
        prep.show_upload_instructions()
    else:
        print("\n[OK] No videos in queue")

    print("\nTikTok Video Specifications:")
    for key, value in prep.SPECS.items():
        print(f"  {key}: {value}")
