"""
UPI Transaction API Endpoints
Add to your FastAPI app to enable UPI transaction scanning
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

# Create router
upi_router = APIRouter(prefix="/upi", tags=["UPI Transactions"])


class UPIScanRequest(BaseModel):
    """Request model for UPI scanning"""
    user_id: str = "default_user"
    hours_ago: int = 168  # Default: 7 days
    max_emails: int = 50


class SingleEmailRequest(BaseModel):
    """Request model for single email parsing"""
    email_text: str
    subject: Optional[str] = ""
    sender: Optional[str] = ""
    user_id: str = "default_user"
    save_to_db: bool = True


@upi_router.post("/scan")
def scan_upi_transactions(request: UPIScanRequest):
    """
    Scan Gmail for UPI transactions and import to database
    
    **Features:**
    - Automatically detects UPI/payment emails
    - Parses transaction details (amount, merchant, date, etc.)
    - Categorizes transactions intelligently
    - Imports to your finance database
    
    **First time usage:** Will trigger Gmail OAuth flow
    
    Args:
        request: UPIScanRequest with scan parameters
        
    Returns:
        Scan results with imported transactions
        
    Example:
        POST /upi/scan
        {
            "user_id": "user123",
            "hours_ago": 168,  // 7 days
            "max_emails": 50
        }
    """
    try:
        from Project_jan.upi_transaction_scanner import get_upi_scanner
        
        scanner = get_upi_scanner()
        result = scanner.scan_and_import(
            user_id=request.user_id,
            hours_ago=request.hours_ago,
            max_emails=request.max_emails
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "UPI scan failed")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"UPI scan failed: {str(e)}"
        )


@upi_router.post("/parse-email")
def parse_upi_email(request: SingleEmailRequest):
    """
    Parse a single UPI transaction email
    
    **Use case:** User forwards/pastes a payment email
    
    Args:
        request: SingleEmailRequest with email details
        
    Returns:
        Parsed transaction details
        
    Example:
        POST /upi/parse-email
        {
            "email_text": "Rs. 150 debited to swiggy@paytm...",
            "subject": "Account debited",
            "sender": "alerts@hdfcbank.net",
            "user_id": "user123",
            "save_to_db": true
        }
    """
    try:
        from Project_jan.upi_transaction_scanner import get_upi_scanner
        from db_.neo4j_finance import get_finance_db
        
        scanner = get_upi_scanner()
        result = scanner.scan_single_email(
            email_text=request.email_text,
            subject=request.subject,
            sender=request.sender
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Could not parse email")
            )
        
        # Optionally save to database
        if request.save_to_db:
            transaction = result["transaction"]
            
            transaction_dict = {
                "amount": transaction["amount"],
                "category": transaction["category"],
                "description": f"{transaction.get('merchant', 'UPI')} ({transaction['transaction_type']})",
                "type": "expense" if transaction["transaction_type"] == "DEBIT" else "income",
                "payment_mode": transaction["payment_mode"],
                "date": transaction["date"]
            }
            
            finance_db = get_finance_db()
            success = finance_db.add_transaction(request.user_id, transaction_dict)
            
            result["saved_to_db"] = success
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email parsing failed: {str(e)}"
        )


@upi_router.get("/status")
def get_upi_scanner_status():
    """
    Check if UPI scanner is configured
    
    Returns:
        Status information
    """
    try:
        from email_service import GMAIL_AVAILABLE
        from Project_jan.upi_transaction_scanner import get_upi_scanner
        
        if not GMAIL_AVAILABLE:
            return {
                "configured": False,
                "message": "Gmail API not available",
                "help": "Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            }
        
        scanner = get_upi_scanner()
        
        return {
            "configured": True,
            "message": "UPI scanner ready",
            "features": [
                "Automatic UPI email detection",
                "Multi-bank support (HDFC, ICICI, SBI, Axis, Kotak, etc.)",
                "Payment app support (Paytm, PhonePe, GPay)",
                "Intelligent categorization",
                "Automatic database import"
            ]
        }
        
    except Exception as e:
        return {
            "configured": False,
            "error": str(e)
        }


# ============================================
# Integration Instructions
# ============================================

"""
TO INTEGRATE: Add to backend/app/main.py

1. Import the router:
   from upi_api import upi_router

2. Include the router in your app:
   app.include_router(upi_router)

3. The endpoints will be available at:
   - POST /upi/scan - Scan Gmail for UPI transactions
   - POST /upi/parse-email - Parse a single forwarded email
   - GET /upi/status - Check scanner status

4. Example usage from frontend:

   // Scan inbox for UPI transactions
   const response = await fetch('http://localhost:8000/upi/scan', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       user_id: 'user123',
       hours_ago: 168,  // 7 days
       max_emails: 50
     })
   });
   const data = await response.json();
   console.log(`Imported ${data.transactions_imported} transactions`);

   // Parse a single forwarded email
   const response = await fetch('http://localhost:8000/upi/parse-email', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       email_text: userForwardedEmail,
       user_id: 'user123',
       save_to_db: true
     })
   });

5. IMPORTANT: Make sure you have:
   - Gmail API credentials (credentials.json)
   - OAuth consent screen configured
   - Gmail API enabled in Google Cloud Console

6. File structure:
   /home/claude/
   ├── upi_transaction_parser.py  (Already created)
   ├── upi_transaction_scanner.py (Already created)
   └── upi_api.py                 (This file)

7. Copy these files to your project:
   - Move them to your project root
   - Update imports in app/main.py
"""