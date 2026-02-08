"""
Playwright Automated File Downloader - GUI Version
===================================================
A user-friendly graphical interface for downloading files from multiple webpages.

IMPORTANT: Only use this script on websites where you have permission to download files.
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path
from datetime import datetime

# =============================================================================
# DOWNLOADER ENGINE (runs in background thread)
# =============================================================================

class DownloaderEngine:
    """
    Handles the actual downloading logic using Playwright.
    Runs in a separate thread to keep the GUI responsive.
    """
    
    def __init__(self, gui_callback):
        """
        Initialize the downloader engine.
        
        Args:
            gui_callback: Function to call for logging messages to GUI
        """
        self.gui_callback = gui_callback
        self.is_running = False
        self.should_stop = False
    
    def log(self, message, level="INFO"):
        """Send a log message to the GUI."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.gui_callback(f"[{timestamp}] {level}: {message}")
    
    def download_file(self, page, url, download_path, selector, attempt, max_retries, 
                      page_timeout, download_timeout):
        """
        Navigate to a URL and click the download button.
        """
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        
        try:
            self.log(f"[Attempt {attempt}/{max_retries + 1}] Opening: {url}")
            
            # Navigate to the page
            page.goto(url, wait_until="networkidle", timeout=page_timeout)
            self.log("Page loaded successfully")
            
            # Small delay for dynamic content
            page.wait_for_timeout(1000)
            
            # Check if download button exists
            download_button = page.locator(selector)
            
            if download_button.count() == 0:
                self.log(f"Download button not found: {selector}", "WARNING")
                return False
            
            self.log("Found download button, initiating download...")
            
            # Use Playwright's download handling
            with page.expect_download(timeout=download_timeout) as download_info:
                download_button.first.click()
            
            download = download_info.value
            filename = download.suggested_filename
            self.log(f"Downloading: {filename}")
            
            # Save the file
            save_path = os.path.join(download_path, filename)
            download.save_as(save_path)
            
            if os.path.exists(save_path):
                file_size = os.path.getsize(save_path)
                self.log(f"✓ Complete: {filename} ({file_size:,} bytes)", "SUCCESS")
                return True
            else:
                self.log(f"✗ File not saved: {filename}", "ERROR")
                return False
                
        except PlaywrightTimeoutError as e:
            self.log(f"✗ Timeout: {str(e)}", "ERROR")
            return False
        except Exception as e:
            self.log(f"✗ Error: {str(e)}", "ERROR")
            return False
    
    def run(self, urls, settings):
        """
        Main download loop.
        
        Args:
            urls: List of URLs to process
            settings: Dictionary of settings from GUI
        """
        from playwright.sync_api import sync_playwright
        
        self.is_running = True
        self.should_stop = False
        
        # Extract settings
        download_path = settings['download_folder']
        selector = settings['selector']
        max_retries = settings['max_retries']
        delay = settings['delay']
        headless = settings['headless']
        page_timeout = settings['page_timeout'] * 1000  # Convert to ms
        download_timeout = settings['download_timeout'] * 1000
        browser_type = settings['browser_type']
        custom_browser_path = settings['custom_browser_path']
        
        # Create download folder
        Path(download_path).mkdir(parents=True, exist_ok=True)
        
        # Statistics
        successful = 0
        failed = 0
        failed_urls = []
        
        self.log("=" * 50)
        self.log("Starting downloads...")
        self.log(f"URLs to process: {len(urls)}")
        self.log(f"Download folder: {download_path}")
        self.log(f"Button selector: {selector}")
        self.log(f"Browser: {browser_type}" + (f" ({custom_browser_path})" if custom_browser_path else ""))
        self.log("=" * 50)
        
        try:
            with sync_playwright() as playwright:
                self.log("Launching browser...")
                
                # Select browser engine and configure launch options
                launch_options = {
                    'headless': headless,
                    'slow_mo': 100
                }
                
                # Add custom executable path if provided
                if custom_browser_path and os.path.exists(custom_browser_path):
                    launch_options['executable_path'] = custom_browser_path
                    self.log(f"Using custom browser: {custom_browser_path}")
                
                # Launch the appropriate browser
                if browser_type == "Firefox" or (custom_browser_path and "zen" in custom_browser_path.lower()):
                    browser = playwright.firefox.launch(**launch_options)
                elif browser_type == "WebKit":
                    browser = playwright.webkit.launch(**launch_options)
                else:
                    browser = playwright.chromium.launch(**launch_options)
                
                context = browser.new_context(accept_downloads=True)
                page = context.new_page()
                
                for index, url in enumerate(urls, start=1):
                    # Check if user requested stop
                    if self.should_stop:
                        self.log("Download stopped by user", "WARNING")
                        break
                    
                    self.log("-" * 40)
                    self.log(f"Processing URL {index}/{len(urls)}")
                    
                    # Try download with retries
                    success = False
                    for attempt in range(1, max_retries + 2):
                        if self.should_stop:
                            break
                        
                        success = self.download_file(
                            page, url, download_path, selector, 
                            attempt, max_retries, page_timeout, download_timeout
                        )
                        
                        if success:
                            break
                        
                        if attempt <= max_retries:
                            self.log(f"Retrying in {delay} seconds...")
                            time.sleep(delay)
                    
                    if success:
                        successful += 1
                    else:
                        failed += 1
                        failed_urls.append(url)
                    
                    # Delay between downloads
                    if index < len(urls) and not self.should_stop:
                        self.log(f"Waiting {delay} seconds...")
                        time.sleep(delay)
                
                self.log("Closing browser...")
                context.close()
                browser.close()
        
        except Exception as e:
            self.log(f"Browser error: {str(e)}", "ERROR")
        
        # Summary
        self.log("=" * 50)
        self.log("DOWNLOAD SUMMARY")
        self.log("=" * 50)
        self.log(f"Total: {len(urls)} | Success: {successful} | Failed: {failed}")
        
        if failed_urls:
            self.log("Failed URLs:")
            for url in failed_urls:
                self.log(f"  - {url}")
        
        self.log("=" * 50)
        self.log("Done!")
        
        self.is_running = False
        return successful, failed
    
    def stop(self):
        """Request the download loop to stop."""
        self.should_stop = True


# =============================================================================
# GUI APPLICATION
# =============================================================================

class DownloaderGUI:
    """
    Main GUI application class.
    """
    
    def __init__(self):
        """Initialize the GUI."""
        self.root = tk.Tk()
        self.root.title("Playwright File Downloader")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)
        
        # Set icon if available
        try:
            self.root.iconbitmap(default='')
        except:
            pass
        
        # Initialize downloader engine
        self.engine = DownloaderEngine(self.log_message)
        self.download_thread = None
        
        # Build the GUI
        self.create_widgets()
        self.load_settings()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Create all GUI widgets."""
        
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # =====================================================================
        # URL INPUT SECTION
        # =====================================================================
        url_frame = ttk.LabelFrame(main_frame, text="URLs (one per line)", padding="5")
        url_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # URL text area with scrollbar
        self.url_text = scrolledtext.ScrolledText(url_frame, height=10, wrap=tk.NONE)
        self.url_text.pack(fill=tk.BOTH, expand=True)
        
        # URL buttons
        url_btn_frame = ttk.Frame(url_frame)
        url_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(url_btn_frame, text="Load from File", 
                   command=self.load_urls_from_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(url_btn_frame, text="Save to File", 
                   command=self.save_urls_to_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(url_btn_frame, text="Clear", 
                   command=lambda: self.url_text.delete(1.0, tk.END)).pack(side=tk.LEFT)
        
        # URL count label
        self.url_count_var = tk.StringVar(value="0 URLs")
        ttk.Label(url_btn_frame, textvariable=self.url_count_var).pack(side=tk.RIGHT)
        
        # Bind text change event
        self.url_text.bind('<KeyRelease>', self.update_url_count)
        
        # =====================================================================
        # SETTINGS SECTION
        # =====================================================================
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="5")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Row 1: Download folder
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(row1, text="Download Folder:", width=15).pack(side=tk.LEFT)
        self.folder_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.folder_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(row1, text="Browse...", command=self.browse_folder).pack(side=tk.LEFT)
        
        # Row 2: CSS Selector
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(row2, text="Button Selector:", width=15).pack(side=tk.LEFT)
        self.selector_var = tk.StringVar(value="button.download-btn")
        selector_entry = ttk.Entry(row2, textvariable=self.selector_var)
        selector_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Selector presets dropdown
        self.selector_presets = ttk.Combobox(row2, width=20, state="readonly", values=[
            "button.download-btn",
            "a.download-link",
            "#downloadButton",
            'button:has-text("Download")',
            '[data-action="download"]',
            ".btn-download",
        ])
        self.selector_presets.pack(side=tk.LEFT)
        self.selector_presets.bind('<<ComboboxSelected>>', 
                                   lambda e: self.selector_var.set(self.selector_presets.get()))
        
        # Row 3: Options
        row3 = ttk.Frame(settings_frame)
        row3.pack(fill=tk.X, pady=2)
        
        ttk.Label(row3, text="Max Retries:", width=15).pack(side=tk.LEFT)
        self.retries_var = tk.IntVar(value=2)
        ttk.Spinbox(row3, from_=0, to=5, width=5, textvariable=self.retries_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row3, text="Delay (sec):").pack(side=tk.LEFT, padx=(20, 0))
        self.delay_var = tk.IntVar(value=2)
        ttk.Spinbox(row3, from_=1, to=30, width=5, textvariable=self.delay_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row3, text="Page Timeout:").pack(side=tk.LEFT, padx=(20, 0))
        self.page_timeout_var = tk.IntVar(value=30)
        ttk.Spinbox(row3, from_=10, to=120, width=5, textvariable=self.page_timeout_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row3, text="Download Timeout:").pack(side=tk.LEFT, padx=(20, 0))
        self.download_timeout_var = tk.IntVar(value=60)
        ttk.Spinbox(row3, from_=30, to=300, width=5, textvariable=self.download_timeout_var).pack(side=tk.LEFT, padx=5)
        
        # Row 4: Checkboxes
        row4 = ttk.Frame(settings_frame)
        row4.pack(fill=tk.X, pady=2)
        
        self.headless_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row4, text="Headless Mode (hide browser)", 
                        variable=self.headless_var).pack(side=tk.LEFT)
        
        # =====================================================================
        # BROWSER SELECTION SECTION
        # =====================================================================
        browser_frame = ttk.LabelFrame(main_frame, text="Browser Settings", padding="5")
        browser_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Row 1: Browser type selection
        browser_row1 = ttk.Frame(browser_frame)
        browser_row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(browser_row1, text="Browser Type:", width=15).pack(side=tk.LEFT)
        self.browser_type_var = tk.StringVar(value="Chromium")
        browser_combo = ttk.Combobox(browser_row1, textvariable=self.browser_type_var, 
                                      state="readonly", width=15, values=[
            "Chromium",
            "Firefox", 
            "WebKit",
            "Custom"
        ])
        browser_combo.pack(side=tk.LEFT, padx=5)
        browser_combo.bind('<<ComboboxSelected>>', self.on_browser_type_change)
        
        ttk.Label(browser_row1, text="(Zen browser = Firefox-based)", 
                  foreground="gray").pack(side=tk.LEFT, padx=10)
        
        # Row 2: Custom browser path
        browser_row2 = ttk.Frame(browser_frame)
        browser_row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(browser_row2, text="Browser Path:", width=15).pack(side=tk.LEFT)
        self.browser_path_var = tk.StringVar()
        self.browser_path_entry = ttk.Entry(browser_row2, textvariable=self.browser_path_var)
        self.browser_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.browse_browser_btn = ttk.Button(browser_row2, text="Browse...", 
                                              command=self.browse_browser)
        self.browse_browser_btn.pack(side=tk.LEFT)
        
        # Add hint for Zen browser
        browser_row3 = ttk.Frame(browser_frame)
        browser_row3.pack(fill=tk.X, pady=2)
        ttk.Label(browser_row3, 
                  text="💡 Zen browser path is usually: C:\\Users\\<username>\\AppData\\Local\\Zen Browser\\zen.exe",
                  foreground="gray").pack(side=tk.LEFT)
        
        # =====================================================================
        # CONTROL BUTTONS
        # =====================================================================
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="▶ Start Download", 
                                    command=self.start_download)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(control_frame, text="⬛ Stop", 
                                   command=self.stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(control_frame, text="📂 Open Downloads Folder", 
                   command=self.open_downloads_folder).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(control_frame, text="🗑 Clear Log", 
                   command=lambda: self.log_text.delete(1.0, tk.END)).pack(side=tk.RIGHT)
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(control_frame, textvariable=self.progress_var).pack(side=tk.RIGHT, padx=10)
        
        # =====================================================================
        # LOG OUTPUT SECTION
        # =====================================================================
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, wrap=tk.WORD,
                                                   state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure log colors
        self.log_text.tag_config("SUCCESS", foreground="green")
        self.log_text.tag_config("ERROR", foreground="red")
        self.log_text.tag_config("WARNING", foreground="orange")
        self.log_text.tag_config("INFO", foreground="black")
    
    def load_settings(self):
        """Load default settings."""
        # Set default download folder
        script_dir = Path(__file__).parent.absolute()
        default_folder = script_dir / "downloads"
        self.folder_var.set(str(default_folder))
        
        # Try to load links.txt if it exists
        links_file = script_dir / "links.txt"
        if links_file.exists():
            self.load_urls_from_file(str(links_file))
    
    def log_message(self, message):
        """
        Add a message to the log output.
        Thread-safe - can be called from any thread.
        """
        def update():
            self.log_text.config(state=tk.NORMAL)
            
            # Determine tag based on message content
            tag = "INFO"
            if "SUCCESS" in message or "✓" in message:
                tag = "SUCCESS"
            elif "ERROR" in message or "✗" in message:
                tag = "ERROR"
            elif "WARNING" in message:
                tag = "WARNING"
            
            self.log_text.insert(tk.END, message + "\n", tag)
            self.log_text.see(tk.END)  # Auto-scroll to bottom
            self.log_text.config(state=tk.DISABLED)
        
        # Schedule update on main thread
        self.root.after(0, update)
    
    def update_url_count(self, event=None):
        """Update the URL count label."""
        text = self.url_text.get(1.0, tk.END).strip()
        urls = [url.strip() for url in text.split('\n') if url.strip() and not url.strip().startswith('#')]
        self.url_count_var.set(f"{len(urls)} URLs")
    
    def browse_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(title="Select Download Folder")
        if folder:
            self.folder_var.set(folder)
    
    def load_urls_from_file(self, filepath=None):
        """Load URLs from a text file."""
        if filepath is None:
            filepath = filedialog.askopenfilename(
                title="Select Links File",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
        
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.url_text.delete(1.0, tk.END)
                self.url_text.insert(1.0, content)
                self.update_url_count()
                self.log_message(f"Loaded URLs from: {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
    
    def save_urls_to_file(self):
        """Save URLs to a text file."""
        filepath = filedialog.asksaveasfilename(
            title="Save Links File",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.url_text.get(1.0, tk.END))
                self.log_message(f"Saved URLs to: {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
    
    def open_downloads_folder(self):
        """Open the downloads folder in file explorer."""
        folder = self.folder_var.get()
        if os.path.exists(folder):
            os.startfile(folder)
        else:
            messagebox.showinfo("Info", "Download folder doesn't exist yet.")
    
    def get_urls(self):
        """Get list of URLs from the text area."""
        text = self.url_text.get(1.0, tk.END).strip()
        urls = [url.strip() for url in text.split('\n') 
                if url.strip() and not url.strip().startswith('#')]
        return urls
    
    def get_settings(self):
        """Get current settings as a dictionary."""
        return {
            'download_folder': self.folder_var.get(),
            'selector': self.selector_var.get(),
            'max_retries': self.retries_var.get(),
            'delay': self.delay_var.get(),
            'headless': self.headless_var.get(),
            'page_timeout': self.page_timeout_var.get(),
            'download_timeout': self.download_timeout_var.get(),
            'browser_type': self.browser_type_var.get(),
            'custom_browser_path': self.browser_path_var.get().strip(),
        }
    
    def start_download(self):
        """Start the download process in a background thread."""
        # Validate inputs
        urls = self.get_urls()
        if not urls:
            messagebox.showwarning("Warning", "Please add at least one URL.")
            return
        
        if not self.selector_var.get().strip():
            messagebox.showwarning("Warning", "Please enter a button selector.")
            return
        
        if not self.folder_var.get().strip():
            messagebox.showwarning("Warning", "Please select a download folder.")
            return
        
        # Check if Playwright is installed
        try:
            import playwright
        except ImportError:
            messagebox.showerror("Error", 
                "Playwright is not installed.\n\n"
                "Run these commands:\n"
                "pip install playwright\n"
                "playwright install chromium")
            return
        
        # Update UI
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set("Downloading...")
        
        # Start download in background thread
        settings = self.get_settings()
        self.download_thread = threading.Thread(
            target=self.run_download_thread,
            args=(urls, settings),
            daemon=True
        )
        self.download_thread.start()
    
    def run_download_thread(self, urls, settings):
        """Run downloads in background thread."""
        try:
            self.engine.run(urls, settings)
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
        finally:
            # Update UI on completion (schedule on main thread)
            self.root.after(0, self.download_complete)
    
    def download_complete(self):
        """Called when download process completes."""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_var.set("Ready")
    
    def stop_download(self):
        """Stop the download process."""
        self.engine.stop()
        self.progress_var.set("Stopping...")
        self.stop_btn.config(state=tk.DISABLED)
    
    def on_closing(self):
        """Handle window close event."""
        if self.engine.is_running:
            if messagebox.askokcancel("Quit", "Download in progress. Stop and quit?"):
                self.engine.stop()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def on_browser_type_change(self, event=None):
        """Handle browser type selection change."""
        browser_type = self.browser_type_var.get()
        if browser_type == "Custom":
            # Enable path entry for custom browser
            self.browser_path_entry.config(state=tk.NORMAL)
            self.browse_browser_btn.config(state=tk.NORMAL)
        else:
            # Clear and keep enabled for optional custom path
            pass
    
    def browse_browser(self):
        """Open file browser to select browser executable."""
        filepath = filedialog.askopenfilename(
            title="Select Browser Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~\\AppData\\Local")
        )
        if filepath:
            self.browser_path_var.set(filepath)
            # Auto-detect browser type based on path
            if "zen" in filepath.lower() or "firefox" in filepath.lower():
                self.browser_type_var.set("Firefox")
            elif "chrome" in filepath.lower() or "chromium" in filepath.lower():
                self.browser_type_var.set("Chromium")
    
    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app = DownloaderGUI()
    app.run()
