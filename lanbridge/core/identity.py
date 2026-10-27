from __future__ import annotations

import datetime as dt
import hashlib
import ssl
import threading
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from lanbridge.core.storage import atomic_write, private_directory, read_json, write_json


def parse_certificate(pem: str) -> x509.Certificate:
    if not isinstance(pem, str) or len(pem) > 8192:
        raise ValueError("Invalid certificate size")
    cert = x509.load_pem_x509_certificate(pem.encode("ascii"))
    key = cert.public_key()
    if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(key.curve, ec.SECP256R1):
        raise ValueError("Unsupported identity key")
    key.verify(cert.signature, cert.tbs_certificate_bytes, ec.ECDSA(cert.signature_hash_algorithm))
    now = dt.datetime.now(dt.UTC)
    if not cert.not_valid_before_utc <= now < cert.not_valid_after_utc:
        raise ValueError("Identity certificate expired or not yet valid")
    return cert


def fingerprint(pem: str) -> str:
    return parse_certificate(pem).fingerprint(hashes.SHA256()).hex()


class Identity:
    def __init__(self, directory: Path):
        self.directory = private_directory(directory)
        self.cert_path = directory / "certificate.pem"
        self.key_path = directory / "private-key.pem"
        if self.cert_path.exists() != self.key_path.exists():
            raise ValueError("Incomplete identity: restore both certificate and private key")
        if not self.cert_path.exists():
            key = ec.generate_private_key(ec.SECP256R1())
            name = x509.Name(
                [
                    x509.NameAttribute(
                        NameOID.COMMON_NAME,
                        f"LanBridge-{hashlib.sha256(key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)).hexdigest()[:24]}",
                    )
                ]
            )
            now = dt.datetime.now(dt.UTC)
            cert = (
                x509.CertificateBuilder()
                .subject_name(name)
                .issuer_name(name)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now - dt.timedelta(minutes=5))
                .not_valid_after(now + dt.timedelta(days=3650))
                .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
                .add_extension(
                    x509.KeyUsage(True, False, False, False, False, True, True, False, False), critical=True
                )
                .add_extension(
                    x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH, ExtendedKeyUsageOID.CLIENT_AUTH]),
                    critical=False,
                )
                .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
                .sign(key, hashes.SHA256())
            )
            atomic_write(
                self.key_path,
                key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                ),
            )
            atomic_write(self.cert_path, cert.public_bytes(serialization.Encoding.PEM))
        self.pem = self.cert_path.read_text(encoding="ascii")
        self.certificate = parse_certificate(self.pem)
        self.id = fingerprint(self.pem)
        self.key = serialization.load_pem_private_key(self.key_path.read_bytes(), password=None)
        if self.key.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        ) != self.certificate.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        ):
            raise ValueError("Identity certificate and key do not match")

    def sign(self, data: bytes) -> str:
        return self.key.sign(data, ec.ECDSA(hashes.SHA256())).hex()


class TrustStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.RLock()
        self.peers: dict[str, dict[str, str]] = read_json(path, {})
        for peer_id, record in self.peers.items():
            if fingerprint(record["certificate"]) != peer_id:
                raise ValueError("Corrupt trust store")

    def add(self, pem: str, name: str) -> str:
        peer_id = fingerprint(pem)
        with self._lock:
            self.peers[peer_id] = {"certificate": pem, "name": name[:100]}
            write_json(self.path, self.peers)
        return peer_id

    def remove(self, peer_id: str) -> None:
        with self._lock:
            self.peers.pop(peer_id, None)
            write_json(self.path, self.peers)

    def context(self, identity: Identity, *, server: bool, peer_id: str | None = None) -> ssl.SSLContext:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER if server else ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False  # Stable certificate pins authenticate identity, not DHCP addresses.
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(identity.cert_path, identity.key_path)
        with self._lock:
            if peer_id is not None and peer_id not in self.peers:
                raise ValueError("Device is not paired")
            certs = (
                [self.peers[peer_id]["certificate"]]
                if peer_id
                else [p["certificate"] for p in self.peers.values()]
            )
        if certs:
            ctx.load_verify_locations(cadata="\n".join(certs))
        return ctx

    def verify_socket(self, writer, expected: str | None = None) -> str:
        tls = writer.get_extra_info("ssl_object")
        if tls is None:
            raise ValueError("Encrypted connection required")
        der = tls.getpeercert(binary_form=True)
        peer_id = hashlib.sha256(der).hexdigest()
        with self._lock:
            if peer_id not in self.peers or (expected is not None and expected != peer_id):
                raise ValueError("Peer certificate does not match trusted identity")
        return peer_id
