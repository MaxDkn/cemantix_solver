import re
import time
import selenium
from random import uniform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Tuple, Dict, Optional


class CemantixInterface:
    def __init__(self, url: str = "https://cemantix.certitudes.org", headless: bool = True, debug_mode: bool = False):
        """
        args:
            url: The URL of the Cemantix game. (default: "https://cemantix.certitudes.org")
            headless: If True, run the browser in headless mode (no GUI).
            debug_mode: If True, adds manual pauses for debugging
        """
        self.url = url
        self.debug_mode = debug_mode

        self.options = webdriver.ChromeOptions()
        if headless:
            self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)

        self.driver = None
        self.wait = None
        self.is_connected = self._connect()
        self.history = []

    def debug_pause(self, message: str = ""):
        if self.debug_mode:
            input(f"DEBUG PAUSE: {message} - Appuyez sur Entrée pour continuer...")

    def _handle_consent_popup(self) -> bool:
        if not self.is_connected:
            return False
        try:
            time.sleep(uniform(0.5, 1.5))            
            selector = "button[class*='consent']"
            
            button = self.driver.find_element(By.CSS_SELECTOR, selector)
            
            if button.is_displayed():
                button.click()
                time.sleep(uniform(0.5, 1.5))
                return True

            # Si le bouton n'est pas trouvé, essayer de fermer la popup avec la touche Échap
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(uniform(0.5, 1.5))            
            return True
            
        except Exception as e:
            return False

    def _connect(self) -> bool:
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.wait = WebDriverWait(self.driver, 10)
            self.driver.get(self.url)
            
            self._handle_consent_popup()
            
            try:
                self.wait.until(EC.presence_of_element_located((By.ID, "guess")))
                return True
            except TimeoutException:
                return False
                
        except Exception as e:
            return False

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
            self.is_connected = False
        return self

    def submit_guess(self, guess: str) -> bool:
        if not self.is_connected:
            return False
        try:
            input_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "guess"))
            )
            input_field.clear()
            input_field.send_keys(guess)
                        
            time.sleep(uniform(0.5, 1.5))
            input_field.send_keys(Keys.RETURN)
            time.sleep(uniform(0.5, 1.5))
            return True
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error submitting guess: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    
    def get_word_history(self) -> List[Dict]:
        if not self.is_connected:
            print("Not connected to Cemantix.")
            return []
        
        history = []
        try:
            table = self.driver.find_element(By.ID, "guesses")
            rows = table.find_elements(By.TAG_NAME, "tr")

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                input(cells)
                if len(cells) >= 3:
                    try:
                        numero = int(cells[0].text.strip())
                        mot = cells[1].text.strip()

                        score_text = cells[2].text.strip().replace(',', '.')
                        score = float(score_text) if score_text else None

                        progression_text = cells[3].text.strip() if len(cells) > 3 else ""

                        entry = {
                            'numero': numero,
                            'mot': mot,
                            'score': score,
                            'progression': progression_text
                        }

                        history.append(entry)

                    except (ValueError, IndexError) as e:
                        print(f"Erreur de parsing d'une ligne: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error getting word history: {e}")
            return []
            
        self.history = history
        return history
    
    def wait_and_inspect(self, seconds: int = 5):
        if self.debug_mode:
            print(f"Pause de {seconds} secondes pour inspection...")
            time.sleep(seconds)
if __name__ == "__main__":
    print(f"Selenium version: {selenium.__version__}")
    
    driver = CemantixInterface(headless=False, debug_mode=True)
    
    if driver.is_connected:
        driver.submit_guess("papa")
        driver.wait_and_inspect(3)
        print("Historique:", driver.get_word_history())
    input('Appuyez sur Entrée pour quitter...')
    driver.close()
    