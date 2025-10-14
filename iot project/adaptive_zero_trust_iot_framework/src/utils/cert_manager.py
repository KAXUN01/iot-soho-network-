"""
Certificate Authority and Device Certificate Management
"""
import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import uuid

class CertificateManager:
    def __init__(self, ca_cert_path="certificates/ca_cert.pem", 
                 ca_key_path="certificates/ca_key.pem"):
        self.ca_cert_path = ca_cert_path
        self.ca_key_path = ca_key_path
        self.ca_cert = None
        self.ca_key = None

        # Create certificates directory
        os.makedirs("certificates", exist_ok=True)

        # Load or create CA
        if os.path.exists(ca_cert_path) and os.path.exists(ca_key_path):
            self.load_ca()
        else:
            self.create_ca()

    def create_ca(self):
        """Create a new Certificate Authority"""
        print("Creating new Certificate Authority...")

        # Generate CA private key
        self.ca_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Create CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"IoT Framework CA"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"IoT Framework Root CA"),
        ])

        self.ca_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self.ca_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=3650)  # 10 years
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True,
        ).add_extension(
            x509.KeyUsage(
                key_cert_sign=True, crl_sign=True, digital_signature=False,
                content_commitment=False, key_encipherment=False,
                data_encipherment=False, key_agreement=False,
                encipher_only=False, decipher_only=False
            ), critical=True,
        ).sign(self.ca_key, hashes.SHA256())

        # Save CA certificate and key
        self.save_ca()
        print(f"CA certificate created and saved to {self.ca_cert_path}")

    def save_ca(self):
        """Save CA certificate and private key to files"""
        # Save CA certificate
        with open(self.ca_cert_path, "wb") as f:
            f.write(self.ca_cert.public_bytes(serialization.Encoding.PEM))

        # Save CA private key
        with open(self.ca_key_path, "wb") as f:
            f.write(self.ca_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

    def load_ca(self):
        """Load existing CA certificate and private key"""
        with open(self.ca_cert_path, "rb") as f:
            cert_bytes = f.read()
            # Support older cryptography versions that require a backend parameter
            try:
                self.ca_cert = x509.load_pem_x509_certificate(cert_bytes)
            except TypeError:
                self.ca_cert = x509.load_pem_x509_certificate(cert_bytes, default_backend())

        with open(self.ca_key_path, "rb") as f:
            key_bytes = f.read()
            try:
                self.ca_key = serialization.load_pem_private_key(key_bytes, password=None)
            except TypeError:
                self.ca_key = serialization.load_pem_private_key(key_bytes, password=None, backend=default_backend())

    def create_device_certificate(self, device_id, public_key_pem):
        """Create and sign a device certificate from CSR"""
        try:
            # Load the public key from PEM format
            public_key = serialization.load_pem_public_key(public_key_pem.encode())

            # Create device certificate
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"IoT Device"),
                x509.NameAttribute(NameOID.COMMON_NAME, device_id),
            ])

            device_cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                self.ca_cert.subject
            ).public_key(
                public_key
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)  # 1 year
            ).add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True,
            ).add_extension(
                x509.KeyUsage(
                    digital_signature=True, key_encipherment=True,
                    key_cert_sign=False, crl_sign=False,
                    content_commitment=False, data_encipherment=False,
                    key_agreement=False, encipher_only=False, decipher_only=False
                ), critical=True,
            ).sign(self.ca_key, hashes.SHA256())

            # Return certificate in PEM format
            return device_cert.public_bytes(serialization.Encoding.PEM).decode()

        except Exception as e:
            print(f"Error creating device certificate: {e}")
            return None

    def get_ca_certificate_pem(self):
        """Return CA certificate in PEM format"""
        return self.ca_cert.public_bytes(serialization.Encoding.PEM).decode()

    def verify_certificate(self, cert_pem):
        """Verify if a certificate was signed by our CA"""
        try:
            cert = x509.load_pem_x509_certificate(cert_pem.encode())
            # Check if certificate was signed by our CA
            ca_public_key = self.ca_cert.public_key()
            ca_public_key.verify(cert.signature, cert.tbs_certificate_bytes, 
                                cert.signature_hash_algorithm)
            return True
        except Exception:
            return False

# Example usage and testing
if __name__ == "__main__":
    cm = CertificateManager()
    print("Certificate Manager initialized successfully")
    print(f"CA Certificate PEM preview:\n{cm.get_ca_certificate_pem()[:200]}...")
