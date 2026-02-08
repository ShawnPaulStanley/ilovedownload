# Playwright Automated File Downloader

A Python automation tool that handles batch downloading from multiple webpages. Just give it a list of URLs, tell it what button to click, and let it do the repetitive work for you.

**Important**: This is meant for legitimate use only. Make sure you have permission to download from the websites you're automating.

## What It Does

This tool automates the tedious process of opening multiple download pages and clicking download buttons. Instead of manually visiting each page, waiting for it to load, finding the download button, and repeating this dozens of times, you can:

- Give it a list of URLs
- Tell it which button to click (using a CSS selector)
- Watch it work through your list automatically
- Find all your files neatly organized in a downloads folder

The script handles the boring stuff: waiting for pages to load, retrying failed downloads, dealing with errors, and keeping track of what worked and what didn't.

## Two Ways to Use It

There are two versions included:

1. **downloader_gui.py** - Graphical interface with buttons and settings (recommended for most people)
2. **downloader.py** - Command-line version if you prefer running scripts from terminal

Both do the same thing, just different interfaces. The GUI version is easier to configure and lets you change settings without editing code.

## Getting Started

### Install Dependencies

First, install Playwright:

```bash
pip install -r requirements.txt
```

Then install the browser engines. You only need Chromium unless you want to use Firefox or WebKit:

```bash
plaUsing the GUI Version (Easier)

Run this:

```bash
python downloader_gui.py
```

A window will open where you can:

1. **Add your URLs** - Paste them directly or load from a text file
2. **Set the button selector** - Choose from presets or enter your own
3. **Pick your browser** - Use Chromium, Firefox, WebKit, or even custom browsers like Zen
4. **Configure settings** - Retries, delays, timeouts, etc.
5. **Click Start** - Watch it work in real-time with a live log

The GUI remembers your settings and has helpful presets for common selectors. You can also specify a custom browser executable if you prefer using Zen Browser, Brave, or any Chromium/Firefox-based browser.

## Finding the Right Button Selector

This is the most important part. You need to tell the script which button to click. Here's how:

1. Open one of your download pages in a browser
2. Right-click the download button and select "Inspect" or "Inspect Element"
3. Look at the HTML element that gets highlighted in the developer tools
4. Find either the `class` or `id` attribute

Common patterns you'll see:

- `<button class="download-btn">` use `button.download-btn`
- `<a class="link-button">` use `a.link-button`
- `<button id="downloadBtn">` use `#downloadBtn`
- Multiple classes like `<button class="btn primary">` use `button.btn.primary`
- If nothing works, try `button:has-text("Download")` to match button text

The selector is just a way to uniquely identify the button. Once you find it, enter it in the GUI or in the script settings

| Website Type | Example Selector |
|--------------|------------------|
| Button with class | `button.download-btn` |
| Link with class | `a.download-link` |
| Button with ID | `#downloadButton` |
| Button with text | `button:has-text("Download")` |
| Data attribute | `[data-action="download"]` |
| Muling the Command-Line Version

If you prefer editing code and running things from terminal:

1. Open `downloader.py` and update the settings at the top:
   - `DOWNLOAD_BUTTON_SELECTOR` - The CSS selector for the download button
   - `MAX_RETRIES` - How many times to retry failed downloads
   - `DELAY_BETWEEN_DOWNLOADS` - Seconds to wait between downloads
   - `HEADLESS_MODE` - True to hide browser, False to watch it work

2. Add your URLs to `links.txt` (one per line)

3. Run it:
   ```bash
   python downloader.py
   ```

The script will show you what it's doing in real-time and give you a summary at the end.

## What Happens When You Run It

The script will:

1. Read your list of URLs
2. Open a browser window
3. Visit each URL one by one
4. Wait for the page to load completely
5. Find and click the download button
6. Wait for the download to finish
7. Move to the next URL
8. Give you a summary when done

All downloaded files go into a "downloads" folder that gets created automatically. The script also logs everything it does, so you can see exactly what happened with each URL.

If a download fails, it will automatically retry a couple times before giving up and moving to the next one. At the end, you'll get a list of which URLs succeeded and which ones had problems.6-02-08 10:30:05 - INFO - Found download button, initiating download...
2026-02-08 10:30:06 - INFO - Downloading: file1.pdf
2026-02-08 10:30:10 - INFO - ✓ Download complete: file1.pdf (1,234,567 bytes)
...
```

## Troubleshooting

### "Download button not found"
- Check that `DOWNLOAD_BUTTON_SELECTOR` matches the actual button on the website
- Use browser DevTools to inspect the button element
- The button might load dynamically - try increasing `PAGE_LOAD_TIMEOUT`

###Common Issues and Solutions

**"Download button not found"**

The selector you entered doesn't match anything on the page. Double-check the selector by inspecting the button element in your browser's developer tools. Sometimes buttons are inside other elements or have classes that change dynamically.

**"Timeout error"**

The page is taking too long to load or the download isn't starting. Try increasing the timeout values in settings. Some websites are just slow or have rate limiting.

**Browser won't launch**

Make sure you ran `playwright install` after installing the package. The browser binaries are separate from the Python package and need to be downloaded.

**Download starts but file doesn't save**

Check that you have write permissions for the downloads folder. Also make sure you have enough disk space for the files you're downloading.

**Using Zen Browser or other custom browsers**

In Project Files

```
ilovedownload/
├── downloader_gui.py  # GUI version - recommended
├── downloader.py      # Command-line version
├── requirements.txt   # Dependencies to install
├── links.txt          # Put your URLs here
├── README.md          # You're reading it
└── downloads/         # Where files get saved
```

## Notes

This tool is for automating legitimate downloads you're already allowed to make. It just saves you from the tedium of clicking through dozens or hundreds of download pages manually.

Use it responsibly. Don't hammer servers with too many requests. The built-in delays exist for a reason.

If a website has an API or bulk download option, use that instead. This is more of a last resort when you need to automate browser-based downloads and there's no better way