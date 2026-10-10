# Reassemble and verify the clean OMI 3.10 distribution. No network access.
$ErrorActionPreference = 'Stop'
function Get-Sha256([string] $FilePath) {
    $engine = [System.Security.Cryptography.SHA256]::Create()
    $inputStream = [System.IO.File]::OpenRead($FilePath)
    try { return [System.BitConverter]::ToString($engine.ComputeHash($inputStream)).Replace('-', '').ToLowerInvariant() }
    finally { $inputStream.Dispose(); $engine.Dispose() }
}
$parts = @(
    @{ Name = 'OMI_Bitrix_3.10_Clean_2026-10-10.zip.001'; Sha256 = '9b3a137c951d8c62dcbd8b492de19669c7bb2674ff37fec1b3ca27dbbc17ab72'; Bytes = 1200000000 }
    @{ Name = 'OMI_Bitrix_3.10_Clean_2026-10-10.zip.002'; Sha256 = '7f5fbc3ae7d69bee335b81e51bddde5a49b570229b6748297577a097d366b75f'; Bytes = 968482049 }
)
$archiveName = 'OMI_Bitrix_3.10_Clean_2026-10-10.zip'
$expectedArchiveHash = '8e97f2653b0d879e7f287dc9725e37b43e566c6dd18048d00b5c3f4fc2c26df0'
$target = Join-Path $PSScriptRoot $archiveName
if (Test-Path -LiteralPath $target) {
    if ((Get-Sha256 $target) -eq $expectedArchiveHash) {
        Write-Host 'The complete ZIP already exists and its SHA-256 is correct.'
        exit 0
    }
    throw 'An existing ZIP has a different checksum. Move it elsewhere before joining; it will not be overwritten.'
}
foreach ($part in $parts) {
    $partPath = Join-Path $PSScriptRoot $part.Name
    if (-not (Test-Path -LiteralPath $partPath -PathType Leaf)) { throw ('Missing release part: ' + $part.Name) }
    if ((Get-Item -LiteralPath $partPath).Length -ne $part.Bytes) { throw ('Incorrect size: ' + $part.Name) }
    Write-Host ('Verifying ' + $part.Name)
    if ((Get-Sha256 $partPath) -ne $part.Sha256) { throw ('Checksum mismatch: ' + $part.Name) }
}
$temporary = $target + '.assembling'
if (Test-Path -LiteralPath $temporary) { throw 'A previous .assembling file exists. Move it elsewhere before retrying.' }
$outputStream = [System.IO.File]::Open($temporary, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write)
try {
    $buffer = New-Object byte[] (4 * 1024 * 1024)
    foreach ($part in $parts) {
        $inputStream = [System.IO.File]::OpenRead((Join-Path $PSScriptRoot $part.Name))
        try {
            while (($count = $inputStream.Read($buffer, 0, $buffer.Length)) -gt 0) { $outputStream.Write($buffer, 0, $count) }
        } finally { $inputStream.Dispose() }
    }
} finally { $outputStream.Dispose() }
Write-Host 'Verifying the complete ZIP...'
if ((Get-Sha256 $temporary) -ne $expectedArchiveHash) { throw 'Complete archive checksum mismatch; the .assembling file is retained for inspection.' }
[System.IO.File]::Move($temporary, $target)
Write-Host ('Ready: ' + $target)
Write-Host 'Extract the ZIP, then run OMI_Bitrix\start.bat with Python 3.14 x64 installed.'
