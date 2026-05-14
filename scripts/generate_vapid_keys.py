"""
VAPID Key Generator for Web Push
Generates public/private key pairs for Web Push authentication
"""
import json
from pathlib import Path
from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization


def generate_vapid_keys():
    """Generate VAPID key pair and save to file"""
    
    print("\n🔑 Generating VAPID keys for Web Push authentication...\n")
    
    # Generate key pair
    vapid = Vapid()
    vapid.generate_keys()
    
    # Get keys in different formats
    private_key_pem = vapid.private_pem().decode('utf-8')
    
    # Get public key in uncompressed format
    public_key_bytes = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    # Convert to URL-safe base64
    import base64
    public_key = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
    
    # Create config directory if it doesn't exist
    config_dir = Path(__file__).parent.parent / "config"
    config_dir.mkdir(exist_ok=True)
    
    # Save keys to file
    keys_file = config_dir / "vapid_keys.json"
    
    keys_data = {
        "private_key": private_key_pem,
        "public_key": public_key,
        "instructions": {
            "private_key": "Keep this SECRET! Never expose in client code.",
            "public_key": "Share this with browsers for subscription. Include in Service Worker."
        }
    }
    
    with open(keys_file, 'w') as f:
        json.dump(keys_data, f, indent=2)
    
    print(f"✅ VAPID keys generated successfully!")
    print(f"📁 Saved to: {keys_file}\n")
    
    print("=" * 70)
    print("PUBLIC KEY (Safe to share with browsers):")
    print("=" * 70)
    print(public_key)
    print()
    
    print("=" * 70)
    print("PRIVATE KEY (KEEP SECRET - Server use only):")
    print("=" * 70)
    print(private_key_pem[:50] + "...")
    print()
    
    # Generate .env entries
    print("=" * 70)
    print("Add these to your .env file:")
    print("=" * 70)
    print(f'VAPID_PUBLIC_KEY="{public_key}"')
    print('VAPID_PRIVATE_KEY="<see vapid_keys.json>"')
    print('VAPID_ADMIN_EMAIL="admin@yourdomain.com"')
    print()
    
    print("🎉 Setup complete! Use public key in your frontend Service Worker.")
    print()


if __name__ == "__main__":
    generate_vapid_keys()
