import cv2
from pyzbar.pyzbar import decode
import subprocess
import platform
import os

def parse_qr_data(qr_data):
    """Parse the Wi-Fi credentials from the QR code data."""
    if not qr_data.startswith("WIFI:"):
        return None, None

    # Split the QR data to get the SSID and Password
    segments = qr_data[5:].split(";")
    ssid = None
    password = None

    for segment in segments:
        if segment.startswith("S:"):
            ssid = segment[2:]
        elif segment.startswith("P:"):
            password = segment[2:]

    return ssid, password

def create_windows_wifi_profile(ssid, password):
    """Create a Wi-Fi profile for Windows."""
    profile_xml = f"""
    <WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
        <name>{ssid}</name>
        <SSIDConfig>
            <SSID>
                <name>{ssid}</name>
            </SSID>
        </SSIDConfig>
        <connectionType>ESS</connectionType>
        <connectionMode>auto</connectionMode>
        <MSM>
            <security>
                <authEncryption>
                    <authentication>WPA2PSK</authentication>
                    <encryption>AES</encryption>
                    <useOneX>false</useOneX>
                </authEncryption>
                <sharedKey>
                    <keyType>passPhrase</keyType>
                    <protected>false</protected>
                    <keyMaterial>{password}</keyMaterial>
                </sharedKey>
            </security>
        </MSM>
    </WLANProfile>
    """
    profile_path = f"{ssid}.xml"
    with open(profile_path, "w") as f:
        f.write(profile_xml)
    return profile_path

def connect_to_wifi(ssid, password):
    """Connect to a Wi-Fi network using system commands."""
    system = platform.system()

    try:
        if system == "Windows":
            # Create a Wi-Fi profile
            profile_path = create_windows_wifi_profile(ssid, password)
            
            # Add the Wi-Fi profile
            subprocess.run(f'netsh wlan add profile filename="{profile_path}"', shell=True, check=True)

            # Connect to the Wi-Fi network using the profile
            connect_cmd = f'netsh wlan connect name="{ssid}" ssid="{ssid}"'
            subprocess.run(connect_cmd, shell=True, check=True)

            # Remove the profile file after use
            os.remove(profile_path)

        elif system == "Darwin":  # macOS
            # Use networksetup command for macOS
            connect_cmd = f'networksetup -setairportnetwork en0 "{ssid}" "{password}"'
            subprocess.run(connect_cmd, shell=True, check=True)

        elif system == "Linux":
            # Use nmcli for Linux (assumes NetworkManager is used)
            connect_cmd = f'nmcli dev wifi connect "{ssid}" password "{password}"'
            subprocess.run(connect_cmd, shell=True, check=True)

        else:
            print(f"Unsupported operating system: {system}")
            return False

        print(f"Connected to Wi-Fi network: {ssid}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed to connect to Wi-Fi network: {ssid}. Error: {e}")
        return False

def save_credentials(ssid, password):
    """Save the Wi-Fi credentials to a text file."""
    with open("wifi_credentials.txt", "a") as f:
        f.write(f"SSID: {ssid}, Password: {password}\n")
    print("Wi-Fi credentials saved to wifi_credentials.txt.")

def scan_qr_code():
    """Scan QR codes from the webcam and handle Wi-Fi connections."""
    cap = cv2.VideoCapture(0)

    connected_ssids = set()

    while True:
        ret, frame = cap.read()
        decoded_objects = decode(frame)

        for obj in decoded_objects:
            qr_data = obj.data.decode('utf-8')

            # Parse Wi-Fi credentials
            ssid, password = parse_qr_data(qr_data)

            if ssid and password and ssid not in connected_ssids:
                print(f"Detected Wi-Fi network: SSID: {ssid}, Password: {password}")

                # Connect to Wi-Fi if not already connected
                if connect_to_wifi(ssid, password):
                    connected_ssids.add(ssid)
                    save_credentials(ssid, password)
                else:
                    print(f"Failed to connect to SSID: {ssid}. Please check the credentials.")

                # Only display the details once
                break

            # Display QR code bounding box
            points = obj.polygon
            if len(points) > 4:
                hull = cv2.convexHull(points)
                points = hull

            num_points = len(points)
            for j in range(num_points):
                cv2.line(frame, tuple(points[j]), tuple(points[(j + 1) % num_points]), (255, 0, 0), 3)

        # Display the resulting frame
        cv2.imshow('QR Code Scanner', frame)

        # Break loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    scan_qr_code()
