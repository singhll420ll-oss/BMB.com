# Fonts Directory

This directory contains custom fonts for the Bite Me Buddy application.

## Required Fonts:

### 1. Digital-7 Font (for clock)
- File: `digital-7.ttf` or `digital-7.woff2`
- Source: https://www.dafont.com/digital-7.font
- Used for the secret clock display

### 2. Montserrat (for headings)
- File: Not stored locally - using Google Fonts CDN
- Import in CSS: @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

### 3. Segoe UI (for body text)
- System font, no download needed

## Installation Instructions:

1. Download digital-7.ttf from the link above
2. Convert to WOFF2 for better performance:
   ```bash
   # Using fonttools
   pyftsubset digital-7.ttf --output-file=digital-7.woff2 --flavor=woff2
