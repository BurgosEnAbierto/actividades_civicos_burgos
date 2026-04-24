"""Tests para src.task_wrapper.main"""
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest

from src.task_wrapper.main import load_config, run_wrapper, notify_results


class TestLoadConfig:
    """Prueba la carga de configuración"""

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

    def test_load_config_uses_env_variables(self, monkeypatch):
        """Prueba que load_config respeta variables de entorno"""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://hooks.discord.com/test")

        config = load_config(config_path=None)

        assert config["log_level"] == "DEBUG"
        assert config["discord_webhook"] == "https://hooks.discord.com/test"

    def test_load_config_creates_log_dir(self, tmp_path):
        """Prueba que load_config crea el directorio de logs"""
        os.chdir(tmp_path)
        
        config = load_config(config_path=None)
        
        assert config["log_dir"].exists()


class TestRunWrapper:
    """Prueba el wrapper de ejecución"""

    @patch("src.task_wrapper.main.run_scraper")
    @patch("src.task_wrapper.main.run_orchestrator")
    def test_run_wrapper_scraper_success_no_new_links(
        self, mock_orchestrator, mock_scraper
    ):
        """Prueba que run_wrapper no ejecuta orchestrator sin enlaces nuevos"""
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
            "month": "202601",
            "total_links_found": 5,
            "new_links_count": 0,
            "new_links": [],
            "links_file": Path("docs/data/202601/links.json"),
            "error": None,
        }

        result = run_wrapper(config, run_orchestrator_if_no_new=False)

        assert result["success"] is True
        assert result["scraper"]["success"] is True
        assert result["orchestrator"] is None
        mock_scraper.assert_called_once()
        mock_orchestrator.assert_not_called()

    @patch("src.task_wrapper.main.run_scraper")
    @patch("src.task_wrapper.main.run_orchestrator")
    def test_run_wrapper_scraper_success_with_new_links(
        self, mock_orchestrator, mock_scraper
    ):
        """Prueba que run_wrapper ejecuta orchestrator cuando scraper encuentra links nuevos"""
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
            "month": "202601",
            "total_links_found": 5,
            "new_links_count": 2,
            "new_links": [{"url": "link1"}, {"url": "link2"}],
            "links_file": Path("docs/data/202601/links.json"),
            "error": None,
        }

        mock_orchestrator.return_value = {
            "success": True,
            "month": "202601",
            "civicos_processed": 3,
            "civicos_with_errors": 0,
            "total_activities": 45,
            "errors": [],
            "activities_file": Path("docs/data/202601/actividades.json"),
        }

        result = run_wrapper(config, run_orchestrator_if_no_new=False)

        assert result["success"] is True
        assert result["scraper"]["success"] is True
        assert result["orchestrator"]["success"] is True
        mock_scraper.assert_called_once()
        mock_orchestrator.assert_called_once()

    @patch("src.task_wrapper.main.run_scraper")
    @patch("src.task_wrapper.main.run_orchestrator")
    def test_run_wrapper_force_orchestrator(self, mock_orchestrator, mock_scraper):
        """Prueba que run_orchestrator_if_no_new fuerza la ejecución del orchestrator"""
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
            "month": "202601",
            "total_links_found": 5,
            "new_links_count": 0,
            "new_links": [],
            "links_file": Path("docs/data/202601/links.json"),
            "error": None,
        }
        
        mock_orchestrator.return_value = {
            "success": True,
            "month": "202601",
            "civicos_processed": 3,
            "civicos_with_errors": 0,
            "total_activities": 45,
            "errors": [],
            "activities_file": Path("docs/data/202601/actividades.json"),
        }

        result = run_wrapper(config, run_orchestrator_if_no_new=True)

        assert result["success"] is True
        assert result["orchestrator"]["success"] is True
        mock_orchestrator.assert_called_once()

    @patch("src.task_wrapper.main.run_scraper")
    def test_run_wrapper_scraper_fails(self, mock_scraper):
        """Prueba que run_wrapper retorna failure cuando scraper falla"""
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

        result = run_wrapper(config, run_orchestrator_if_no_new=False)

        assert result["success"] is False
        assert len(result["errors"]) > 0


class TestNotifyResults:
    """Prueba la formación de notificaciones"""

    @patch("src.task_wrapper.main.notify")
    def test_notify_results_calls_notify_with_correct_params(self, mock_notify):
        """Prueba que notify_results llama a notify() con los parámetros correctos"""
        result = {
            "success": True,
            "scraper": {
                "success": True,
                "month": "202601",
                "total_links_found": 5,
                "new_links_count": 2,
            },
            "orchestrator": {
                "success": True,
                "month": "202601",
                "civicos_processed": 3,
                "total_activities": 45,
                "civicos_with_errors": 0,
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
        
        notify_results(result, config)
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args.kwargs
        assert call_kwargs["month"] == "202601"
        assert call_kwargs["status"] == "success"
        assert call_kwargs["scraped_new"] == 2

    @patch("src.task_wrapper.main.notify")
    def test_notify_results_extracts_month_from_scraper(self, mock_notify):
        """Prueba que notify_results extrae month del scraper result"""
        result = {
            "success": True,
            "scraper": {
                "success": True,
                "month": "202601",
                "total_links_found": 5,
                "new_links_count": 2,
            },
            "orchestrator": None,
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
        
        notify_results(result, config)
        
        call_kwargs = mock_notify.call_args.kwargs
        assert call_kwargs["month"] == "202601"

    @patch("src.task_wrapper.main.notify")
    def test_notify_results_extracts_month_from_orchestrator(self, mock_notify):
        """Prueba que notify_results usa month del orchestrator si scraper es None"""
        result = {
            "success": True,
            "scraper": None,
            "orchestrator": {
                "success": True,
                "month": "202602",
                "civicos_processed": 3,
                "total_activities": 50,
                "civicos_with_errors": 0,
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
        
        notify_results(result, config)
        
        call_kwargs = mock_notify.call_args.kwargs
        assert call_kwargs["month"] == "202602"

    @patch("src.task_wrapper.main.notify")
    def test_notify_results_handles_error_status(self, mock_notify):
        """Prueba que notify_results envía status 'error' cuando falla"""
        result = {
            "success": False,
            "scraper": {
                "success": False,
                "month": None,
                "error": "Connection error",
            },
            "orchestrator": None,
            "errors": ["Scraper: Connection error"],
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
        
        notify_results(result, config)
        
        call_kwargs = mock_notify.call_args.kwargs
        assert call_kwargs["status"] == "error"
        assert len(call_kwargs["errors"]) > 0
