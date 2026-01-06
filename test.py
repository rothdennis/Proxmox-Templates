import unittest
import json
import urllib.request
import urllib.error
from pathlib import Path


class TestImageURLs(unittest.TestCase):
    """Test that all image URLs in images.json are accessible."""
    
    @classmethod
    def setUpClass(cls):
        """Load the configuration file once for all tests."""
        config_path = Path(__file__).parent / 'images.json'
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            cls.config = json.load(f)
        
        cls.images = cls.config['images']
        cls.timeout = 5
        cls.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    def test_config_file_loaded(self):
        """Test that the configuration file has distributions."""
        self.assertTrue(len(self.images) > 0, 
                       "Configuration file should have at least one distribution")
    
    def test_all_urls_accessible(self):
        """Test that all URLs in the configuration are accessible."""
        failed_urls = []
        
        for distro_name in self.images:
            for version_dict in self.images[distro_name]:
                # Each version_dict is like {"3.22": "https://..."}
                for version, url in version_dict.items():
                    with self.subTest(distribution=distro_name, version=version, url=url):
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
                                'distribution': distro_name,
                                'version': version,
                                'url': url,
                                'error': f"HTTP {e.code}"
                            })
                            self.fail(f"HTTP error {e.code} for {distro_name} {version}")
                        except urllib.error.URLError as e:
                            failed_urls.append({
                                'distribution': distro_name,
                                'version': version,
                                'url': url,
                                'error': f"URL Error: {e.reason}"
                            })
                            self.fail(f"URL error: {e.reason}")
                        except Exception as e:
                            failed_urls.append({
                                'distribution': distro_name,
                                'version': version,
                                'url': url,
                                'error': str(e)
                            })
                            self.fail(f"Unexpected error: {str(e)}")
        
        # Store failed URLs as class attribute for tearDown reporting
        self.__class__.failed_urls = failed_urls
    
    def test_each_distribution_has_urls(self):
        """Test that each distribution has at least one version/URL."""
        for distro_name in self.images:
            with self.subTest(distribution=distro_name):
                self.assertTrue(len(self.images[distro_name]) > 0,
                              f"Distribution '{distro_name}' should have at least one version")
    
    @classmethod
    def tearDownClass(cls):
        """Print summary of failed URLs if any."""
        if hasattr(cls, 'failed_urls') and cls.failed_urls:
            print("\n" + "="*80)
            print("FAILED URL SUMMARY")
            print("="*80)
            for failure in cls.failed_urls:
                print(f"{failure['distribution']:30}{failure['version']:20}{failure['error']}")
            print("="*80)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)