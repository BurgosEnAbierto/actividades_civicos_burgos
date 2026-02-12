from pathlib import Path
from unittest.mock import patch, Mock

from src.downloader.download_pdf import download_pdf


@patch("src.downloader.download_pdf.requests.get")
def test_download_pdf(mock_get, tmp_path):
    mock_response = Mock()
    mock_response.content = b"PDFDATA"
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    pdf = download_pdf("https://example.com/test.pdf", tmp_path)

    assert pdf.exists()
    assert pdf.read_bytes() == b"PDFDATA"
