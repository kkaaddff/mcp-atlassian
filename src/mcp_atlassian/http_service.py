"""HTTP Service wrapper for Confluence with configurable base URL and request-based authentication."""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from mcp_atlassian.confluence import ConfluenceFetcher, ConfluenceConfig
from mcp_atlassian.utils.oauth import OAuthConfig, BYOAccessTokenOAuthConfig

logger = logging.getLogger("mcp-confluence.http_service")


class ConfluenceAuthRequest(BaseModel):
    """Request model for Confluence operations with authentication."""
    
    base_url: str = Field(..., description="Base URL for Confluence instance")
    auth_type: str = Field(..., description="Authentication type: 'basic', 'pat', or 'oauth'")
    username: Optional[str] = Field(None, description="Username for basic auth")
    api_token: Optional[str] = Field(None, description="API token for basic auth")
    personal_token: Optional[str] = Field(None, description="Personal access token for Server/DC")
    oauth_token: Optional[str] = Field(None, description="OAuth access token")
    cloud_id: Optional[str] = Field(None, description="Cloud ID for OAuth")
    operation: str = Field(..., description="Operation to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the operation")


class ConfluenceAuthService:
    """Service for handling Confluence operations with request-based authentication."""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp-confluence.auth_service")
    
    async def create_config_from_request(self, request: ConfluenceAuthRequest) -> ConfluenceConfig:
        """Create ConfluenceConfig from request parameters."""
        
        # Determine authentication configuration
        oauth_config = None
        
        if request.auth_type == "oauth":
            if not request.oauth_token:
                raise HTTPException(status_code=400, detail="OAuth token is required for OAuth authentication")
            
            if not request.cloud_id:
                raise HTTPException(status_code=400, detail="Cloud ID is required for OAuth authentication")
            
            # Create minimal OAuth config for user-provided token
            oauth_config = BYOAccessTokenOAuthConfig(
                client_id="",
                client_secret="",
                redirect_uri="",
                scope="",
                access_token=request.oauth_token,
                refresh_token=None,
                expires_at=None,
                cloud_id=request.cloud_id,
            )
        
        elif request.auth_type == "basic":
            if not request.username or not request.api_token:
                raise HTTPException(status_code=400, detail="Username and API token are required for basic auth")
        
        elif request.auth_type == "pat":
            if not request.personal_token:
                raise HTTPException(status_code=400, detail="Personal token is required for PAT authentication")
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported auth type: {request.auth_type}")
        
        # Create ConfluenceConfig
        config = ConfluenceConfig(
            url=request.base_url,
            auth_type=request.auth_type,
            username=request.username,
            api_token=request.api_token,
            personal_token=request.personal_token,
            oauth_config=oauth_config,
            ssl_verify=True,  # Default to SSL verification
        )
        
        # Validate configuration
        if not config.is_auth_configured():
            raise HTTPException(status_code=400, detail="Authentication configuration is incomplete")
        
        return config
    
    async def execute_operation(self, config: ConfluenceConfig, operation: str, parameters: Dict[str, Any]) -> Any:
        """Execute Confluence operation with the given configuration."""
        
        try:
            # Create ConfluenceFetcher with the configuration
            fetcher = ConfluenceFetcher(config=config)
            
            # Execute the requested operation
            if operation == "get_page":
                page_id = parameters.get("page_id")
                if not page_id:
                    raise HTTPException(status_code=400, detail="page_id is required for get_page operation")
                return await fetcher.get_page_by_id(page_id)
            
            elif operation == "search_pages":
                query = parameters.get("query", "")
                space_key = parameters.get("space_key")
                limit = parameters.get("limit", 50)
                return await fetcher.search_content(query, space_key=space_key, limit=limit)
            
            elif operation == "get_space":
                space_key = parameters.get("space_key")
                if not space_key:
                    raise HTTPException(status_code=400, detail="space_key is required for get_space operation")
                return await fetcher.get_space(space_key)
            
            elif operation == "list_spaces":
                limit = parameters.get("limit", 50)
                return await fetcher.get_spaces(limit=limit)
            
            elif operation == "create_page":
                space_key = parameters.get("space_key")
                title = parameters.get("title")
                content = parameters.get("content")
                parent_id = parameters.get("parent_id")
                
                if not all([space_key, title, content]):
                    raise HTTPException(status_code=400, detail="space_key, title, and content are required for create_page operation")
                
                return await fetcher.create_page(space_key, title, content, parent_id)
            
            elif operation == "update_page":
                page_id = parameters.get("page_id")
                title = parameters.get("title")
                content = parameters.get("content")
                version = parameters.get("version")
                
                if not page_id:
                    raise HTTPException(status_code=400, detail="page_id is required for update_page operation")
                
                return await fetcher.update_page(page_id, title, content, version)
            
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported operation: {operation}")
        
        except Exception as e:
            self.logger.error(f"Error executing operation {operation}: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Initialize FastAPI app
app = FastAPI(
    title="Confluence HTTP Service",
    description="HTTP service for Confluence operations with configurable base URL and request-based authentication",
    version="1.0.0"
)

# Initialize auth service
auth_service = ConfluenceAuthService()


@app.post("/confluence/execute")
async def execute_confluence_operation(request: ConfluenceAuthRequest):
    """Execute a Confluence operation with the provided authentication."""
    
    try:
        # Create configuration from request
        config = await auth_service.create_config_from_request(request)
        
        # Execute the operation
        result = await auth_service.execute_operation(config, request.operation, request.parameters)
        
        return JSONResponse(content={"success": True, "data": result})
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in execute_confluence_operation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "confluence-http-service"}


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Confluence HTTP Service",
        "version": "1.0.0",
        "description": "HTTP service for Confluence operations with configurable base URL and request-based authentication",
        "endpoints": {
            "POST /confluence/execute": "Execute Confluence operations",
            "GET /health": "Health check",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)