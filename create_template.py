import pandas as pd

# Create sample data
data = {
    'IP Address': [
        '8.8.8.8',           # Google DNS
        '1.1.1.1',           # Cloudflare DNS
        '208.67.222.222',    # OpenDNS
        '192.168.1.1',       # Common router IP
        '127.0.0.1',         # Localhost
        '192.168.1.100',     # Example local IP
        '10.0.0.1',          # Another common router IP
        '172.16.0.1'         # Private network IP
    ],
    'Description': [
        'Google DNS Primary',
        'Cloudflare DNS',
        'OpenDNS',
        'Default Gateway',
        'Localhost',
        'Local Device',
        'Router',
        'Private Network Gateway'
    ]
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel
df.to_excel('example_template.xlsx', index=False)
print("Example template created: example_template.xlsx")
print("\nContent:")
print(df)
