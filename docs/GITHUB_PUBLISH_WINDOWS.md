# Publish AgriORBIT using GitHub Desktop — Windows

1. Download and extract the prepared GitHub ZIP. **Do not** upload the single ZIP as your repository: GitHub judges need to browse the actual source files.
2. Sign into [GitHub Desktop](https://desktop.github.com/).
3. Choose **File → Add local repository** and select the extracted `AgriORBIT-Phase42-NASA-Field-Shift` folder.
4. If told this directory is not a Git repository, choose **Create a Repository here**. Name `AgriORBIT-Phase42-NASA-Field-Shift` and do not add another README/license, because one already exists.
5. Confirm the file changes, set the commit message `Publish AgriORBIT Phase 42 NASA Field Shift prototype`, then **Commit to main**.
6. Select **Publish repository**, choose your own account or authorized organization, then **uncheck Keep this code private** only after reviewing the rights/privacy checklist and deciding to publish publicly.
7. Open your new repo on github.com and test its URL in an incognito/private browser window.
8. In NASA Space Apps → your Team → Project tab → Edit, put the public repository URL in the available project/source-code links. Save/submit your project separately.

This approach avoids the Windows `cmd.exe` issue in earlier local startup screenshots. GitHub Desktop handles authentication.

**If an existing repo is already linked:** do not use these steps to overwrite it. Open the existing repository and copy in reviewed changes or create a branch instead.
