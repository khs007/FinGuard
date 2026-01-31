"""
UPI Transaction Email Parser
Extracts transaction details from UPI notification emails
"""

import re
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


class UPITransaction(BaseModel):
    """Parsed UPI transaction from email"""
    amount: float = Field(..., description="Transaction amount in INR")
    transaction_type: str = Field(..., description="DEBIT or CREDIT")
    upi_id: Optional[str] = Field(None, description="UPI ID/VPA")
    merchant: Optional[str] = Field(None, description="Merchant/recipient name")
    transaction_id: Optional[str] = Field(None, description="UPI transaction reference ID")
    bank_name: Optional[str] = Field(None, description="Bank name")
    date: str = Field(..., description="Transaction date YYYY-MM-DD")
    time: Optional[str] = Field(None, description="Transaction time HH:MM")
    category: Optional[str] = Field("other", description="Inferred category")
    payment_mode: str = Field("upi", description="Payment mode")


class UPIEmailParser:
    """Parses UPI transaction emails from various banks"""
    
    # Common UPI email patterns
    UPI_KEYWORDS = [
        'upi', 'unified payments', 'bhim', 'paytm', 'gpay', 'google pay',
        'phonepe', 'amazon pay', 'imps', 'neft', 'rtgs'
    ]
    
    # Bank-specific sender patterns
    BANK_SENDERS = {
        'hdfc': ['alerts@hdfcbank.net', 'hdfcbank.net'],
        'icici': ['alerts@icicibank.com', 'icicibank.com'],
        'sbi': ['sbi.co.in', 'onlinesbi.com'],
        'axis': ['axisbank.com', 'axis.bank'],
        'kotak': ['kotak.com', 'kotakbank.com'],
        'paytm': ['paytm.com'],
        'phonepe': ['phonepe.com'],
        'gpay': ['google.com', 'payments-noreply@google.com']
    }
    
    def __init__(self):
        self.llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    
    def is_upi_email(self, subject: str, sender: str, body: str) -> bool:
        """Check if email is a UPI transaction notification"""
        subject_lower = subject.lower()
        body_lower = body.lower()
        sender_lower = sender.lower()
        
        # Check for UPI keywords
        has_upi_keyword = any(kw in subject_lower or kw in body_lower for kw in self.UPI_KEYWORDS)
        
        # Check for transaction amount pattern (Rs. or ₹)
        has_amount = bool(re.search(r'(?:rs\.?|₹|inr)\s*[\d,]+(?:\.\d{2})?', body_lower, re.IGNORECASE))
        
        # Check for known bank senders
        is_bank_sender = any(
            domain in sender_lower 
            for domains in self.BANK_SENDERS.values() 
            for domain in domains
        )
        
        return (has_upi_keyword and has_amount) or (is_bank_sender and has_amount)
    
    def parse_transaction(self, email_subject: str, email_body: str, sender: str, date: datetime) -> Optional[UPITransaction]:
        """
        Parse UPI transaction from email
        
        Args:
            email_subject: Email subject line
            email_body: Email body text
            sender: Email sender
            date: Email received date
            
        Returns:
            UPITransaction or None if parsing fails
        """
        # First try regex-based parsing (faster)
        transaction = self._parse_with_regex(email_subject, email_body, sender, date)
        
        if transaction:
            return transaction
        
        # Fallback to LLM-based parsing
        return self._parse_with_llm(email_subject, email_body, sender, date)
    
    def _parse_with_regex(self, subject: str, body: str, sender: str, date: datetime) -> Optional[UPITransaction]:
        """Fast regex-based parsing for common formats"""
        
        # Extract amount
        amount_pattern = r'(?:rs\.?|₹|inr)\s*([\d,]+(?:\.\d{2})?)'
        amount_match = re.search(amount_pattern, body, re.IGNORECASE)
        
        if not amount_match:
            return None
        
        amount_str = amount_match.group(1).replace(',', '')
        amount = float(amount_str)
        
        # Determine transaction type
        body_lower = body.lower()
        if any(word in body_lower for word in ['debited', 'debit', 'paid', 'spent', 'sent']):
            transaction_type = "DEBIT"
        elif any(word in body_lower for word in ['credited', 'credit', 'received', 'refund']):
            transaction_type = "CREDIT"
        else:
            transaction_type = "DEBIT"  # Default assumption
        
        # Extract UPI ID
        upi_pattern = r'(\w+@\w+)'
        upi_match = re.search(upi_pattern, body)
        upi_id = upi_match.group(1) if upi_match else None
        
        # Extract transaction ID
        txn_patterns = [
            r'(?:txn|transaction|ref)[\s:#]*([A-Z0-9]{10,})',
            r'upi ref[:\s]*([0-9]{12,})'
        ]
        transaction_id = None
        for pattern in txn_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                transaction_id = match.group(1)
                break
        
        # Extract merchant/recipient name
        merchant_patterns = [
            r'(?:to|from)\s+([A-Za-z\s]+)(?:\s+on|\s+via|\s+using)',
            r'(?:merchant|recipient):\s*([A-Za-z\s]+)',
        ]
        merchant = None
        for pattern in merchant_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                merchant = match.group(1).strip()
                break
        
        # Infer category from merchant name or description
        category = self._infer_category(merchant or subject)
        
        return UPITransaction(
            amount=amount,
            transaction_type=transaction_type,
            upi_id=upi_id,
            merchant=merchant,
            transaction_id=transaction_id,
            bank_name=self._extract_bank_name(sender),
            date=date.strftime("%Y-%m-%d"),
            time=date.strftime("%H:%M"),
            category=category,
            payment_mode="upi"
        )
    
    def _parse_with_llm(self, subject: str, body: str, sender: str, date: datetime) -> Optional[UPITransaction]:
        """LLM-based parsing for complex formats"""
        
        parse_prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are a UPI transaction email parser.

Extract transaction details from bank/payment app emails.

RULES:
- Amount is MANDATORY (look for Rs., ₹, INR followed by numbers)
- Transaction type: DEBIT (paid/sent/debited) or CREDIT (received/credited)
- Look for UPI ID pattern: name@bankname
- Extract merchant/recipient name
- Extract transaction reference/ID if available
- Infer category from merchant name or description:
  * FOOD: swiggy, zomato, restaurant names, food outlets
  * TRANSPORT: uber, ola, rapido, redbus, irctc
  * SHOPPING: amazon, flipkart, myntra, store names
  * ENTERTAINMENT: bookmyshow, netflix, spotify, prime
  * BILLS: electricity, water, jio, airtel, vi, reliance
  * HEALTH: pharmacy, practo, apollo, hospital names
  * EDUCATION: udemy, coursera, institution names
  * OTHER: anything else

Examples:
Subject: "Account debited"
Body: "Rs. 150 debited from your account to swiggy@paytm on 25 Jan 2025"
→ amount: 150, type: DEBIT, merchant: Swiggy, category: food, upi_id: swiggy@paytm

Subject: "Payment received"
Body: "Rs 2500 credited to your account from john@oksbi on 20 Jan"
→ amount: 2500, type: CREDIT, merchant: John, upi_id: john@oksbi
"""),
            ("human", """
Subject: {subject}
Sender: {sender}
Body: {body}
Date: {date}

Extract transaction details.
""")
        ])
        
        chain = parse_prompt | self.llm.with_structured_output(UPITransaction)
        
        try:
            transaction = chain.invoke({
                "subject": subject,
                "sender": sender,
                "body": body[:1000],  # Limit body length
                "date": date.isoformat()
            })
            
            print(f"[UPIParser] ✅ LLM parsed: ₹{transaction.amount} ({transaction.transaction_type})")
            return transaction
            
        except Exception as e:
            print(f"[UPIParser] ❌ LLM parsing failed: {e}")
            return None
    
    def _infer_category(self, text: str) -> str:
        """Infer transaction category from text"""
        if not text:
            return "other"
        
        text_lower = text.lower()
        
        category_keywords = {
            'food': ['swiggy', 'zomato', 'restaurant', 'cafe', 'food', 'dominos', 'pizza', 'burger'],
            'transport': ['uber', 'ola', 'rapido', 'redbus', 'irctc', 'metro', 'petrol', 'fuel'],
            'shopping': ['amazon', 'flipkart', 'myntra', 'ajio', 'meesho', 'shop', 'store', 'mall'],
            'entertainment': ['bookmyshow', 'netflix', 'spotify', 'prime', 'hotstar', 'movie', 'game'],
            'bills': ['electricity', 'water', 'jio', 'airtel', 'vi', 'bsnl', 'gas', 'recharge'],
            'health': ['pharmacy', 'practo', 'apollo', 'hospital', 'clinic', 'medicine', 'doctor'],
            'education': ['udemy', 'coursera', 'unacademy', 'byju', 'book', 'course', 'fees']
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return category
        
        return "other"
    
    def _extract_bank_name(self, sender: str) -> Optional[str]:
        """Extract bank name from sender email"""
        sender_lower = sender.lower()
        
        for bank, domains in self.BANK_SENDERS.items():
            if any(domain in sender_lower for domain in domains):
                return bank.upper()
        
        return None


# Singleton
_upi_parser = None


def get_upi_parser() -> UPIEmailParser:
    """Get or create UPI parser singleton"""
    global _upi_parser
    if _upi_parser is None:
        _upi_parser = UPIEmailParser()
        print("[UPIParser] ✅ Singleton initialized")
    return _upi_parser