import unittest
import configparser
import urllib.request
import urllib.error
from pathlib import Path


class TestImageURLs(unittest.TestCase):
    """Test that all image URLs in images.toml are accessible."""
    
    @classmethod
    def setUpClass(cls):
        """Load the configuration file once for all tests."""
        cls.config = configparser.ConfigParser()
        config_path = Path(__file__).parent / 'images.toml'
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        cls.config.read(config_path)
        cls.timeout = 5
        cls.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    def test_config_file_loaded(self):
        """Test that the configuration file has sections."""
        self.assertTrue(len(self.config.sections()) > 0, 
                       "Configuration file should have at least one section")
    
    def test_all_urls_accessible(self):
        """Test that all URLs in the configuration are accessible."""
        failed_urls = []
        
        for section in self.config.sections():
            for key in self.config[section]:
                url = self.config[section][key]
                
                with self.subTest(distribution=section, version=key, url=url):
                    try:
                        request = urllib.request.Request(
                            url,
                            headers={'User-Agent': self.user_agent}
                        )
                        with urllib.request.urlopen(request, timeout=self.timeout) as response:
                            self.assertEqual(response.status, 200,
                                           f"URL returned status {response.status}")
                    except urllib.error.HTTPError as e:
                        failed_urls.append({
                            'section': section,
                            'key': key,
                            'url': url,
                            'error': f"HTTP {e.code}"
                        })
                        self.fail(f"HTTP error {e.code} for {section} {key}")
                    except urllib.error.URLError as e:
                        failed_urls.append({
                            'section': section,
                            'key': key,
                            'url': url,
                            'error': f"URL Error: {e.reason}"
                        })
                        self.fail(f"URL error: {e.reason}")
                    except Exception as e:
                        failed_urls.append({
                            'section': section,
                            'key': key,
                            'url': url,
                            'error': str(e)
                        })
                        self.fail(f"Unexpected error: {str(e)}")
        
        # Store failed URLs as class attribute for tearDown reporting
        self.__class__.failed_urls = failed_urls
    
    def test_each_section_has_urls(self):
        """Test that each section has at least one URL."""
        for section in self.config.sections():
            with self.subTest(section=section):
                self.assertTrue(len(self.config[section]) > 0,
                              f"Section '{section}' should have at least one URL")
    
    @classmethod
    def tearDownClass(cls):
        """Print summary of failed URLs if any."""
        if hasattr(cls, 'failed_urls') and cls.failed_urls:
            print("\n" + "="*80)
            print("FAILED URL SUMMARY")
            print("="*80)
            for failure in cls.failed_urls:
                print(f"{failure['section']:30}{failure['key']:20}{failure['error']}")
            print("="*80)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)