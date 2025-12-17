import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

# ================= CONFIG =================
SHIFT_URL = "https://933bba13123200.na.deputy.com/exec/hr/roster_confirm?p=eyJFbXBsb3llZUlkIjo0MjY0LCJGcm9tIjoxNzY1Nzc0ODAwLCJUbyI6MTc2NjM3OTU5OSwiY2hlY2tzdW0iOiI3NWVmNTUxZTMwMDdjOTc0MWFmNTVhYzEyMjA2ODYwNjI1ODZmYWFmIn0="
# =========================================

# ================= SHIFT SCANNER & CLAIMER =================
class ShiftAutoClaimer:
    def __init__(self, url):
        self.url = url
        self.playwright = None
        self.browser = None
        self.page = None
        self.seen_shifts = {}  # Track shifts we've already seen: {shift_id: status}
        self.claimed_shifts = set()  # Track claimed shift IDs
        
    def start(self):
        """Start the auto-claimer"""
        print("\n" + "="*60)
        print("🚀 SHIFT AUTO-CLAIMER - OPTIMIZED")
        print("="*60)
        print(f"URL: {self.url}")
        print("📝 Tracking seen shifts for faster iterations")
        print("\n🔄 Running in continuous mode - Press Ctrl+C to stop\n")
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-gpu"
            ]
        )
        
        self.page = self.browser.new_page()
        self.page.set_default_timeout(30000)
        
        try:
            print("🌐 Loading page...")
            self.page.goto(self.url, wait_until="load", timeout=30000)
            time.sleep(3)
            print("✅ Page loaded successfully")
            
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            raise
        
        self.continuous_scan()
        
    def continuous_scan(self):
        """Continuously scan and claim shifts with seen shift tracking"""
        iteration = 0
        
        while True:
            iteration += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n{'='*60}")
            print(f"🔍 SCAN #{iteration} - {current_time}")
            print('='*60)
            
            try:
                start_time = time.time()
                
                # Collect only NEW shifts (not seen before)
                new_shifts = self.collect_new_shifts()
                
                if new_shifts:
                    print(f"\n📊 Found {len(new_shifts)} NEW shifts")
                    self.display_new_shifts(new_shifts)
                    
                    # Try to claim available new shifts
                    shifts_claimed = self.claim_new_shifts(new_shifts)
                    
                    if shifts_claimed > 0:
                        print(f"✅ Claimed {shifts_claimed} new shift(s)")
                else:
                    print("\n📭 No new shifts found")
                
                scan_time = time.time() - start_time
                print(f"\n⏱️  Scan completed in {scan_time:.2f}s")
                
                # Show overall statistics
                self.show_statistics()
                
                # Wait and refresh
                print("\n🔄 Refreshing page...")
                self.page.reload(wait_until="domcontentloaded", timeout=10000)
                time.sleep(2)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"[ERROR] Scan error: {str(e)[:100]}")
                print("🔄 Attempting recovery...")
                try:
                    self.page.reload(wait_until="domcontentloaded", timeout=15000)
                    time.sleep(3)
                except:
                    self.restart_browser()
    
    def collect_new_shifts(self):
        """Collect only shifts we haven't seen before"""
        print("\n🔍 Scanning for NEW shifts...")
        new_shifts = []
        
        # Get all text elements that might contain shift info
        all_elements = self.page.query_selector_all("div, span, td, li, p")
        
        for element in all_elements:
            try:
                element_text = element.inner_text().strip()
                if not element_text or len(element_text) < 20:
                    continue
                    
                # Check if this looks like a shift
                if self.is_shift_text(element_text):
                    # Create a unique ID for this shift
                    shift_id = self.generate_shift_id(element_text)
                    
                    # Skip if we've already seen this shift
                    if shift_id in self.seen_shifts:
                        continue
                    
                    # Get shift status
                    status = self.get_shift_status(element)
                    
                    # Store in seen shifts
                    self.seen_shifts[shift_id] = {
                        'status': status,
                        'first_seen': datetime.now().strftime("%H:%M:%S"),
                        'info': self.extract_shift_info(element_text)
                    }
                    
                    # Clean and extract shift info
                    shift_info = self.extract_shift_info(element_text)
                    
                    if shift_info:
                        new_shifts.append({
                            'id': shift_id,
                            'info': shift_info,
                            'status': status,
                            'element': element
                        })
                        
            except:
                continue
        
        # Remove duplicates based on shift info
        unique_shifts = []
        seen_infos = set()
        
        for shift in new_shifts:
            if shift['info'] not in seen_infos:
                seen_infos.add(shift['info'])
                unique_shifts.append(shift)
        
        return unique_shifts
    
    def generate_shift_id(self, text):
        """Generate a unique ID for a shift based on its content"""
        # Extract key parts for the ID
        # Find date pattern (e.g., "Wed 17 Dec")
        date_match = re.search(r'\b(mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+\d{1,2}\s+\w{3}', text.lower())
        
        # Find time pattern (e.g., "10:00 am - 11:00 am")
        time_match = re.search(r'\b\d{1,2}:\d{2}\s*(am|pm)\s*-\s*\d{1,2}:\d{2}\s*(am|pm)', text.lower())
        
        # Combine for unique ID
        if date_match and time_match:
            return f"{date_match.group()}_{time_match.group()}".replace(" ", "_")
        else:
            # Fallback: hash of first 100 chars
            import hashlib
            return hashlib.md5(text[:100].encode()).hexdigest()[:12]
    
    def is_shift_text(self, text):
        """Check if text contains shift information"""
        text_lower = text.lower()
        
        # Check for day patterns
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
                'monday', 'tuesday', 'wednesday', 'thursday', 
                'friday', 'saturday', 'sunday']
        
        has_day = any(f' {day} ' in f' {text_lower} ' for day in days)
        
        # Check for time patterns (hh:mm am/pm)
        has_time = bool(re.search(r'\b\d{1,2}:\d{2}\s*(am|pm)\b', text_lower, re.IGNORECASE))
        
        # Check for EST timezone
        has_est = ' est' in text_lower or ' EST' in text_lower
        
        # Check for shift keyword
        has_shift = 'shift' in text_lower or 'glo' in text_lower.lower()
        
        return (has_day and has_time) or (has_day and has_est) or (has_day and has_shift)
    
    def extract_shift_info(self, text):
        """Extract clean shift information"""
        # Split by lines and filter
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Look for the line containing date and time
        shift_lines = []
        for line in lines:
            # Check if line contains day and time
            has_day = bool(re.search(r'\b(mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', line, re.IGNORECASE))
            has_time = bool(re.search(r'\b\d{1,2}:\d{2}\s*(am|pm)\b', line, re.IGNORECASE))
            
            if has_day and has_time:
                # Clean up the line
                clean_line = re.sub(r'\s+', ' ', line)
                shift_lines.append(clean_line)
        
        # If we found specific shift lines, return them
        if shift_lines:
            return " | ".join(shift_lines[:2])
        
        # Otherwise return first meaningful line
        for line in lines:
            if len(line) > 10 and any(word in line.lower() for word in ['am', 'pm', 'est']):
                return line[:80]
        
        # Fallback
        return text[:60]
    
    def get_shift_status(self, element):
        """Determine shift status based on buttons and text"""
        try:
            element_text = element.inner_text().lower()
            
            # Check for claim buttons
            has_claim_button = False
            claim_selectors = [
                "button:has-text('Claim')",
                "button:has-text('CLAIM')",
                "button:has-text('Accept')",
                "button:has-text('ACCEPT')",
                "a:has-text('Claim')",
                "a:has-text('Accept')"
            ]
            
            for selector in claim_selectors:
                try:
                    btn = element.query_selector(selector)
                    if btn and btn.is_visible():
                        has_claim_button = True
                        break
                except:
                    continue
            
            # Check for accepted text
            has_accepted = 'accepted' in element_text
            
            # Apply rules
            if has_claim_button:
                return "MY CLAIM"
            elif has_accepted:
                return "ALREADY CLAIMED"
            else:
                return "NOT MY CLAIM"
                
        except:
            return "UNKNOWN"
    
    def display_new_shifts(self, shifts):
        """Display newly found shifts with their status"""
        print("-" * 100)
        
        # Group shifts by status for better display
        status_groups = {}
        for shift in shifts:
            status = shift['status']
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(shift)
        
        # Display order
        display_order = ["MY CLAIM", "ALREADY CLAIMED", "NOT MY CLAIM", "UNKNOWN"]
        
        for status in display_order:
            if status in status_groups:
                shifts_in_group = status_groups[status]
                
                # Status symbol
                symbol = "🚀" if status == "MY CLAIM" else \
                         "✅" if status == "ALREADY CLAIMED" else \
                         "❌" if status == "NOT MY CLAIM" else "❓"
                
                print(f"\n{symbol} {status} ({len(shifts_in_group)} new):")
                print("-" * 40)
                
                for i, shift in enumerate(shifts_in_group, 1):
                    print(f"{i:2d}. {shift['info']}")
        
        print("\n" + "-" * 100)
    
    def claim_new_shifts(self, shifts):
        """Claim new shifts that are available (MY CLAIM status)"""
        shifts_claimed = 0
        
        # Filter for new shifts that need claiming
        claimable_shifts = [s for s in shifts if s['status'] == "MY CLAIM"]
        
        if not claimable_shifts:
            return 0
        
        print(f"\n🎯 ATTEMPTING TO CLAIM {len(claimable_shifts)} NEW SHIFT(S)...")
        
        for shift in claimable_shifts:
            try:
                claimed = self.claim_single_shift(shift)
                if claimed:
                    shifts_claimed += 1
                    # Mark as claimed in seen shifts
                    self.claimed_shifts.add(shift['id'])
                    time.sleep(0.5)  # Brief pause between claims
            except Exception as e:
                print(f"[ERROR] Failed to claim shift: {str(e)[:50]}")
                continue
        
        return shifts_claimed
    
    def claim_single_shift(self, shift):
        """Claim a single shift"""
        try:
            element = shift['element']
            
            # Find claim button within the element
            claim_button = None
            claim_selectors = [
                "button:has-text('Claim')",
                "button:has-text('CLAIM')",
                "button:has-text('Accept')",
                "button:has-text('ACCEPT')",
                "a:has-text('Claim')",
                "a:has-text('Accept')"
            ]
            
            for selector in claim_selectors:
                try:
                    btn = element.query_selector(selector)
                    if btn and btn.is_visible():
                        claim_button = btn
                        break
                except:
                    continue
            
            if not claim_button:
                # Look in nearby elements
                parent = element.query_selector("..")
                for _ in range(3):
                    if parent:
                        for selector in claim_selectors:
                            try:
                                btn = parent.query_selector(selector)
                                if btn and btn.is_visible():
                                    claim_button = btn
                                    break
                            except:
                                continue
                        if claim_button:
                            break
                        parent = parent.query_selector("..")
            
            if claim_button:
                print(f"[CLAIMING] {shift['info'][:60]}...")
                
                # Click the button
                claim_button.click(delay=20)
                time.sleep(0.5)
                
                # Handle confirmation dialogs
                self.handle_confirmation_dialogs()
                
                print(f"[SUCCESS] Claimed: {shift['info'][:50]}")
                return True
            else:
                print(f"[SKIP] No claim button found for: {shift['info'][:50]}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Claim failed: {str(e)[:50]}")
            return False
    
    def handle_confirmation_dialogs(self):
        """Handle confirmation dialogs if they appear"""
        try:
            time.sleep(0.3)
            
            # Check for common dialog types
            dialog_selectors = [
                "div[role='dialog']",
                ".modal",
                ".popup",
                ".dialog",
                ".confirmation"
            ]
            
            for selector in dialog_selectors:
                try:
                    dialog = self.page.query_selector(selector)
                    if dialog and dialog.is_visible():
                        # Look for confirm buttons
                        confirm_selectors = [
                            "button:has-text('OK')",
                            "button:has-text('Confirm')",
                            "button:has-text('Yes')",
                            "button:has-text('Agree')",
                            "button[type='submit']"
                        ]
                        
                        for confirm_selector in confirm_selectors:
                            try:
                                confirm_btn = dialog.query_selector(confirm_selector)
                                if confirm_btn and confirm_btn.is_visible():
                                    confirm_btn.click(delay=10)
                                    time.sleep(0.3)
                                    return
                            except:
                                continue
                except:
                    continue
        except:
            pass
    
    def show_statistics(self):
        """Show overall statistics about seen shifts"""
        if not self.seen_shifts:
            return
            
        total_shifts = len(self.seen_shifts)
        
        # Count by status
        status_counts = {}
        for shift_data in self.seen_shifts.values():
            status = shift_data['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Total unique shifts seen: {total_shifts}")
        print(f"   Currently tracking: {len(self.seen_shifts)} shifts in memory")
        
        if status_counts:
            print(f"   Breakdown:")
            for status, count in status_counts.items():
                print(f"     {status}: {count}")
    
    def restart_browser(self):
        """Restart browser session"""
        print("🔄 Restarting browser...")
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            self.page = self.browser.new_page()
            self.page.set_default_timeout(30000)
            
            print("🌐 Loading page...")
            self.page.goto(self.url, wait_until="load", timeout=30000)
            time.sleep(3)
            print("✅ Browser restarted")
            
        except Exception as e:
            print(f"❌ Failed to restart: {e}")
            raise
    
    def stop(self):
        """Stop the auto-claimer"""
        print("\n🛑 Stopping Auto-Claimer...")
        print(f"📊 Final Statistics:")
        print(f"   Total shifts seen: {len(self.seen_shifts)}")
        print(f"   Total shifts claimed: {len(self.claimed_shifts)}")
        
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass
        print("✅ Auto-claimer stopped. All tracking data cleared.")

# ================= MAIN =================
def main():
    print("\n" + "="*60)
    print("🚀 SHIFT AUTO-CLAIMER - WITH SEEN SHIFT TRACKING")
    print("="*60)
    print(f"🎯 Target: Deputy Shift Roster")
    print("⚡ Features:")
    print("   • Tracks seen shifts in memory")
    print("   • Only processes NEW shifts each iteration")
    print("   • Much faster scanning after first pass")
    print("   • Shows real-time statistics")
    print("   • Auto-claims available new shifts")
    print("\n📝 Starting... (Press Ctrl+C to stop)\n")
    
    claimer = ShiftAutoClaimer(SHIFT_URL)
    
    try:
        claimer.start()
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        claimer.stop()

if __name__ == "__main__":
    main()