import requests

ORG_SLUG = "bazel-trusted"
# Generate token with read/write pipelines and read organizations scope
# and access to graghQL
API_TOKEN = "bkua_b53978e5f05c755074e9359d26bef470dd1511c1"

def generate_terraform_imports(org_slug, token):
    url = f"https://api.buildkite.com/v2/organizations/{org_slug}/pipelines"
    headers = {"Authorization": f"Bearer {token}"}
    
    import_blocks = []

    print(f"Connecting to Buildkite for org: {org_slug}...")

    while url:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break
            
        data = response.json()
        for p in data:
            slug = p['slug']
            gql_id = p['graphql_id']
            
            block = f'import {{\n  to = buildkite_pipeline.{slug}\n  id = "{gql_id}"\n}}\n'
            import_blocks.append(block)
        
        url = response.links.get('next', {}).get('url')

    # Write to file
    with open(f"../{ORG_SLUG}/import.tf", "w") as f:
        f.write("# Generated Import Blocks\n\n")
        f.writelines("\n".join(import_blocks))
    
    print(f"✅ Success! Created import.tf with {len(import_blocks)} pipelines.")

if __name__ == "__main__":
    generate_terraform_imports(ORG_SLUG, API_TOKEN)