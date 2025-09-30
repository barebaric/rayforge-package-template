# Rayforge Package Template

Welcome! This is the official template for creating and publishing packages for Rayforge.
A "package" can be a code-based plugin, a collection of assets (like recipes and
machine profiles), or both.

This template includes a pre-configured GitHub Actions workflow that automatically
announces your new releases to the central Rayforge Registry.

## How to Use This Template

Follow these steps to get your package published.

### Step 1: Create Your Repository

Click the **"Use this template"** button at the top of this repository's page on
GitHub. Ensure the new repository is **public**, as the Rayforge app will need
to be able to clone it.

Private repositories are not supported.

### Step 2: Configure Your Package Metadata

Open the `rayforge-package.yaml` file and edit the placeholder values to describe
your package.

### Step 3: Add Your Code and Assets

- **Code:** Place your Python source code in the folder you used in `rayforge-package.yaml`.
- **Assets:** Place your assets (recipes, profiles, etc.) in the `assets/`
  directory and ensure the paths in `rayforge-package.yaml` are correct.

### Step 4: Set Up the Release Token (One-Time Setup)

The automated release workflow needs a token with minimal permissions to announce your releases.

1.  **Create a Personal Access Token (PAT):**
    - Go to your GitHub Settings > Developer settings > Personal access tokens > Tokens (classic).
    - Click **"Generate new token"** (classic).
    - Give it a descriptive name (e.g., `Rayforge Registry Announcer`).
    - Set an expiration date (e.g., 1 year).
    - Under **"Select scopes,"** check only the box for **`public_repo`**. This grants read-only
      permission for public repositories.
    - Click **"Generate token"** and **copy the token immediately**. You will not see it again.

2.  **Add the Token to Your Repository Secrets:**
    - Go to your new repository's **Settings > Secrets and variables > Actions**.
    - Click **"New repository secret"**.
    - For the **Name**, enter `REGISTRY_ACCESS_TOKEN`.
    - For the **Secret**, paste the Personal Access Token you just copied.
    - Click **"Add secret"**.

### Step 5: Publish Your First Release!

You're all set! To publish a version, all you need to do is create and push a Git tag.

```bash
# Commit all your changes first
git add .
git commit -m "feat: Initial release v1.0.0"

# Create and push a semantic version tag
git tag v1.0.0
git push origin v1.0.0
```

That's it! The GitHub Action in this repository will automatically run and submit your
new version to the central Rayforge Registry.

---

## Best Practices

- **Use Semantic Versioning:** Your tags must follow the `vX.Y.Z` format (e.g., `v1.0.0`, `v1.2.3`).
- **Keep Your Repository Public:** The Rayforge client needs to be able to clone your repository to install the package.
- **Don't Modify the Workflow:** The `.github/workflows/release.yml` file is designed to work out-of-the-box.
- **Choose a License:** This template includes a placeholder `LICENSE` file. Please replace it with an open-source license of your choice.
