"""Sirve la app GymTracker por HTTPS con certificado autofirmado"""
import ssl, http.server, socketserver, os, sys

# 1. Generar certificado autofirmado
CERT_FILE = "server.crt"
KEY_FILE = "server.key"

if not os.path.exists(CERT_FILE):
    print("Generando certificado SSL autofirmado...")
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime, ipaddress

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(1000)
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )
        with open(KEY_FILE, "wb") as f:
            f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
        with open(CERT_FILE, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print("  Certificado generado con cryptography")
    except ImportError:
        print("  cryptography no disponible, instalando...")
        os.system(f"{sys.executable} -m pip install cryptography -q")
        print("  Re-ejecuta el script para generar el certificado.")
        sys.exit(1)

# 2. Obtener IP local
ip_local = "127.0.0.1"
try:
    import subprocess
    result = subprocess.run(["ipconfig"], capture_output=True, text=True, shell=True)
    for line in result.stdout.splitlines():
        if "IPv4" in line or "Direcci" in line:
            parts = line.split(":")
            if len(parts) > 1:
                ip_local = parts[1].strip()
                break
except:
    pass

# 3. Servir HTTPS
PORT = 8443
web_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(web_dir)

print(f"\n{'='*55}")
print(f"  SERVIDOR HTTPS GYMTRACKER")
print(f"{'='*55}")
print(f"  En tu Android (Chrome): https://{ip_local}:{PORT}")
print(f"  En tu PC:              https://localhost:{PORT}")
print(f"  (ignora la advertencia de conexión no segura)")
print(f"  Ctrl+C para detener")
print(f"{'='*55}\n")

handler = http.server.SimpleHTTPRequestHandler
httpd = socketserver.TCPServer(("0.0.0.0", PORT), handler)
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(CERT_FILE, KEY_FILE)
httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
