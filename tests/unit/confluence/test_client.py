"""ConfluenceClient 类的单元测试。"""

import os
from unittest.mock import MagicMock, patch

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.confluence.client import ConfluenceClient
from mcp_atlassian.confluence.config import ConfluenceConfig


def test_init_with_basic_auth():
    """测试使用基本身份验证配置初始化客户端。"""
    # 准备
    config = ConfluenceConfig(
        url="https://test.atlassian.net/wiki",
        auth_type="basic",
        username="test_user",
        api_token="test_token",
    )

    # 模拟 Confluence 类、ConfluencePreprocessor 和 configure_ssl_verification
    with (
        patch("mcp_atlassian.confluence.client.Confluence") as mock_confluence,
        patch(
            "mcp_atlassian.preprocessing.confluence.ConfluencePreprocessor"
        ) as mock_preprocessor,
        patch(
            "mcp_atlassian.confluence.client.configure_ssl_verification"
        ) as mock_configure_ssl,
    ):
        # 执行
        client = ConfluenceClient(config=config)

        # 断言
        mock_confluence.assert_called_once_with(
            url="https://test.atlassian.net/wiki",
            username="test_user",
            password="test_token",
            cloud=True,
            verify_ssl=True,
        )
        assert client.config == config
        assert client.confluence == mock_confluence.return_value
        assert client.preprocessor == mock_preprocessor.return_value

        # Verify SSL verification was configured
        mock_configure_ssl.assert_called_once_with(
            service_name="Confluence",
            url="https://test.atlassian.net/wiki",
            session=mock_confluence.return_value._session,
            ssl_verify=True,
        )


def test_init_with_token_auth():
    """测试使用令牌身份验证配置初始化客户端。"""
    # 准备
    config = ConfluenceConfig(
        url="https://confluence.example.com",
        auth_type="pat",
        personal_token="test_personal_token",
        ssl_verify=False,
    )

    # 模拟 Confluence 类、ConfluencePreprocessor 和 configure_ssl_verification
    with (
        patch("mcp_atlassian.confluence.client.Confluence") as mock_confluence,
        patch(
            "mcp_atlassian.preprocessing.confluence.ConfluencePreprocessor"
        ) as mock_preprocessor,
        patch(
            "mcp_atlassian.confluence.client.configure_ssl_verification"
        ) as mock_configure_ssl,
    ):
        # 执行
        client = ConfluenceClient(config=config)

        # 断言
        mock_confluence.assert_called_once_with(
            url="https://confluence.example.com",
            token="test_personal_token",
            cloud=False,
            verify_ssl=False,
        )
        assert client.config == config
        assert client.confluence == mock_confluence.return_value
        assert client.preprocessor == mock_preprocessor.return_value

        # Verify SSL verification was configured with ssl_verify=False
        mock_configure_ssl.assert_called_once_with(
            service_name="Confluence",
            url="https://confluence.example.com",
            session=mock_confluence.return_value._session,
            ssl_verify=False,
        )


def test_init_from_env():
    """Test initializing the client from environment variables."""
    # 准备
    with (
        patch(
            "mcp_atlassian.confluence.config.ConfluenceConfig.from_env"
        ) as mock_from_env,
        patch("mcp_atlassian.confluence.client.Confluence") as mock_confluence,
        patch("mcp_atlassian.preprocessing.confluence.ConfluencePreprocessor"),
        patch("mcp_atlassian.confluence.client.configure_ssl_verification"),
    ):
        mock_config = MagicMock()
        mock_from_env.return_value = mock_config

        # 执行
        client = ConfluenceClient()

        # 断言
        mock_from_env.assert_called_once()
        assert client.config == mock_config


def test_process_html_content():
    """Test the _process_html_content method."""
    # 准备
    with (
        patch("mcp_atlassian.confluence.client.ConfluenceConfig.from_env"),
        patch("mcp_atlassian.confluence.client.Confluence"),
        patch(
            "mcp_atlassian.preprocessing.confluence.ConfluencePreprocessor"
        ) as mock_preprocessor_class,
        patch("mcp_atlassian.confluence.client.configure_ssl_verification"),
    ):
        mock_preprocessor = mock_preprocessor_class.return_value
        mock_preprocessor.process_html_content.return_value = (
            "<p>HTML</p>",
            "Markdown",
        )

        client = ConfluenceClient()

        # 执行
        html, markdown = client._process_html_content("<p>Test</p>", "TEST")

        # 断言
        mock_preprocessor.process_html_content.assert_called_once_with(
            "<p>Test</p>", "TEST", client.confluence
        )
        assert html == "<p>HTML</p>"
        assert markdown == "Markdown"


def test_get_user_details_by_accountid():
    """Test the get_user_details_by_accountid method."""
    # 准备
    with (
        patch("mcp_atlassian.confluence.client.ConfluenceConfig.from_env"),
        patch("mcp_atlassian.confluence.client.Confluence") as mock_confluence_class,
        patch("mcp_atlassian.preprocessing.confluence.ConfluencePreprocessor"),
        patch("mcp_atlassian.confluence.client.configure_ssl_verification"),
    ):
        mock_confluence = mock_confluence_class.return_value
        mock_confluence.get_user_details_by_accountid.return_value = {
            "displayName": "Test User",
            "accountId": "123456",
            "emailAddress": "test@example.com",
            "active": True,
        }

        client = ConfluenceFetcher()

        # 执行
        user_details = client.get_user_details_by_accountid("123456")

        # 断言
        mock_confluence.get_user_details_by_accountid.assert_called_once_with(
            "123456", None
        )
        assert user_details["displayName"] == "Test User"
        assert user_details["accountId"] == "123456"
        assert user_details["emailAddress"] == "test@example.com"
        assert user_details["active"] is True

        # Test with expand parameter
        mock_confluence.get_user_details_by_accountid.reset_mock()
        mock_confluence.get_user_details_by_accountid.return_value = {
            "displayName": "Test User",
            "accountId": "123456",
            "status": "active",
        }

        user_details = client.get_user_details_by_accountid("123456", expand="status")

        mock_confluence.get_user_details_by_accountid.assert_called_once_with(
            "123456", "status"
        )
        assert user_details["status"] == "active"


def test_init_sets_proxies_and_no_proxy(monkeypatch):
    """Test that ConfluenceClient sets session proxies and NO_PROXY env var from config."""
    # Patch Confluence and its _session
    mock_confluence = MagicMock()
    mock_session = MagicMock()
    mock_session.proxies = {}  # Use a real dict for proxies
    mock_confluence._session = mock_session
    monkeypatch.setattr(
        "mcp_atlassian.confluence.client.Confluence", lambda **kwargs: mock_confluence
    )
    monkeypatch.setattr(
        "mcp_atlassian.confluence.client.configure_ssl_verification",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "mcp_atlassian.preprocessing.confluence.ConfluencePreprocessor",
        lambda **kwargs: MagicMock(),
    )

    # Patch environment
    monkeypatch.setenv("NO_PROXY", "")

    config = ConfluenceConfig(
        url="https://test.atlassian.net/wiki",
        auth_type="basic",
        username="user",
        api_token="token",
        http_proxy="http://proxy:8080",
        https_proxy="https://proxy:8443",
        socks_proxy="socks5://user:pass@proxy:1080",
        no_proxy="localhost,127.0.0.1",
    )
    client = ConfluenceClient(config=config)
    assert mock_session.proxies["http"] == "http://proxy:8080"
    assert mock_session.proxies["https"] == "https://proxy:8443"
    assert mock_session.proxies["socks"] == "socks5://user:pass@proxy:1080"
    assert os.environ["NO_PROXY"] == "localhost,127.0.0.1"


def test_init_no_proxies(monkeypatch):
    """Test that ConfluenceClient does not set proxies if not configured."""
    # Patch Confluence and its _session
    mock_confluence = MagicMock()
    mock_session = MagicMock()
    mock_session.proxies = {}  # Use a real dict for proxies
    mock_confluence._session = mock_session
    monkeypatch.setattr(
        "mcp_atlassian.confluence.client.Confluence", lambda **kwargs: mock_confluence
    )
    monkeypatch.setattr(
        "mcp_atlassian.confluence.client.configure_ssl_verification",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "mcp_atlassian.preprocessing.confluence.ConfluencePreprocessor",
        lambda **kwargs: MagicMock(),
    )

    config = ConfluenceConfig(
        url="https://test.atlassian.net/wiki",
        auth_type="basic",
        username="user",
        api_token="token",
    )
    client = ConfluenceClient(config=config)
    assert mock_session.proxies == {}
