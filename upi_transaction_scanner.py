"""
UPI Transaction Email Scanner
Scans Gmail for UPI transactions and adds them to finance database
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from Project_jan.upi_transaction_parser import get_upi_parser, UPITransaction

class UPITransactionScanner:
    """Scans Gmail for UPI transactions"""
    
    def __init__(self):
        self.parser = get_upi_parser()
    
    def scan_and_import(self, user_id: str, hours_ago: int = 168, max_emails: int = 50) -> Dict[str, Any]:
        """
        Scan Gmail for UPI transactions and import to database
        
        Args:
            user_id: User identifier
            hours_ago: How far back to scan (default: 7 days)
            max_emails: Maximum emails to process
            
        Returns:
            Dict with scan results
        """
        from db_.neo4j_finance import get_finance_db
        from email_service import get_email_service
        
        # Get email service
        email_service = get_email_service()
        
        # Authenticate
        if not email_service.authenticate():
            return {
                "success": False,
                "error": "Gmail authentication failed",
                "message": "Please set up Gmail API credentials"
            }
        
        # Fetch recent emails
        print(f"[UPIScanner] Fetching emails from last {hours_ago} hours...")
        emails = email_service.fetch_recent_emails(
            max_results=max_emails,
            hours_ago=hours_ago
        )
        
        if not emails:
            return {
                "success": True,
                "total_emails": 0,
                "transactions_found": 0,
                "transactions_imported": 0,
                "message": "No emails found"
            }
        
        # Parse UPI transactions
        transactions: List[UPITransaction] = []
        
        for email in emails:
            if self.parser.is_upi_email(email.subject, email.sender, email.body):
                transaction = self.parser.parse_transaction(
                    email.subject,
                    email.body,
                    email.sender,
                    email.received_date
                )
                
                if transaction:
                    transactions.append(transaction)
        
        print(f"[UPIScanner] ✅ Found {len(transactions)} UPI transactions")
        
        if not transactions:
            return {
                "success": True,
                "total_emails": len(emails),
                "transactions_found": 0,
                "transactions_imported": 0,
                "message": "No UPI transactions found"
            }
        
        # Import to database
        finance_db = get_finance_db()
        imported_count = 0
        
        for transaction in transactions:
            # Convert to finance DB format
            transaction_dict = {
                "amount": transaction.amount,
                "category": transaction.category,
                "description": f"{transaction.merchant or 'UPI'} ({transaction.transaction_type})",
                "type": "expense" if transaction.transaction_type == "DEBIT" else "income",
                "payment_mode": transaction.payment_mode,
                "date": transaction.date
            }
            
            # Add to database
            try:
                success = finance_db.add_transaction(user_id, transaction_dict)
                if success:
                    imported_count += 1
                    print(f"[UPIScanner] ✅ Imported: ₹{transaction.amount} - {transaction.merchant}")
            except Exception as e:
                print(f"[UPIScanner] ⚠️ Failed to import transaction: {e}")
        
        return {
            "success": True,
            "total_emails": len(emails),
            "transactions_found": len(transactions),
            "transactions_imported": imported_count,
            "transactions": [t.model_dump() for t in transactions[:10]],  # Show first 10
            "message": f"Imported {imported_count} UPI transactions"
        }
    
    def scan_single_email(self, email_text: str, subject: str = "", sender: str = "") -> Dict[str, Any]:
        """
        Parse a single email forwarded by user
        
        Args:
            email_text: Email body
            subject: Email subject
            sender: Email sender
            
        Returns:
            Parsed transaction or error
        """
        # Check if it's a UPI email
        if not self.parser.is_upi_email(subject, sender, email_text):
            return {
                "success": False,
                "error": "not_upi_email",
                "message": "This doesn't appear to be a UPI transaction email"
            }
        
        # Parse transaction
        transaction = self.parser.parse_transaction(
            subject,
            email_text,
            sender,
            datetime.now()
        )
        
        if not transaction:
            return {
                "success": False,
                "error": "parse_failed",
                "message": "Could not parse transaction from this email"
            }
        
        return {
            "success": True,
            "transaction": transaction.model_dump()
        }


# Singleton
_upi_scanner = None


def get_upi_scanner() -> UPITransactionScanner:
    """Get or create UPI scanner singleton"""
    global _upi_scanner
    if _upi_scanner is None:
        _upi_scanner = UPITransactionScanner()
        print("[UPIScanner] ✅ Singleton initialized")
    return _upi_scanner