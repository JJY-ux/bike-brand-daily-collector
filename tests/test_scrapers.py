"""Tests for brand scrapers."""

import pytest
from scrapers import BrandScraperFactory
from scrapers.brand_scrapers import GenericBrandScraper


class TestBrandScraperFactory:
    """Test brand scraper factory."""

    def test_create_generic_scraper(self):
        """Test creating a generic brand scraper."""
        scraper = BrandScraperFactory.create_scraper(
            brand_name="Test Brand",
            news_url="https://example.com/news",
            selector=".news-item",
        )

        assert scraper is not None
        assert isinstance(scraper, GenericBrandScraper)
        assert scraper.brand_name == "Test Brand"

    def test_create_trek_scraper(self):
        """Test creating Trek-specific scraper."""
        from scrapers.brand_scrapers import TrekScraper

        scraper = BrandScraperFactory.create_scraper(
            brand_name="Trek",
            news_url="https://newsroom.trekbikes.com/",
            selector=".article",
        )

        assert scraper is not None
        assert isinstance(scraper, TrekScraper)
        assert scraper.brand_name == "Trek"

    def test_scraper_attributes(self):
        """Test scraper has correct attributes."""
        scraper = BrandScraperFactory.create_scraper(
            brand_name="Giant",
            news_url="https://www.giant-bicycles.com/news",
            selector=".news-item",
            timeout=15,
            retry_times=5,
        )

        assert scraper.timeout == 15
        assert scraper.retry_times == 5
        assert scraper.brand_name == "Giant"
        assert scraper.news_url == "https://www.giant-bicycles.com/news"


class TestGenericBrandScraper:
    """Test generic brand scraper."""

    def test_clean_text(self):
        """Test text cleaning."""
        scraper = GenericBrandScraper(
            brand_name="Test",
            news_url="https://example.com",
            selector=".news",
        )

        # Test with extra spaces
        result = scraper._clean_text("  Hello   World  ")
        assert result == "Hello World"

        # Test with newlines
        result = scraper._clean_text("Line1\nLine2\nLine3")
        assert "Line1 Line2 Line3" in result

    def test_parse_date(self):
        """Test date parsing."""
        scraper = GenericBrandScraper(
            brand_name="Test",
            news_url="https://example.com",
            selector=".news",
        )

        # Test various date formats
        result = scraper._parse_date("2026-06-17")
        assert result is not None
        assert result.year == 2026

        result = scraper._parse_date("June 17, 2026")
        assert result is not None

        result = scraper._parse_date("Invalid Date")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
