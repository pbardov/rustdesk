# VSGSoft RustDesk client

Custom builds use `rustdesk.vsgsoft.com` with the public key and relay in
[`vsgsoft/server.json`](vsgsoft/server.json). The private server key is never
needed by this repository or its workflows.

Downloads: **https://pbardov.github.io/rustdesk/**

## Builds and updates

The **VSGSoft client** workflow runs daily, after customization changes, and
manually from the Actions tab. It selects the latest stable upstream release,
replaces the application sources with that release, preserves this fork's
automation, reapplies the public server defaults, and commits normally to
`vsgsoft`. It does not force-push or merge upstream development snapshots.

The workflow builds the modern Flutter client for:

- Windows x64: portable EXE and MSI;
- Linux x64: DEB and RPM;
- macOS Intel and Apple Silicon: DMG.

Platform build steps and dependency pins are adapted from RustDesk 1.5.1's
official workflows. Future upstream changes that alter build dependencies or
configuration entry points may require updating the workflow; incompatible
patch entry points fail explicitly. Flutter bridge code generation runs only
in GitHub Actions, following the upstream CI process.

Completed builds become GitHub Releases. GitHub Pages links to those assets,
so downloads do not require a GitHub account. A release contains SHA256 checksums,
a manifest recording the exact upstream and custom source commits, and a full
source archive including Git submodules. A failed build leaves the previous
download page and release available. An already published configuration is
skipped on scheduled checks; **Force rebuild** creates a new release tag.

No personal access token or server secret is required. The preparation job has
repository write permission for source synchronization. Compilation jobs have
read permission. Only publication can write Releases and deploy Pages.

## Configuration behavior

`vsgsoft/configure.py` adds one module and two small hooks to upstream:

- `src/lib.rs` declares `vsgsoft_config`;
- `src/common.rs::load_custom_client` applies defaults before loading optional
  custom configuration;
- generated `src/vsgsoft_config.rs` populates the existing `DEFAULT_SETTINGS`
  and `DEFAULT_LOCAL_SETTINGS` maps.

The ID server, relay, public key and empty API server are presets, not locked
settings. Existing user configuration takes precedence. New installations need
no manual server setup, and renaming the downloaded file does not change the
preset. Built binaries are checked for the embedded server profile before
publication.

Upstream update checks are disabled by default because upstream installers do
not include this customization. Download updates from the VSGSoft page.
No permanent remote-access password is embedded; RustDesk's normal local
password and consent behavior remains intact.

## Signing

These builds are unsigned. Authenticode signing and Apple notarization require
the corresponding certificates and account credentials, which are not present
in this repository. macOS still requires the usual screen-recording and
accessibility permissions.

## Changing server settings

Edit `vsgsoft/server.json`, commit to `vsgsoft`, and allow the workflow to finish.
For a local source checkout, apply the same customization with:

```sh
python3 vsgsoft/configure.py
```

The server public key is public configuration. Preserve all RustDesk copyright
and license files; application sources remain under the upstream AGPL-3.0 license.
