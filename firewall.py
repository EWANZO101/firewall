from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import config  # Make sure you have your config file for API key and controller URL

app = Flask(__name__)
app.secret_key = "your_secret_key"  # To enable flashing messages

# Set up headers with the API key for authentication
headers = {
    "Authorization": f"Bearer {config.API_KEY}",
    "Accept": "application/json"
}

# Function to validate the VLAN IP (starts with 192.168.)
def validate_local_ip(local_ip):
    return local_ip.startswith("192.168.")

# Function to check if WAN IP matches VLAN IP
def validate_wan_ip(vlan_ip, wan_ip):
    return vlan_ip == wan_ip

@app.route('/')
def index():
    return render_template('fw.html')  # Your HTML page

@app.route('/apply_port_forward', methods=['POST'])
def apply_port_forward():
    if request.method == 'POST':
        vlan_ip = request.form['vlan_ip']  # Get the VLAN IP from the form
        dst_port = request.form['dst_port']
        fwd_ip = request.form['fwd_ip']
        fwd_port = request.form['fwd_port']
        protocol = request.form['protocol']
        name = request.form['name']

        # Step 1: Validate VLAN IP
        if not validate_local_ip(vlan_ip):
            flash(f"The VLAN IP address {vlan_ip} is not valid. It should start with '192.168.'", "danger")
            return redirect(url_for('index'))  # Return to form if validation fails

        # Step 2: Ensure WAN IP matches the VLAN IP
        if not validate_wan_ip(vlan_ip, fwd_ip):
            flash(f"The WAN IP ({fwd_ip}) does not match the VLAN IP ({vlan_ip}). Please enter a valid WAN IP.", "danger")
            return redirect(url_for('index'))  # Return to form if validation fails

        # Step 3: Apply the port forwarding rule
        port_forward_rule = {
            "enabled": True,
            "name": name,
            "src": "any",
            "src_port": "any",
            "dst_port": dst_port,
            "fwd_ip": fwd_ip,
            "fwd_port": fwd_port,
            "protocol": protocol,
            "log": False,
            "wan_ip": fwd_ip  # Set the WAN IP here (same as VLAN IP)
        }

        rules_url = f"{config.CONTROLLER_URL}/api/s/default/rest/firewallrule"
        response = requests.post(rules_url, json=port_forward_rule, headers=headers, verify=False)
        if response.status_code == 200:
            flash(f"Port forwarding rule for {dst_port} created successfully!", "success")
            return redirect(url_for('index'))  # Redirect back to the form
        else:
            flash(f"Failed to create port forwarding rule: {response.text}", "danger")
            return redirect(url_for('index'))

    return render_template('fw.html')  # Template for the port forwarding form

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=6001)
