$ErrorActionPreference = "Continue"
$root = (Get-Location).Path
Write-Host "=== ПРОВЕРКА ПАПКИ: $root ===" -ForegroundColor Cyan

$mustHave = @("tgbot1.py", ".env", "requirements.txt", "collect_parts.ps1")

Write-Host "`n--- Обязательные файлы ---" -ForegroundColor Yellow
foreach ($f in $mustHave) {
    if (Test-Path $f) {
        $sz = (Get-Item $f).Length
        Write-Host ("  OK  {0,-25} {1,10} байт" -f $f, $sz) -ForegroundColor Green
    } else {
        Write-Host ("  НЕТ {0,-25} ОТСУТСТВУЕТ" -f $f) -ForegroundColor Red
    }
}

Write-Host "`n--- Python-файлы в корне ---" -ForegroundColor Yellow
Get-ChildItem -Filter *.py -File | ForEach-Object {
    Write-Host ("  - {0,-30} {1,8} байт" -f $_.Name, $_.Length)
}

Write-Host "`n--- .env: ключи (значения скрыты) ---" -ForegroundColor Yellow
if (Test-Path ".env") {
    Get-Content ".env" | Where-Object { $_ -match "^\s*[^#\s].*=" } | ForEach-Object {
        $k = ($_ -split "=",2)[0].Trim()
        Write-Host "  - $k"
    }
} else {
    Write-Host "  нет .env" -ForegroundColor Red
}

Write-Host "`n--- Git ---" -ForegroundColor Yellow
if (Test-Path ".git") {
    git status --short 2>$null
    Write-Host "--- последние коммиты ---"
    git log --oneline -3 2>$null
} else {
    Write-Host "  (нет .git)"
}

Write-Host "`n--- requirements.txt ---" -ForegroundColor Yellow
if (Test-Path "requirements.txt") { Get-Content "requirements.txt" }
else { Write-Host "  нет requirements.txt" -ForegroundColor DarkYellow }

Write-Host "`n=== КОНЕЦ ПРОВЕРКИ ===" -ForegroundColor Cyan
