param(
    [Parameter(Mandatory=$true)][string]$SessionDirectory,
    [Parameter(Mandatory=$true)][ValidateSet('admin','market','employee')][string]$Role
)
$ErrorActionPreference = 'Stop'
$resolvedDirectory = [IO.Path]::GetFullPath($SessionDirectory)
$temporaryRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
if (-not $resolvedDirectory.StartsWith($temporaryRoot, [StringComparison]::OrdinalIgnoreCase) -or
    -not ([IO.Path]::GetFileName($resolvedDirectory)).StartsWith('ai-portal-single-login-')) {
    throw 'Only an isolated single-login acceptance directory is allowed.'
}
Add-Type -AssemblyName System.Security
$protectedBytes = [IO.File]::ReadAllBytes((Join-Path $resolvedDirectory 'credentials.dpapi'))
$plainBytes = [Security.Cryptography.ProtectedData]::Unprotect($protectedBytes, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
try {
    $credentials = [Text.Encoding]::UTF8.GetString($plainBytes) | ConvertFrom-Json
    Set-Clipboard -Value $credentials.$Role.password
    Write-Output ('Temporary password copied for ' + $credentials.$Role.username + '. Paste into the local login form, then clear the clipboard.')
} finally {
    [Array]::Clear($plainBytes, 0, $plainBytes.Length)
    $credentials = $null
}
