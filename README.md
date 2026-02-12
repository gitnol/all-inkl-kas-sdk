# All-Inkl KAS SOAP API SDK for Python

[![CI](https://github.com/gitnol/all-inkl-kas-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/gitnol/all-inkl-kas-sdk/actions/workflows/ci.yml)

A robust, modular Python SDK for the All-Inkl KAS SOAP API.
It handles known API quirks (like integer handling and trailing dots) automatically, so you don't have to.

## Features

- **Automatic Type Conversion**: Converts integers to strings (API requirement).
- **DNS Safeties**:
    - Auto-appends trailing dots for `zone_host` on creation.
    - Strips `zone_host` on updates (prevents errors).
- **Robust XML Parsing**: Namespace-safe, handles complex nested responses and lists.
- **Typed Exceptions**: `KasApiError`, `KasAuthError`, `KasConnectionError` for precise error handling.
- **Lazy-Loaded Services**: Services are imported on first access — fast startup, no unnecessary overhead.
- **Service Pattern**: 21 organized modules for `Account`, `DNS`, `Domain`, `Mail`, and more.
- **Flood Protection**: Built-in rate limiting (defaults to 2s).

## Installation

```bash
pip install -e .
```

This installs `kas_sdk` as an editable package so all scripts in `scripts/`, `tests/`, and `debug/` can import it from any working directory.

## Usage

### Credential Management (Secure)

The SDK supports secure credential management via **Keyring** (System Vault) and **Environment Variables**, so you don't have to hardcode passwords in scripts.

**Priority Order:**
1.  **Explicit Arguments**: Passed directly to `KasClient`.
2.  **Environment Variables**: `KAS_LOGIN` and `KAS_PASS`.
3.  **System Keyring**: Looks for service `kas_api` and your login user.

### Initialization

```python
from kas_sdk import KasClient

# 1. Automatic Discovery (Recommended)
# Looks in Env Vars or Keyring
client = KasClient(kas_login='w0123456')

# 2. Hardcoded (Not Recommended)
client = KasClient('w0123456', 'secret_password')

# 3. Dry Run Config
# client = KasClient(dry_run=True)
```

### Dry Run Mode

You can enable `dry_run` mode to simulate requests without sending them to the API. This is useful for testing and debugging.

- **Constructor**: Pass `dry_run=True` to the `KasClient` constructor.
- **Environment Variable**: Set `KAS_DRY_RUN=1` (or `true`) in your environment.

When enabled, the client will log the request details (Action, Params, XML) and return a mock success response.

### Error Handling

All SDK errors inherit from `KasApiError`, so you can catch broadly or precisely:

```python
from kas_sdk import KasClient, KasApiError, KasAuthError, KasConnectionError

try:
    client = KasClient(kas_login='w0123456')
    records = client.dns.get_dns_settings('example.com')
except KasAuthError as e:
    print(f"Login failed: {e}")
except KasConnectionError as e:
    print(f"Network error: {e}")
except KasApiError as e:
    print(f"API error: {e}")
```

| Exception | When raised |
| :--- | :--- |
| `KasAuthError` | Missing or invalid credentials |
| `KasConnectionError` | HTTP/network failure |
| `KasApiError` | SOAP fault or malformed response (base class for all SDK errors) |

## Documentation

The API Documentation is split into logical sections for easier navigation.

### 📚 [1. Account & Session Management](docs/01_account.md)
*   **AccountService**: Create and manage KAS sub-accounts and settings.
*   **SessionService**: Generate KAS SSO tokens.

### 🌐 [2. Domains & DNS](docs/02_domains_dns.md)
*   **DomainService**: Add/Move/Delete domains.
*   **SubdomainService**: Manage subdomains.
*   **DnsService**: Edit zone records (A, MX, TXT, etc).
*   **DdnsService**: Manage DynDNS users.
*   **SslService**: Manage SSL certificates (custom certs, HSTS, Force HTTPS).

### 📧 [3. Email Infrastructure](docs/03_email.md)
*   **MailAccountService**: Manage POP3/IMAP mailboxes.
*   **MailForwardService**: Setup email forwarders.
*   **MailFilterService**: Configure server-side rules.
*   **MailingListService**: Manage mailing lists.

### 🛠️ [4. System & Tools](docs/04_system.md)
*   **CronjobService**: Manage strict cronjobs.
*   **DatabaseService**: Create MySQL databases.
*   **FtpUserService**: Manage FTP access.
*   **SoftwareInstallService**: Application installers (e.g. WordPress).
*   **StatisticService**: Check disk space and traffic.
*   **DirectoryProtectionService**: htaccess protection.
*   **Samba/Chown/Symlink**: Advanced filesystem tools.

## Supported Services Overview

Here is a quick summary of all available services on the `KasClient`:

| Service Property | Class | Key Functions |
| :--- | :--- | :--- |
| `client.account` | `AccountService` | `get_accounts`, `add_account`, `update_account`, `delete_account` |
| `client.session` | `SessionService` | `add_session` |
| `client.domain` | `DomainService` | `get_domains`, `add_domain`, `update_domain`, `delete_domain`, `move_domain` |
| `client.subdomain` | `SubdomainService` | `get_subdomains`, `add_subdomain`, `update_subdomain`, `delete_subdomain` |
| `client.dns` | `DnsService` | `get_dns_settings`, `add_dns_settings`, `update_dns_settings`, `delete_dns_settings` |
| `client.ddns` | `DdnsService` | `get_ddnsusers`, `add_ddnsuser`, `update_ddnsuser`, `delete_ddnsuser` |
| `client.ssl` | `SslService` | `update_ssl` |
| `client.dkim` | `DkimService` | `get_dkim`, `add_dkim`, `delete_dkim` |
| `client.mailaccount` | `MailAccountService` | `get_mailaccounts`, `add_mailaccount`, `update_mailaccount`, `delete_mailaccount` |
| `client.mailforward` | `MailForwardService` | `get_mailforwards`, `add_mailforward`, `update_mailforward`, `delete_mailforward` |
| `client.mailfilter` | `MailFilterService` | `get_mailstandardfilter`, `add_mailstandardfilter`, `delete_mailstandardfilter` |
| `client.mailinglist` | `MailingListService` | `get_mailinglists`, `add_mailinglist`, `update_mailinglist`, `delete_mailinglist` |
| `client.cronjob` | `CronjobService` | `get_cronjobs`, `add_cronjob`, `update_cronjob`, `delete_cronjob` |
| `client.database` | `DatabaseService` | `get_databases`, `add_database`, `update_database`, `delete_database` |
| `client.ftpuser` | `FtpUserService` | `get_ftpusers`, `add_ftpusers`, `update_ftpuser`, `delete_ftpuser` |
| `client.softwareinstall` | `SoftwareInstallService` | `get_softwareinstall`, `add_softwareinstall`, `delete_softwareinstall` |
| `client.statistic` | `StatisticService` | `get_space`, `get_space_usage`, `get_traffic` |
| `client.directoryprotection` | `DirectoryProtectionService` | `get_directoryprotection`, `add_directoryprotection`, `update_directoryprotection`, `delete_directoryprotection` |
| `client.sambauser` | `SambaUserService` | `get_sambausers`, `add_sambauser`, `update_sambauser`, `delete_sambauser` |
| `client.chown` | `ChownService` | `update_chown` |
| `client.symlink` | `SymlinkService` | `add_symlink`, `delete_symlink` |

## Running Tests

```bash
pytest tests/
```

The test suite runs without API credentials and covers payload construction, XML parsing (including namespace-prefixed responses), exception hierarchy, and service integration.
