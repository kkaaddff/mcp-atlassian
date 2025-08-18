"""
MCP Atlassian 测试的根 pytest 配置文件。

该模块提供跨所有测试模块共享的会话范围的 fixture 和实用程序。
它与新的测试实用程序框架集成，提供高效、可重用的测试 fixture。
"""

import pytest

from tests.utils.factories import (
    AuthConfigFactory,
    ConfluencePageFactory,
    ErrorResponseFactory,
    JiraIssueFactory,
)
from tests.utils.mocks import MockAtlassianClient, MockEnvironment


def pytest_addoption(parser):
    """为测试添加命令行选项。"""
    parser.addoption(
        "--use-real-data",
        action="store_true",
        default=False,
        help="运行使用真实 API 数据的测试（需要环境变量）",
    )


# ============================================================================
# 会话范围的配置 Fixture
# ============================================================================


@pytest.fixture(scope="session")
def session_auth_configs():
    """
    会话范围的 fixture，提供身份验证配置模板。

    该 fixture 在每个测试会话中计算一次，为基本身份验证和 PAT 场景
    提供标准的身份验证配置。

    返回：
        Dict[str, Dict[str, str]]: 身份验证配置模板
    """
    return {
        "basic_auth": AuthConfigFactory.create_basic_auth_config(),
        "pat_auth": AuthConfigFactory.create_pat_auth_config(),
        "jira_basic": {
            "url": "https://test.atlassian.net",
            "username": "test@example.com",
            "api_token": "test-jira-token",
        },
        "confluence_basic": {
            "url": "https://test.atlassian.net/wiki",
            "username": "test@example.com",
            "api_token": "test-confluence-token",
        },
    }


@pytest.fixture(scope="session")
def session_mock_data():
    """
    会话范围的 fixture，提供模拟数据模板。

    该 fixture 在每个会话中创建一次模拟数据模板，以避免为每个测试
    重新创建昂贵的模拟对象。

    返回：
        Dict[str, Any]: 各种 API 响应的模拟数据模板
    """
    return {
        "jira_issue": JiraIssueFactory.create(),
        "jira_issue_minimal": JiraIssueFactory.create_minimal(),
        "confluence_page": ConfluencePageFactory.create(),
        "api_error": ErrorResponseFactory.create_api_error(),
        "auth_error": ErrorResponseFactory.create_auth_error(),
        "jira_search_results": {
            "issues": [
                JiraIssueFactory.create("TEST-1"),
                JiraIssueFactory.create("TEST-2"),
                JiraIssueFactory.create("TEST-3"),
            ],
            "total": 3,
            "startAt": 0,
            "maxResults": 50,
        },
    }


# ============================================================================
# 环境和配置 Fixture
# ============================================================================


@pytest.fixture
def clean_environment():
    """
    提供无身份验证变量的干净环境的 fixture。

    这对于测试错误条件和配置验证很有用。
    """
    with MockEnvironment.clean_env() as env:
        yield env


@pytest.fixture
def pat_environment():
    """
    提供完整 PAT 环境设置的 fixture。

    这会设置所有必要的 PAT 环境变量，用于测试基于 PAT 的身份验证流程。
    """
    with MockEnvironment.pat_env() as env:
        yield env


@pytest.fixture
def basic_auth_environment():
    """
    提供基本身份验证环境设置的 fixture。

    这为 Jira 和 Confluence 设置用户名/令牌身份验证。
    """
    with MockEnvironment.basic_auth_env() as env:
        yield env


# ============================================================================
# 基于 Factory 的 Fixture
# ============================================================================


@pytest.fixture
def make_jira_issue():
    """
    用于创建具有可自定义属性的 Jira 问题的 factory fixture。

    返回：
        Callable: 创建 Jira 问题数据的 factory 函数

    示例：
        def test_issue_creation(make_jira_issue):
            issue = make_jira_issue(key="CUSTOM-123",
                                  fields={"priority": {"name": "High"}})
            assert issue["key"] == "CUSTOM-123"
    """
    return JiraIssueFactory.create


@pytest.fixture
def make_confluence_page():
    """
    用于创建具有可自定义属性的 Confluence 页面的 factory fixture。

    返回：
        Callable: 创建 Confluence 页面数据的 factory 函数

    示例：
        def test_page_creation(make_confluence_page):
            page = make_confluence_page(title="Custom Page",
                                      space={"key": "CUSTOM"})
            assert page["title"] == "Custom Page"
    """
    return ConfluencePageFactory.create


@pytest.fixture
def make_auth_config():
    """
    用于创建身份验证配置的 factory fixture。

    返回：
        Dict[str, Callable]: 不同身份验证类型的 factory 函数

    示例：
        def test_basic_config(make_auth_config):
            config = make_auth_config["basic"](username="custom-user")
            assert config["username"] == "custom-user"
    """
    return {
        "basic": AuthConfigFactory.create_basic_auth_config,
        "pat": AuthConfigFactory.create_pat_auth_config,
    }


@pytest.fixture
def make_api_error():
    """
    用于创建 API 错误响应的 factory fixture。

    返回：
        Callable: 创建错误响应数据的 factory 函数

    示例：
        def test_error_handling(make_api_error):
            error = make_api_error(status_code=404, message="Not Found")
            assert error["status"] == 404
    """
    return ErrorResponseFactory.create_api_error


# ============================================================================
# 模拟客户端 Fixture
# ============================================================================


@pytest.fixture
def mock_jira_client():
    """
    提供预配置模拟 Jira 客户端的 fixture。

    该客户端具有常见操作的合理默认值，但可以根据每个测试的需要进行自定义。

    返回：
        MagicMock: 配置的模拟 Jira 客户端
    """
    return MockAtlassianClient.create_jira_client()


@pytest.fixture
def mock_confluence_client():
    """
    提供预配置模拟 Confluence 客户端的 fixture。

    该客户端具有常见操作的合理默认值，但可以根据每个测试的需要进行自定义。

    返回：
        MagicMock: 配置的模拟 Confluence 客户端
    """
    return MockAtlassianClient.create_confluence_client()


# ============================================================================
# 兼容性 Fixture（保持向后兼容）
# ============================================================================


@pytest.fixture
def use_real_jira_data(request):
    """
    检查是否应该运行真实 Jira 数据测试。

    如果 --use-real-data 标志传递给 pytest，这将返回 True。

    注意：此 fixture 为向后兼容而维护。
    """
    return request.config.getoption("--use-real-data")


@pytest.fixture
def use_real_confluence_data(request):
    """
    检查是否应该运行真实 Confluence 数据测试。

    如果 --use-real-data 标志传递给 pytest，这将返回 True。

    注意：此 fixture 为向后兼容而维护。
    """
    return request.config.getoption("--use-real-data")


# ============================================================================
# 高级环境实用程序
# ============================================================================


@pytest.fixture
def env_var_manager():
    """
    提供在测试中管理环境变量的实用程序的 fixture。

    返回：
        MockEnvironment: 环境管理实用程序

    示例：
        def test_with_custom_env(env_var_manager):
            with env_var_manager.pat_env():
                # 测试 PAT 功能
                pass
    """
    return MockEnvironment


@pytest.fixture
def parametrized_auth_env(request):
    """
    用于测试不同身份验证环境的参数化 fixture。

    该 fixture 可以与 pytest.mark.parametrize 一起使用，以使用不同的身份验证设置
    测试相同的功能。

    示例：
        @pytest.mark.parametrize("parametrized_auth_env",
                               ["pat", "basic_auth"], indirect=True)
        def test_auth_scenarios(parametrized_auth_env):
            # 测试将为 PAT 和基本身份验证各运行一次
            pass
    """
    auth_type = request.param

    if auth_type == "pat":
        with MockEnvironment.pat_env() as env:
            yield env
    elif auth_type == "basic_auth":
        with MockEnvironment.basic_auth_env() as env:
            yield env
    elif auth_type == "clean":
        with MockEnvironment.clean_env() as env:
            yield env
    else:
        raise ValueError(f"未知的身份验证类型: {auth_type}")


# ============================================================================
# 会话验证和健康检查
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def validate_test_environment():
    """
    会话范围的 fixture，验证测试环境设置。

    该 fixture 自动运行，确保测试环境已正确配置以运行测试套件。
    """
    # 验证测试实用程序是否可导入
    try:
        import importlib.util

        # 检查模块是否可以导入
        for module_name in [
            "tests.fixtures.confluence_mocks",
            "tests.fixtures.jira_mocks",
            "tests.utils.base",
            "tests.utils.factories",
            "tests.utils.mocks",
        ]:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                pytest.fail(f"找不到模块: {module_name}")
    except ImportError as e:
        pytest.fail(f"导入测试实用程序失败: {e}")

    # 记录会话开始
    print("\n🧪 使用增强的 fixture 开始 MCP Atlassian 测试会话")

    yield

    # 记录会话结束
    print("\n✅ 完成 MCP Atlassian 测试会话")
