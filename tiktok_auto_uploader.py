#!/usr/bin/env python3
"""
Automatic TikTok video uploader using Playwright browser automation
Improved version with better reliability and error handling
Supports Google authentication
"""

import os
import time
from pathlib import Path
from typing import Optional, Dict
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeout
import json
import random


class TikTokAutoUploader:
    """Automate TikTok video uploads with Google authentication - Enhanced version"""

    def __init__(self, headless: bool = False, session_file: str = "./tiktok_session.json", debug: bool = False):
        """
        Initialize TikTok auto uploader

        Args:
            headless: Run browser in headless mode (not recommended for first login)
            session_file: Path to save/load browser session
            debug: Enable debug mode (saves screenshots on errors)
        """
        self.headless = headless
        self.session_file = Path(session_file)
        self.debug = debug
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None

        # Create debug directory if needed
        if self.debug:
            self.debug_dir = Path("./debug_screenshots")
            self.debug_dir.mkdir(exist_ok=True)

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup"""
        self.close()

    def close(self):
        """Close browser and cleanup"""
        if self.page:
            try:
                self.page.close()
            except:
                pass
        if self.context:
            try:
                self.context.close()
            except:
                pass
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass

    def _save_debug_screenshot(self, name: str):
        """Save screenshot for debugging"""
        if self.debug and self.page:
            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                screenshot_path = self.debug_dir / f"{timestamp}_{name}.png"
                self.page.screenshot(path=str(screenshot_path))
                print(f"📸 Debug screenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"⚠️  Could not save screenshot: {e}")

    def _human_delay(self, min_sec=0.5, max_sec=2.0):
        """Add human-like delay"""
        time.sleep(random.uniform(min_sec, max_sec))

    def _wait_for_element(self, selectors: list, timeout: int = 10000) -> Optional[str]:
        """
        Wait for one of multiple selectors to appear
        Returns the selector that was found, or None
        """
        for selector in selectors:
            try:
                self.page.wait_for_selector(selector, timeout=timeout, state='visible')
                return selector
            except PlaywrightTimeout:
                continue
        return None

    def _click_element(self, selectors: list, timeout: int = 10000) -> bool:
        """
        Try to click one of multiple selectors
        Returns True if clicked, False otherwise
        """
        found_selector = self._wait_for_element(selectors, timeout)
        if found_selector:
            try:
                self.page.click(found_selector)
                self._human_delay()
                return True
            except Exception as e:
                print(f"⚠️  Could not click {found_selector}: {e}")
                return False
        return False

    def _wait_for_login(self, page: Page, timeout: int = 300000):
        """
        Wait for user to complete Google login manually

        Args:
            page: Playwright page
            timeout: Maximum wait time in milliseconds (default 5 minutes)
        """
        print("\n" + "="*70)
        print("🔐 AUTHENTIFICATION GOOGLE REQUISE")
        print("="*70)
        print("\nUne fenêtre de navigateur s'est ouverte.")
        print("Veuillez vous connecter avec votre compte Google.")
        print("\nAttente de l'authentification...")
        print("(Le script continuera automatiquement après connexion)")
        print("="*70 + "\n")

        try:
            # Wait for successful redirect to TikTok upload page or main page
            page.wait_for_url("https://www.tiktok.com/**", timeout=timeout)
            print("✅ Authentification réussie!\n")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Timeout ou erreur d'authentification: {e}")
            return False

    def login_with_google(self):
        """
        Login to TikTok using Google authentication
        Opens browser for manual Google login
        Enhanced with better error handling and detection
        """
        self.playwright = sync_playwright().start()

        # Enhanced browser args for better stealth
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-infobars',
            '--window-size=1280,720',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process'
        ]

        # Try different browser channels
        for channel in ['chrome', 'msedge', 'chromium', None]:
            try:
                print(f"🌐 Tentative de lancement du navigateur (channel={channel or 'default'})...")
                if channel:
                    self.browser = self.playwright.chromium.launch(
                        headless=self.headless,
                        channel=channel,
                        args=browser_args
                    )
                else:
                    self.browser = self.playwright.chromium.launch(
                        headless=self.headless,
                        args=browser_args
                    )
                print(f"✅ Navigateur lancé avec succès!")
                break
            except Exception as e:
                print(f"⚠️  Échec avec {channel or 'default'}: {e}")
                if channel is None:
                    raise Exception("Impossible de lancer le navigateur. Installez Chrome, Edge ou Chromium.")

        # Create context with session persistence and realistic settings
        context_options = {
            'viewport': {'width': 1280, 'height': 720},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'locale': 'fr-FR',
            'timezone_id': 'Europe/Paris'
        }

        if self.session_file.exists():
            print("📂 Chargement de la session existante...")
            try:
                with open(self.session_file) as f:
                    storage_state = json.load(f)
                context_options['storage_state'] = storage_state
            except Exception as e:
                print(f"⚠️  Impossible de charger la session: {e}")

        self.context = self.browser.new_context(**context_options)
        self.page = self.context.new_page()

        # Inject anti-detection script
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Navigate to TikTok upload page
        print("🌐 Navigation vers TikTok...")
        try:
            self.page.goto("https://www.tiktok.com/upload", wait_until='networkidle', timeout=30000)
        except:
            self.page.goto("https://www.tiktok.com/upload", timeout=30000)

        self._human_delay(2, 4)
        self._save_debug_screenshot("01_initial_page")

        # Check if already logged in
        if self._is_logged_in():
            print("✅ Déjà connecté!")
            return True

        # Need to login
        print("🔑 Tentative de connexion avec Google...")

        # Look for login button
        login_selectors = [
            "button:has-text('Log in')",
            "button:has-text('Se connecter')",
            "[data-e2e='top-login-button']",
            "a:has-text('Log in')",
            "a:has-text('Se connecter')"
        ]

        if not self._click_element(login_selectors, timeout=10000):
            self._save_debug_screenshot("02_login_button_not_found")
            print("⚠️  Bouton de connexion introuvable, tentative de navigation directe...")
            self.page.goto("https://www.tiktok.com/login", timeout=30000)

        self._human_delay(1, 2)
        self._save_debug_screenshot("03_login_page")

        # Click on Google login option
        google_selectors = [
            "[data-e2e='channel-item'][href*='google']",
            "div[role='link']:has-text('Google')",
            "a:has-text('Continue with Google')",
            "a:has-text('Continuer avec Google')",
            "div[data-e2e='google-icon']"
        ]

        if not self._click_element(google_selectors, timeout=10000):
            self._save_debug_screenshot("04_google_button_not_found")
            print("❌ Impossible de trouver le bouton Google")
            return False

        self._save_debug_screenshot("05_before_google_auth")

        # Wait for user to complete Google authentication
        if not self._wait_for_login(self.page):
            self._save_debug_screenshot("06_login_failed")
            return False

        # Save session for future use
        try:
            storage_state = self.context.storage_state()
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_file, 'w') as f:
                json.dump(storage_state, f)
            print(f"💾 Session sauvegardée dans {self.session_file}")
        except Exception as e:
            print(f"⚠️  Impossible de sauvegarder la session: {e}")

        self._save_debug_screenshot("07_login_success")
        return True

    def _is_logged_in(self) -> bool:
        """Check if user is already logged in"""
        # Check for upload interface elements
        upload_indicators = [
            "input[type='file']",
            "[data-e2e='upload-btn']",
            "text='Select file'"
        ]

        for selector in upload_indicators:
            try:
                if self.page.locator(selector).is_visible(timeout=3000):
                    return True
            except:
                continue

        return False

    def upload_video(
        self,
        video_path: Path,
        title: str,
        hashtags: list,
        description: str = "",
        use_recommended_music: bool = False,
        publish: bool = True
    ) -> bool:
        """
        Upload a video to TikTok - Enhanced version

        Args:
            video_path: Path to video file
            title: Video title
            hashtags: List of hashtags (without #)
            description: Video description
            use_recommended_music: Use TikTok's recommended music (disabled by default as it's unreliable)
            publish: Publish immediately (True) or save as draft (False)

        Returns:
            True if upload successful
        """
        if not self.page:
            print("❌ Pas de session active. Appelez login_with_google() d'abord.")
            return False

        try:
            print(f"\n{'='*70}")
            print(f"📤 UPLOAD TIKTOK: {video_path.name}")
            print(f"{'='*70}\n")

            # Navigate to upload page
            print("🌐 Navigation vers la page d'upload...")
            try:
                self.page.goto("https://www.tiktok.com/upload", wait_until='networkidle', timeout=30000)
            except:
                self.page.goto("https://www.tiktok.com/upload", timeout=30000)

            self._human_delay(2, 3)
            self._save_debug_screenshot("10_upload_page")

            # Check if logged in
            if not self._is_logged_in():
                print("❌ Session expirée. Reconnectez-vous.")
                return False

            # Upload video file
            print("📁 Upload du fichier vidéo...")
            file_input_selectors = [
                "input[type='file'][accept*='video']",
                "input[type='file']",
                "input[accept*='video']"
            ]

            file_input_selector = self._wait_for_element(file_input_selectors, timeout=10000)
            if not file_input_selector:
                self._save_debug_screenshot("11_file_input_not_found")
                print("❌ Impossible de trouver le bouton d'upload")
                return False

            # Upload the file
            self.page.set_input_files(file_input_selector, str(video_path.absolute()))
            print("✅ Fichier sélectionné, traitement en cours...")
            self._human_delay(3, 5)
            self._save_debug_screenshot("12_video_uploaded")

            # Wait for video processing (check for preview)
            print("⏳ Attente du traitement de la vidéo...")
            processing_timeout = 60  # 60 seconds max
            start_time = time.time()

            while time.time() - start_time < processing_timeout:
                try:
                    # Check if caption field is available (indicates video is processed)
                    caption_selectors = [
                        "div[contenteditable='true']",
                        "[data-e2e='video-caption']",
                        "div.public-DraftEditor-content"
                    ]

                    if self._wait_for_element(caption_selectors, timeout=3000):
                        print("✅ Vidéo traitée!")
                        break
                except:
                    pass

                self._human_delay(2, 3)
            else:
                print("⚠️  Timeout lors du traitement, continuant quand même...")

            self._save_debug_screenshot("13_video_processed")

            # Add caption (title + hashtags + description)
            print("📝 Ajout du titre et hashtags...")
            caption = f"{title}\n\n"
            caption += " ".join(f"#{tag}" for tag in hashtags)
            if description:
                caption += f"\n\n{description}"

            caption_selectors = [
                "div[contenteditable='true']",
                "[data-e2e='video-caption']",
                "div.public-DraftEditor-content",
                "div[data-contents='true']"
            ]

            caption_added = False
            for selector in caption_selectors:
                try:
                    caption_elem = self.page.locator(selector).first
                    if caption_elem.is_visible(timeout=3000):
                        caption_elem.click()
                        self._human_delay(0.5, 1)
                        caption_elem.fill(caption)
                        self._human_delay(1, 2)
                        print(f"✅ Caption ajoutée ({len(caption)} caractères)")
                        caption_added = True
                        break
                except Exception as e:
                    continue

            if not caption_added:
                self._save_debug_screenshot("14_caption_failed")
                print("⚠️  Impossible d'ajouter la caption")

            self._save_debug_screenshot("15_caption_added")

            # Skip music selection as it's unreliable
            if use_recommended_music:
                print("⚠️  Sélection de musique désactivée (peu fiable)")

            # Scroll down to make publish button visible
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self._human_delay(1, 2)
            self._save_debug_screenshot("16_scrolled_down")

            # Publish or save as draft
            if publish:
                print("🚀 Publication de la vidéo...")
                publish_selectors = [
                    "button[data-e2e='post-button']",
                    "button:has-text('Post')",
                    "button:has-text('Publier')",
                    "div[role='button']:has-text('Post')",
                    "div[role='button']:has-text('Publier')"
                ]
            else:
                print("💾 Sauvegarde en brouillon...")
                publish_selectors = [
                    "button:has-text('Save as draft')",
                    "button:has-text('Sauvegarder comme brouillon')",
                    "[data-e2e='draft-btn']"
                ]

            if self._click_element(publish_selectors, timeout=5000):
                print("✅ Vidéo " + ("publiée" if publish else "sauvegardée en brouillon") + " avec succès!")
                self._human_delay(3, 5)
                self._save_debug_screenshot("17_published")
                return True
            else:
                self._save_debug_screenshot("18_publish_button_not_found")
                print("⚠️  Impossible de trouver le bouton de publication")
                print("   La vidéo a été préparée mais doit être publiée manuellement")

                # Keep browser open for manual intervention
                print("\n" + "="*70)
                print("⏸️  INTERVENTION MANUELLE REQUISE")
                print("="*70)
                print("Veuillez cliquer sur le bouton 'Publier' manuellement dans le navigateur.")
                input("Appuyez sur Entrée une fois terminé...")
                return True

        except Exception as e:
            self._save_debug_screenshot("19_error")
            print(f"❌ Erreur lors de l'upload: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Test the TikTok auto uploader"""
    print("TikTok Auto Uploader - Test Mode")
    print("="*70)

    # Initialize uploader
    uploader = TikTokAutoUploader(headless=False)

    # Login with Google
    print("\n🔑 Connexion à TikTok avec Google...")
    if not uploader.login_with_google():
        print("❌ Échec de la connexion")
        return

    print("\n✅ Connexion réussie!")
    print("📝 Le système est maintenant prêt à uploader des vidéos.")
    print("\nPour tester l'upload, modifiez le code main() avec un vrai fichier vidéo.")

    # Example upload (commented out - uncomment to test)
    """
    test_video = Path("./tiktok_ready/test_video.mp4")
    if test_video.exists():
        uploader.upload_video(
            video_path=test_video,
            title="Test Video",
            hashtags=["chess", "test", "tiktok"],
            description="Test automatique",
            use_recommended_music=True,
            publish=False  # Save as draft for testing
        )
    """

    uploader.close()


if __name__ == "__main__":
    main()
