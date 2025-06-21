"""
Security Utility Plugin - encryption, audit trails, and security helpers
"""

import os
import hashlib
import secrets
import base64
import hmac
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..base import UtilPlugin, UtilConfig


class SecurityUtil(UtilPlugin):
    """
    Security utility plugin for encryption, audit trails, and security operations.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        self.audit_trail = []
        self.failed_operations = 0
        self.successful_operations = 0
        self.last_security_event = None
        
        # Security configuration
        self.max_audit_entries = 1000
        self.password_min_length = 12
        self.token_expiry_hours = 24
        
        # Rate limiting
        self.rate_limits = {}
        self.rate_limit_window = 300  # 5 minutes
        self.max_requests_per_window = 100
    
    async def _initialize_util(self) -> bool:
        """Initialize security utility."""
        try:
            # Generate master key if not exists
            self.master_key = self._get_or_create_master_key()
            
            # Initialize encryption cipher
            self.cipher = Fernet(self.master_key)
            
            self.logger.info("Security utility initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize security utility: {e}")
            return False
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process security operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "encrypt")
        
        # Rate limiting check
        if not self._check_rate_limit(action):
            return {"success": False, "error": "Rate limit exceeded"}
        
        try:
            if action == "encrypt":
                return await self._encrypt_data(data)
            elif action == "decrypt":
                return await self._decrypt_data(data)
            elif action == "hash_password":
                return await self._hash_password(data)
            elif action == "verify_password":
                return await self._verify_password(data)
            elif action == "generate_token":
                return await self._generate_token(data)
            elif action == "verify_token":
                return await self._verify_token(data)
            elif action == "create_signature":
                return await self._create_signature(data)
            elif action == "verify_signature":
                return await self._verify_signature(data)
            elif action == "audit_log":
                return await self._log_audit_event(data)
            elif action == "get_audit_trail":
                return self._get_audit_trail(data)
            elif action == "validate_api_key":
                return await self._validate_api_key(data)
            elif action == "generate_secure_random":
                return self._generate_secure_random(data)
            elif action == "check_password_strength":
                return self._check_password_strength(data)
            elif action == "sanitize_input":
                return self._sanitize_input(data)
            elif action == "get_stats":
                return self._get_security_stats()
            else:
                raise ValueError(f"Unknown security action: {action}")
                
        except Exception as e:
            self.failed_operations += 1
            await self._log_audit_event({
                "event_type": "security_error",
                "action": action,
                "error": str(e),
                "severity": "high"
            })
            raise e
    
    async def _encrypt_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive data."""
        try:
            plaintext = data.get("data", "")
            context = data.get("context", "general")
            
            if not plaintext:
                return {"success": False, "error": "No data provided for encryption"}
            
            # Convert to bytes if string
            if isinstance(plaintext, str):
                plaintext_bytes = plaintext.encode('utf-8')
            else:
                plaintext_bytes = json.dumps(plaintext).encode('utf-8')
            
            # Encrypt data
            encrypted_data = self.cipher.encrypt(plaintext_bytes)
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            
            # Log audit event
            await self._log_audit_event({
                "event_type": "data_encryption",
                "context": context,
                "data_size": len(plaintext_bytes),
                "severity": "low"
            })
            
            self.successful_operations += 1
            
            return {
                "success": True,
                "encrypted_data": encrypted_b64,
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _decrypt_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt encrypted data."""
        try:
            encrypted_data = data.get("encrypted_data", "")
            context = data.get("context", "general")
            return_type = data.get("return_type", "string")  # string or json
            
            if not encrypted_data:
                return {"success": False, "error": "No encrypted data provided"}
            
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Decrypt data
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            
            # Convert back to original format
            if return_type == "json":
                try:
                    decrypted_data = json.loads(decrypted_bytes.decode('utf-8'))
                except json.JSONDecodeError:
                    decrypted_data = decrypted_bytes.decode('utf-8')
            else:
                decrypted_data = decrypted_bytes.decode('utf-8')
            
            # Log audit event
            await self._log_audit_event({
                "event_type": "data_decryption",
                "context": context,
                "data_size": len(decrypted_bytes),
                "severity": "medium"
            })
            
            self.successful_operations += 1
            
            return {
                "success": True,
                "decrypted_data": decrypted_data,
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return {"success": False, "error": "Decryption failed - invalid data or key"}
    
    async def _hash_password(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Hash a password using secure methods."""
        try:
            password = data.get("password", "")
            salt_provided = data.get("salt")
            
            if not password:
                return {"success": False, "error": "No password provided"}
            
            # Check password strength first
            strength_check = self._check_password_strength({"password": password})
            if not strength_check["strong"]:
                return {
                    "success": False, 
                    "error": f"Weak password: {', '.join(strength_check['issues'])}"
                }
            
            # Generate salt if not provided
            if salt_provided:
                salt = base64.b64decode(salt_provided.encode('utf-8'))
            else:
                salt = os.urandom(32)
            
            # Hash password using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            password_hash = kdf.derive(password.encode('utf-8'))
            
            # Encode for storage
            hash_b64 = base64.b64encode(password_hash).decode('utf-8')
            salt_b64 = base64.b64encode(salt).decode('utf-8')
            
            # Log audit event
            await self._log_audit_event({
                "event_type": "password_hashed",
                "password_length": len(password),
                "severity": "low"
            })
            
            self.successful_operations += 1
            
            return {
                "success": True,
                "password_hash": hash_b64,
                "salt": salt_b64,
                "algorithm": "PBKDF2-SHA256",
                "iterations": 100000,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Password hashing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _verify_password(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a password against its hash."""
        try:
            password = data.get("password", "")
            password_hash = data.get("password_hash", "")
            salt = data.get("salt", "")
            
            if not all([password, password_hash, salt]):
                return {"success": False, "error": "Password, hash, and salt required"}
            
            # Decode hash and salt
            hash_bytes = base64.b64decode(password_hash.encode('utf-8'))
            salt_bytes = base64.b64decode(salt.encode('utf-8'))
            
            # Hash provided password with same salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt_bytes,
                iterations=100000,
            )
            
            try:
                kdf.verify(password.encode('utf-8'), hash_bytes)
                password_valid = True
            except Exception:
                password_valid = False
            
            # Log audit event
            await self._log_audit_event({
                "event_type": "password_verification",
                "success": password_valid,
                "severity": "medium" if not password_valid else "low"
            })
            
            if password_valid:
                self.successful_operations += 1
            else:
                self.failed_operations += 1
            
            return {
                "success": True,
                "password_valid": password_valid,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Password verification failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a secure token."""
        try:
            payload = data.get("payload", {})
            expiry_hours = data.get("expiry_hours", self.token_expiry_hours)
            token_type = data.get("token_type", "access")
            
            # Create token data
            token_data = {
                "payload": payload,
                "token_type": token_type,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=expiry_hours)).isoformat(),
                "jti": secrets.token_hex(16)  # JWT ID
            }
            
            # Encrypt token data
            token_json = json.dumps(token_data)
            encrypted_token = self.cipher.encrypt(token_json.encode('utf-8'))
            token = base64.b64encode(encrypted_token).decode('utf-8')
            
            # Log audit event
            await self._log_audit_event({
                "event_type": "token_generated",
                "token_type": token_type,
                "expiry_hours": expiry_hours,
                "jti": token_data["jti"],
                "severity": "low"
            })
            
            self.successful_operations += 1
            
            return {
                "success": True,
                "token": token,
                "token_type": token_type,
                "expires_at": token_data["expires_at"],
                "jti": token_data["jti"]
            }
            
        except Exception as e:
            self.logger.error(f"Token generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _verify_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify and decode a token."""
        try:
            token = data.get("token", "")
            
            if not token:
                return {"success": False, "error": "No token provided"}
            
            # Decrypt token
            encrypted_token = base64.b64decode(token.encode('utf-8'))
            decrypted_data = self.cipher.decrypt(encrypted_token)
            token_data = json.loads(decrypted_data.decode('utf-8'))
            
            # Check expiry
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            is_expired = datetime.now() > expires_at
            
            # Log audit event
            await self._log_audit_event({
                "event_type": "token_verification",
                "token_type": token_data.get("token_type", "unknown"),
                "jti": token_data.get("jti", "unknown"),
                "is_expired": is_expired,
                "severity": "medium" if is_expired else "low"
            })
            
            if not is_expired:
                self.successful_operations += 1
            else:
                self.failed_operations += 1
            
            return {
                "success": True,
                "valid": not is_expired,
                "expired": is_expired,
                "payload": token_data.get("payload", {}),
                "token_type": token_data.get("token_type", "unknown"),
                "created_at": token_data.get("created_at"),
                "expires_at": token_data.get("expires_at"),
                "jti": token_data.get("jti")
            }
            
        except Exception as e:
            self.logger.error(f"Token verification failed: {e}")
            await self._log_audit_event({
                "event_type": "token_verification_failed",
                "error": str(e),
                "severity": "high"
            })
            return {"success": False, "error": "Invalid token"}
    
    async def _create_signature(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create HMAC signature for data integrity."""
        try:
            message = data.get("message", "")
            secret_key = data.get("secret_key", "")
            algorithm = data.get("algorithm", "sha256")
            
            if not message:
                return {"success": False, "error": "No message provided"}
            
            if not secret_key:
                # Use master key if no secret provided
                secret_key = base64.b64encode(self.master_key).decode('utf-8')
            
            # Create signature
            if algorithm == "sha256":
                signature = hmac.new(
                    secret_key.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
            elif algorithm == "sha512":
                signature = hmac.new(
                    secret_key.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha512
                ).hexdigest()
            else:
                return {"success": False, "error": f"Unsupported algorithm: {algorithm}"}
            
            # Log audit event
            await self._log_audit_event({
                "event_type": "signature_created",
                "algorithm": algorithm,
                "message_length": len(message),
                "severity": "low"
            })
            
            self.successful_operations += 1
            
            return {
                "success": True,
                "signature": signature,
                "algorithm": algorithm,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Signature creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _verify_signature(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify HMAC signature."""
        try:
            message = data.get("message", "")
            signature = data.get("signature", "")
            secret_key = data.get("secret_key", "")
            algorithm = data.get("algorithm", "sha256")
            
            if not all([message, signature]):
                return {"success": False, "error": "Message and signature required"}
            
            if not secret_key:
                # Use master key if no secret provided
                secret_key = base64.b64encode(self.master_key).decode('utf-8')
            
            # Create expected signature
            if algorithm == "sha256":
                expected_signature = hmac.new(
                    secret_key.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
            elif algorithm == "sha512":
                expected_signature = hmac.new(
                    secret_key.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha512
                ).hexdigest()
            else:
                return {"success": False, "error": f"Unsupported algorithm: {algorithm}"}
            
            # Compare signatures using secure comparison
            signature_valid = hmac.compare_digest(signature, expected_signature)
            
            # Log audit event
            await self._log_audit_event({
                "event_type": "signature_verification",
                "algorithm": algorithm,
                "valid": signature_valid,
                "severity": "medium" if not signature_valid else "low"
            })
            
            if signature_valid:
                self.successful_operations += 1
            else:
                self.failed_operations += 1
            
            return {
                "success": True,
                "signature_valid": signature_valid,
                "algorithm": algorithm,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Signature verification failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _log_audit_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log an audit event."""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": data.get("event_type", "unknown"),
                "severity": data.get("severity", "low"),
                "details": {k: v for k, v in data.items() if k not in ["event_type", "severity"]},
                "source": "security_util"
            }
            
            # Add to audit trail
            self.audit_trail.append(event)
            
            # Maintain audit trail size
            if len(self.audit_trail) > self.max_audit_entries:
                self.audit_trail = self.audit_trail[-self.max_audit_entries:]
            
            self.last_security_event = datetime.now()
            
            return {
                "success": True,
                "event_logged": True,
                "audit_trail_size": len(self.audit_trail)
            }
            
        except Exception as e:
            self.logger.error(f"Audit logging failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_audit_trail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get audit trail entries."""
        try:
            limit = data.get("limit", 50)
            severity_filter = data.get("severity_filter")
            event_type_filter = data.get("event_type_filter")
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            
            # Filter audit trail
            filtered_events = self.audit_trail.copy()
            
            if severity_filter:
                filtered_events = [e for e in filtered_events if e["severity"] == severity_filter]
            
            if event_type_filter:
                filtered_events = [e for e in filtered_events if e["event_type"] == event_type_filter]
            
            if start_time:
                start_dt = datetime.fromisoformat(start_time)
                filtered_events = [e for e in filtered_events if datetime.fromisoformat(e["timestamp"]) >= start_dt]
            
            if end_time:
                end_dt = datetime.fromisoformat(end_time)
                filtered_events = [e for e in filtered_events if datetime.fromisoformat(e["timestamp"]) <= end_dt]
            
            # Sort by timestamp (newest first) and limit
            filtered_events.sort(key=lambda x: x["timestamp"], reverse=True)
            limited_events = filtered_events[:limit]
            
            return {
                "success": True,
                "audit_events": limited_events,
                "total_events": len(self.audit_trail),
                "filtered_events": len(filtered_events),
                "returned_events": len(limited_events)
            }
            
        except Exception as e:
            self.logger.error(f"Audit trail retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_secure_random(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cryptographically secure random data."""
        try:
            length = data.get("length", 32)
            format_type = data.get("format", "hex")  # hex, base64, bytes
            
            if length <= 0 or length > 1024:
                return {"success": False, "error": "Invalid length (1-1024)"}
            
            # Generate random bytes
            random_bytes = secrets.token_bytes(length)
            
            # Format output
            if format_type == "hex":
                output = random_bytes.hex()
            elif format_type == "base64":
                output = base64.b64encode(random_bytes).decode('utf-8')
            elif format_type == "bytes":
                output = list(random_bytes)  # Convert to list for JSON serialization
            else:
                return {"success": False, "error": f"Unsupported format: {format_type}"}
            
            return {
                "success": True,
                "random_data": output,
                "length": length,
                "format": format_type,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Secure random generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _check_password_strength(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check password strength."""
        try:
            password = data.get("password", "")
            
            if not password:
                return {"success": False, "error": "No password provided"}
            
            issues = []
            score = 0
            
            # Length check
            if len(password) < self.password_min_length:
                issues.append(f"Too short (minimum {self.password_min_length} characters)")
            else:
                score += 20
            
            # Character variety checks
            if not re.search(r'[a-z]', password):
                issues.append("Missing lowercase letters")
            else:
                score += 15
            
            if not re.search(r'[A-Z]', password):
                issues.append("Missing uppercase letters")
            else:
                score += 15
            
            if not re.search(r'\d', password):
                issues.append("Missing numbers")
            else:
                score += 15
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                issues.append("Missing special characters")
            else:
                score += 15
            
            # Common patterns
            if re.search(r'(.)\1{2,}', password):
                issues.append("Contains repeated characters")
                score -= 10
            
            if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
                issues.append("Contains sequential numbers")
                score -= 10
            
            if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
                issues.append("Contains sequential letters")
                score -= 10
            
            # Common passwords (simplified check)
            common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
            if password.lower() in common_passwords:
                issues.append("Using common password")
                score -= 30
            
            # Calculate strength
            strength_score = max(0, min(100, score))
            
            if strength_score >= 80:
                strength = "very_strong"
            elif strength_score >= 60:
                strength = "strong"
            elif strength_score >= 40:
                strength = "moderate"
            elif strength_score >= 20:
                strength = "weak"
            else:
                strength = "very_weak"
            
            is_strong = len(issues) == 0 and strength_score >= 60
            
            return {
                "success": True,
                "strong": is_strong,
                "strength": strength,
                "score": strength_score,
                "issues": issues,
                "recommendations": [
                    f"Use at least {self.password_min_length} characters",
                    "Include uppercase and lowercase letters",
                    "Include numbers and special characters",
                    "Avoid common patterns and dictionary words"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Password strength check failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize user input to prevent injection attacks."""
        try:
            input_data = data.get("input", "")
            input_type = data.get("type", "string")  # string, sql, html, json
            
            if not input_data:
                return {"success": False, "error": "No input provided"}
            
            sanitized = input_data
            warnings = []
            
            if input_type == "sql":
                # Basic SQL injection prevention
                dangerous_patterns = [
                    r"('|(\\'))",  # Single quotes
                    r'(\"|(\\\"))',  # Double quotes
                    r'(;|\s+(OR|AND)\s+)',  # SQL operators
                    r'(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE)',  # SQL commands
                    r'(--|\/\*|\*\/)',  # SQL comments
                ]
                
                for pattern in dangerous_patterns:
                    if re.search(pattern, sanitized, re.IGNORECASE):
                        warnings.append(f"Potentially dangerous SQL pattern detected: {pattern}")
                        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
            
            elif input_type == "html":
                # Basic XSS prevention
                sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
                sanitized = sanitized.replace('"', '&quot;').replace("'", '&#x27;')
                sanitized = sanitized.replace('&', '&amp;')
                
                if '<script' in input_data.lower() or 'javascript:' in input_data.lower():
                    warnings.append("Potentially dangerous script content detected")
            
            elif input_type == "json":
                # JSON injection prevention
                try:
                    json.loads(input_data)
                except json.JSONDecodeError:
                    warnings.append("Invalid JSON format")
                    sanitized = json.dumps(input_data)  # Escape as string
            
            # General sanitization
            sanitized = sanitized.strip()
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]',  # Control characters
                r'(eval|exec|system|shell_exec)',  # Dangerous functions
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, sanitized, re.IGNORECASE):
                    warnings.append(f"Suspicious pattern detected: {pattern}")
            
            return {
                "success": True,
                "original_input": input_data,
                "sanitized_input": sanitized,
                "input_type": input_type,
                "warnings": warnings,
                "safe": len(warnings) == 0
            }
            
        except Exception as e:
            self.logger.error(f"Input sanitization failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key."""
        try:
            # In production, this should be stored securely (HSM, key vault, etc.)
            key_file = "master.key"
            
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    return f.read()
            else:
                # Generate new master key
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                os.chmod(key_file, 0o600)  # Restrict permissions
                return key
                
        except Exception:
            # Fallback to environment variable or generate temporary key
            env_key = os.environ.get('CRYPTO_MASTER_KEY')
            if env_key:
                return base64.b64decode(env_key.encode('utf-8'))
            else:
                # Generate temporary key (not recommended for production)
                return Fernet.generate_key()
    
    def _check_rate_limit(self, action: str) -> bool:
        """Check if action is within rate limits."""
        now = datetime.now()
        
        # Clean old entries
        self.rate_limits = {
            k: v for k, v in self.rate_limits.items()
            if (now - v['last_request']).total_seconds() < self.rate_limit_window
        }
        
        # Check current action
        if action not in self.rate_limits:
            self.rate_limits[action] = {'count': 1, 'last_request': now}
            return True
        
        rate_data = self.rate_limits[action]
        time_diff = (now - rate_data['last_request']).total_seconds()
        
        if time_diff >= self.rate_limit_window:
            # Reset counter
            self.rate_limits[action] = {'count': 1, 'last_request': now}
            return True
        
        if rate_data['count'] >= self.max_requests_per_window:
            return False
        
        # Increment counter
        self.rate_limits[action]['count'] += 1
        self.rate_limits[action]['last_request'] = now
        return True
    
    def _get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        return {
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "success_rate": (self.successful_operations / max(1, self.successful_operations + self.failed_operations)) * 100,
            "audit_trail_size": len(self.audit_trail),
            "last_security_event": self.last_security_event.isoformat() if self.last_security_event else None,
            "rate_limit_stats": {
                "active_limits": len(self.rate_limits),
                "window_seconds": self.rate_limit_window,
                "max_requests": self.max_requests_per_window
            },
            "security_features": {
                "encryption": True,
                "password_hashing": True,
                "token_generation": True,
                "signature_creation": True,
                "audit_logging": True,
                "input_sanitization": True,
                "rate_limiting": True
            },
            "plugin_name": self.name,
            "enabled": self.config.enabled
        }