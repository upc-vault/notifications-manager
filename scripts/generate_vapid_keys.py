"""
Generate VAPID keys for Web Push notifications
"""

from py_vapid import Vapid
import json
import os

def generate_vapid_keys():
    """Generate VAPID keys and save to .env"""
    print("\n" + "="*70)
    print("🔐 GENERATING VAPID KEYS FOR WEB PUSH")
    print("="*70)
    
    # Create config directory
    os.makedirs('config', exist_ok=True)
    
    # Generate VAPID keys
    vapid = Vapid()
    vapid.generate_keys()
    
    # Save to files
    vapid.save_key('config/vapid_private.pem')
    
    # Get the public key in the correct format for Web Push
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    from py_vapid import b64urlencode
    
    public_key_bytes = vapid.public_key.public_bytes(
        encoding=Encoding.X962,
        format=PublicFormat.UncompressedPoint
    )
    public_key_b64 = b64urlencode(public_key_bytes)
    
    print("\n✅ VAPID Keys Generated:\n")
    print(f"Public Key:  {public_key_b64}")
    print(f"Private Key: Saved to config/vapid_private.pem\n")
    
    # Save to .env file
    env_path = '.env'
    env_content = []
    
    # Read existing .env or .env.example
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.readlines()
    elif os.path.exists('.env.example'):
        with open('.env.example', 'r') as f:
            env_content = f.readlines()
    
    # Remove old VAPID keys if present
    env_content = [line for line in env_content if not line.startswith('VAPID_')]
    
    # Add new VAPID keys
    import datetime
    env_content.append(f'\n# VAPID Keys for Web Push (Generated {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")})\n')
    env_content.append(f'VAPID_PUBLIC_KEY={public_key_b64}\n')
    env_content.append(f'VAPID_PRIVATE_KEY_FILE=config/vapid_private.pem\n')
    env_content.append(f'VAPID_EMAIL=mailto:admin@yourbank.com\n')
    
    # Write to .env
    with open(env_path, 'w') as f:
        f.writelines(env_content)
    
    print(f"✅ Keys saved to {env_path}\n")
    
    # Save to JSON for easy access
    keys_json = {
        'public_key': public_key_b64,
        'private_key_file': 'config/vapid_private.pem',
        'email': 'mailto:admin@yourbank.com'
    }
    
    os.makedirs('config', exist_ok=True)
    with open('config/vapid_keys.json', 'w') as f:
        json.dump(keys_json, f, indent=2)
    
    print(f"✅ Keys also saved to config/vapid_keys.json\n")
    
    print("="*70)
    print("\n🌐 Next Steps:")
    print("1. Copy the VAPID_PUBLIC_KEY to your web page")
    print("2. Restart the API server to load the new keys")
    print("3. Open the web page and click 'Subscribe to Notifications'")
    print("="*70 + "\n")
    
    return keys_json

if __name__ == '__main__':
    generate_vapid_keys()
