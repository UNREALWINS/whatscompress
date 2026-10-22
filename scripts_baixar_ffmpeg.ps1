$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$bin = Join-Path $PSScriptRoot 'bin'
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$ff = Join-Path $bin 'ffmpeg.exe'
$fp = Join-Path $bin 'ffprobe.exe'

function Test-Exe([string]$exe) {
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { return $false }
    try {
        & $exe -version 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

Write-Host 'Verificando bin\ffmpeg.exe e bin\ffprobe.exe...'
if ((Test-Exe $ff) -and (Test-Exe $fp)) {
    Write-Host 'Ja estao presentes e funcionando: nenhum download necessario.' -ForegroundColor Green
    exit 0
}

Write-Host 'Falta uma ferramenta ou a copia existente esta com problema.' -ForegroundColor Yellow
Write-Host 'Baixando FFmpeg (isso so e necessario uma vez)...'
$archive = Join-Path $env:TEMP ('whatscompress_ffmpeg_' + [guid]::NewGuid().ToString('N') + '.zip')
$extract = Join-Path $env:TEMP ('whatscompress_ffmpeg_' + [guid]::NewGuid().ToString('N'))
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
    Invoke-WebRequest -Uri $url -OutFile $archive -UseBasicParsing
    Expand-Archive -LiteralPath $archive -DestinationPath $extract -Force
    $newff = Get-ChildItem -Path $extract -Recurse -Filter 'ffmpeg.exe' -File | Select-Object -First 1
    $newfp = Get-ChildItem -Path $extract -Recurse -Filter 'ffprobe.exe' -File | Select-Object -First 1
    if (-not $newff -or -not $newfp) { throw 'Executaveis ffmpeg.exe/ffprobe.exe nao encontrados dentro do ZIP.' }
    if (-not (Test-Exe $ff)) { Copy-Item -LiteralPath $newff.FullName -Destination $ff -Force }
    if (-not (Test-Exe $fp)) { Copy-Item -LiteralPath $newfp.FullName -Destination $fp -Force }
    if (-not ((Test-Exe $ff) -and (Test-Exe $fp))) { throw 'FFmpeg nao passou no teste de execucao.' }
    Write-Host 'FFmpeg e FFprobe prontos!' -ForegroundColor Green
    exit 0
} catch {
    Write-Host ('Falha: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
} finally {
    Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $extract -Recurse -Force -ErrorAction SilentlyContinue
}
