"""Tests para src.scraper_runner.main"""
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.scraper_runner.main import load_config, run_scraper_only, notify_if_new_links


class TestScraperRunnerLoadConfig:
    """Prueba la carga de configuración en scraper_runner"""

    def test_load_config_returns_required_keys(self, monkeypatch, tmp_path):
        """Prueba que load_config retorna las claves requeridas"""
        monkeypatch.setenv("WORKSPACE", str(tmp_path / "workspace"))
        monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))

        config = load_config(config_path=None)

        assert "workspace" in config
        assert "data_dir" in config
        assert "log_dir" in config
        assert "log_level" in config
        assert "discord_webhook" in config
        assert "smtp" in config


class TestRunScraperOnly:
    """Prueba la ejecución del scraper"""

    @patch("src.scraper_runner.main.run_scraper")
    def test_run_scraper_only_success(self, mock_scraper):
        """Prueba que run_scraper_only retorna success cuando scraper funciona"""
        config = {
            "workspace": Path.cwd(),
            "data_dir": Path("docs/data"),
            "log_dir": Path("logs"),
            "log_level": "INFO",
            "discord_webhook": None,
            "smtp": {},
        }
        
        mock_scraper.return_value = {
            "success": True,
            "month": "202604",
            "total_links_found": 8,
            "new_links_count": 3,
            "new_links": [{"url": "link1"}, {"url": "link2"}, {"url": "link3"}],
            "links_file": Path("docs/data/202604/links.json"),
            "error": None,
        }

        result = run_scraper_only(config)

        assert result["success"] is True
        assert result["scraper"]["success"] is True
        assert result["scraper"]["new_links_count"] == 3
        mock_scraper.assert_called_once()

    @patch("src.scraper_runner.main.run_scraper")
    def test_run_scraper_only_fails(self, mock_scraper):
        """Prueba que run_scraper_only retorna failure cuando scraper falla"""
        config = {
            "workspace": Path.cwd(),
            "data_dir": Path("docs/data"),
            "log_dir": Path("logs"),
            "log_level": "INFO",
            "discord_webhook": None,
            "smtp": {},
        }
        
        mock_scraper.return_value = {
            "success": False,
            "month": None,
            "error": "Connection error",
        }

        result = run_scraper_only(config)

        assert result["success"] is False
        assert len(result["errors"]) > 0


class TestNotifyIfNewLinks:
    """Prueba las notificaciones condicionales"""

    @patch("src.scraper_runner.main.notify")
    def test_notify_if_new_links_sends_when_new_links_exist(self, mock_notify):
        """Prueba que notifica cuando hay enlaces nuevos"""
        result = {
            "success": True,
            "scraper": {
                "success": True,
                "month": "202604",
                "total_links_found": 8,
                "new_links_count": 3,
            },
            "errors": [],
        }
        
        config = {
            "discord_webhook": "https://hooks.discord.com/test",
            "smtp": {
                "host": None,
                "port": None,
                "user": None,
                "password": None,
                "from": None,
                "to": None,
            },
        }
        
        notify_if_new_links(result, config)
        
        # Debe llamar a notify una vez
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args.kwargs
        assert call_kwargs["scraped_new"] == 3

    @patch("src.scraper_runner.main.notify")
    def test_notify_if_new_links_silent_when_no_new_links(self, mock_notify):
        """Prueba que NO notifica cuando no hay enlaces nuevos"""
        result = {
            "success": True,
            "scraper": {
                "success": True,
                "month": "202604",
                "total_links_found": 8,
                "new_links_count": 0,
            },
            "errors": [],
        }
        
        config = {
            "discord_webhook": "https://hooks.discord.com/test",
            "smtp": {
                "host": None,
                "port": None,
                "user": None,
                "password": None,
                "from": None,
                "to": None,
            },
        }
        
        notify_if_new_links(result, config)
        
        # NO debe llamar a notify
        mock_notify.assert_not_called()

    @patch("src.scraper_runner.main.notify")
    def test_notify_if_new_links_includes_correct_info(self, mock_notify):
        """Prueba que la notificación incluye la información correcta"""
        result = {
            "success": True,
            "scraper": {
                "success": True,
                "month": "202604",
                "total_links_found": 10,
                "new_links_count": 2,
            },
            "errors": [],
        }
        
        config = {
            "discord_webhook": None,
            "smtp": {
                "host": None,
                "port": None,
                "user": None,
                "password": None,
                "from": None,
                "to": None,
            },
        }
        
        notify_if_new_links(result, config)
        
        call_kwargs = mock_notify.call_args.kwargs
        assert call_kwargs["month"] == "202604"
        assert call_kwargs["status"] == "success"
        assert call_kwargs["scraped_count"] == 10
        assert call_kwargs["scraped_new"] == 2
        assert "nuevos" in call_kwargs["title"].lower()
