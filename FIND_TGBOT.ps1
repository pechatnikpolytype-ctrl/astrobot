$ErrorActionPreference = "Continue"
$root = (Get-Location).Path
Write-Host "=== ПОИСК tgbot1.py и родственных файлов ===" -ForegroundColor Cyan

$patterns = @("tgbot1.py","admin.py","database.py","keyboards.py","handlers.py","main.py","bot.py")
$searchRoots = @(
    "$env:USERPROFILE\Desktop",
    "$env:USERPROFILE\source",
    "$env:USERPROFILE\Downloads",
    "$env:USERPROFILE\Documents"
) | Where-Object { Test-Path $_ }

foreach ($file in $patterns) {
    Write-Host "`n--- Ищу: $file ---" -ForegroundColor Yellow
    $found = $false
    foreach ($r in $searchRoots) {
        $hits = Get-ChildItem -Path $r -Filter $file -Recurse -File -ErrorAction SilentlyContinue |
                Select-Object -First 20
        foreach ($h in $hits) {
            $found = $true
            Write-Host ("  {0,-20} {1,8} байт  {2}" -f $h.Name, $h.Length, $h.FullName) -ForegroundColor Green
        }
    }
    if (-not $found) { Write-Host "  не найден в: $($searchRoots -join ', ')" -ForegroundColor Red }
}

Write-Host "`n--- Все .py рекурсивно по Desktop (верхние 50, сортировка по размеру) ---" -ForegroundColor Yellow
Get-ChildItem -Path "$env:USERPROFILE\Desktop" -Filter *.py -Recurse -File -ErrorAction SilentlyContinue |
    Sort-Object Length -Descending | Select-Object -First 50 |
    ForEach-Object { Write-Host ("  {0,10} байт  {1}" -f $_.Length, $_.FullName) }

Write-Host "`n=== КОНЕЦ ПОИСКА ===" -ForegroundColor Cyan
