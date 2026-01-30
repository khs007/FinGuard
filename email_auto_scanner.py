"""
Email Scam Detection API Endpoints with Auto-Scanner
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

# Create router
email_router = APIRouter(prefix="/email", tags=["Email Scam Detection"])


class EmailScanRequest(BaseModel):
    """Request model for email scanning"""
    user_id: str = "default_user"
    hours_ago: int = 24
    max_emails: int = 10


class SingleEmailCheckRequest(BaseModel):
    """Request model for single email check"""
    email_text: str
    sender: Optional[str] = None
    subject: Optional[str] = None


class AutoScannerRegisterRequest(BaseModel):
    """Request model for registering user in auto-scanner"""
    user_id: str
    scan_interval_hours: int = 6
    max_emails: int = 10
    auto_scan: bool = True


@email_router.post("/scan")
def scan_emails(request: EmailScanRequest):
    """
    Scan recent emails for scams
    
    **First time usage**: Will trigger OAuth flow
    
    Args:
        request: EmailScanRequest with scan parameters
        
    Returns:
        Analysis results with scam detection
        
    Example:
        POST /email/scan
        {
            "user_id": "user123",
            "hours_ago": 24,
            "max_emails": 10
        }
    """
    try:
        from email_scam_handler import handle_email_scam_check
        
        result = handle_email_scam_check(
            user_id=request.user_id,
            hours_ago=request.hours_ago,
            max_emails=request.max_emails
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Email scan failed")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email scan failed: {str(e)}"
        )


@email_router.post("/check-single")
def check_single_email(request: SingleEmailCheckRequest):
    """
    Check a single email for scam indicators
    
    Use this when user pastes an email they received
    
    Args:
        request: SingleEmailCheckRequest with email details
        
    Returns:
        Scam analysis result
        
    Example:
        POST /email/check-single
        {
            "email_text": "Dear user, your account will be suspended...",
            "sender": "no-reply@suspicious.com",
            "subject": "Urgent: Verify your account"
        }
    """
    try:
        from email_scam_handler import handle_single_email_analysis
        
        result = handle_single_email_analysis(
            email_text=request.email_text,
            sender=request.sender,
            subject=request.subject
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Analysis failed")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email analysis failed: {str(e)}"
        )


@email_router.get("/status")
def get_email_service_status():
    """
    Check if Gmail API is configured and working
    
    Returns:
        Status information
    """
    try:
        from email_service import get_email_service, GMAIL_AVAILABLE
        
        if not GMAIL_AVAILABLE:
            return {
                "configured": False,
                "authenticated": False,
                "message": "Gmail API libraries not installed",
                "help": "Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            }
        
        service = get_email_service()
        authenticated = service.authenticate()
        
        return {
            "configured": True,
            "authenticated": authenticated,
            "user_email": service.user_email if authenticated else None,
            "message": "Ready" if authenticated else "Authentication required"
        }
        
    except Exception as e:
        return {
            "configured": False,
            "authenticated": False,
            "error": str(e)
        }


# ============================================
# AUTO-SCANNER ENDPOINTS (NEW)
# ============================================

@email_router.post("/auto-scan/register")
def register_auto_scan(request: AutoScannerRegisterRequest):
    """
    Register user for automatic email scanning
    
    **New Feature**: Automatically scans your inbox at regular intervals
    
    Args:
        request: AutoScannerRegisterRequest with configuration
        
    Returns:
        Registration confirmation
        
    Example:
        POST /email/auto-scan/register
        {
            "user_id": "user123",
            "scan_interval_hours": 6,
            "max_emails": 10,
            "auto_scan": true
        }
    """
    try:
        from email_auto_scanner import get_auto_scanner
        
        scanner = get_auto_scanner()
        scanner.register_user(
            user_id=request.user_id,
            scan_interval_hours=request.scan_interval_hours,
            max_emails=request.max_emails,
            auto_scan=request.auto_scan
        )
        
        return {
            "success": True,
            "message": f"Registered {request.user_id} for automatic scanning",
            "config": {
                "scan_interval_hours": request.scan_interval_hours,
                "max_emails": request.max_emails,
                "auto_scan": request.auto_scan
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )


@email_router.delete("/auto-scan/unregister/{user_id}")
def unregister_auto_scan(user_id: str):
    """
    Unregister user from automatic email scanning
    
    Args:
        user_id: User identifier
        
    Returns:
        Unregistration confirmation
    """
    try:
        from email_auto_scanner import get_auto_scanner
        
        scanner = get_auto_scanner()
        scanner.unregister_user(user_id)
        
        return {
            "success": True,
            "message": f"Unregistered {user_id} from automatic scanning"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unregistration failed: {str(e)}"
        )


@email_router.get("/auto-scan/status/{user_id}")
def get_auto_scan_status(user_id: str):
    """
    Get automatic scanning status for a user
    
    Args:
        user_id: User identifier
        
    Returns:
        Scan status and latest results
    """
    try:
        from email_auto_scanner import get_auto_scanner
        
        scanner = get_auto_scanner()
        status = scanner.get_user_status(user_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} not registered for auto-scanning"
            )
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Status check failed: {str(e)}"
        )


@email_router.post("/auto-scan/trigger/{user_id}")
async def trigger_manual_scan(user_id: str, background_tasks: BackgroundTasks):
    """
    Manually trigger an email scan for a user
    
    **Use this to force an immediate scan** outside the regular schedule
    
    Args:
        user_id: User identifier
        background_tasks: FastAPI background tasks
        
    Returns:
        Scan trigger confirmation
    """
    try:
        from email_auto_scanner import get_auto_scanner
        import asyncio
        
        scanner = get_auto_scanner()
        
        # Check if user is registered
        if user_id not in scanner.users:
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} not registered for auto-scanning"
            )
        
        # Trigger scan in background
        async def run_scan():
            await scanner.scan_user_emails(user_id)
        
        # Run in background
        asyncio.create_task(run_scan())
        
        return {
            "success": True,
            "message": f"Manual scan triggered for {user_id}",
            "note": "Scan running in background. Check status endpoint for results."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Manual scan failed: {str(e)}"
        )


@email_router.put("/auto-scan/config/{user_id}")
def update_auto_scan_config(user_id: str, config: AutoScannerRegisterRequest):
    """
    Update auto-scan configuration for a user
    
    Args:
        user_id: User identifier
        config: Updated configuration
        
    Returns:
        Update confirmation
    """
    try:
        from email_auto_scanner import get_auto_scanner
        
        scanner = get_auto_scanner()
        
        if user_id not in scanner.users:
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} not registered for auto-scanning"
            )
        
        scanner.update_user_config(
            user_id=user_id,
            scan_interval_hours=config.scan_interval_hours,
            max_emails=config.max_emails,
            auto_scan=config.auto_scan
        )
        
        return {
            "success": True,
            "message": f"Updated config for {user_id}",
            "config": scanner.users[user_id]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Config update failed: {str(e)}"
        )


# ============================================
# Integration Instructions
# ============================================

"""
TO INTEGRATE: Add to backend/app/main.py

1. Import the router:
   from app.email_api import email_router

2. Include the router in your app:
   app.include_router(email_router)

3. Start auto-scanner on app startup:
   
   @app.on_event("startup")
   async def startup_event():
       import asyncio
       from email_auto_scanner import start_background_scanner
       
       # Start scanner in background
       asyncio.create_task(start_background_scanner())

4. The endpoints will be available at:
   - POST /email/scan - Manual inbox scan
   - POST /email/check-single - Check single email
   - GET /email/status - Gmail API status
   - POST /email/auto-scan/register - Register for auto-scanning
   - DELETE /email/auto-scan/unregister/{user_id} - Unregister
   - GET /email/auto-scan/status/{user_id} - Check scan status
   - POST /email/auto-scan/trigger/{user_id} - Force manual scan
   - PUT /email/auto-scan/config/{user_id} - Update config

5. Example: Register a user for auto-scanning

   const response = await fetch('http://localhost:8000/email/auto-scan/register', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       user_id: 'user123',
       scan_interval_hours: 6,  // Scan every 6 hours
       max_emails: 10,
       auto_scan: true
     })
   });
"""