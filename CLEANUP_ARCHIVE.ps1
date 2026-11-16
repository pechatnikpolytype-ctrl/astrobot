param(
    [switch]$WhatIf
)
$ErrorActionPreference = "Stop"
$root = (Get-Location).Path
$archiveRoot = Join-Path $root "_archive"
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm"
$archiveDir = Join-Path $archiveRoot $stamp

# 1. Кандидаты по маскам (только файлы в корне и папка FixAstro целиком)
$patterns = @(
    "fix_*.py", "big_fix.py", "check_*.py", "diag*.py",
    "test_*.py", "split_dump.py", "collect_project.py",
    "find_ai_lines.py", "*.bak_*", "dump_*.txt"
)
$candidates = @()
foreach ($p in $patterns) {
    $candidates += Get-ChildItem -Path $root -Filter $p -File -ErrorAction SilentlyContinue
}
# FixAstro целиком (папка)
if (Test-Path (Join-Path $root "FixAstro")) {
    $candidates += Get-Item (Join-Path $root "FixAstro")
}
# Уникализируем по FullName
$candidates = $candidates | Sort-Object FullName -Unique

# 2. Собираем все .py проекта для грепа (исключая .venv, __pycache__, .git, _archive)
$allPy = Get-ChildItem -Path $root -Filter *.py -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\\.venv\\|\\__pycache__\\|\\\.git\\|\\_archive\\' }

# 3. Для каждого .py-кандидата проверяем, импортируется ли он где-то
function Test-IsImported {
    param([string]$fileName)
    $base = [System.IO.Path]::GetFileNameWithoutExtension($fileName)
    $pattern = "\b(import\s+$([regex]::Escape($base))\b|from\s+$([regex]::Escape($base))\b)"
    foreach ($py in $allPy) {
        if ($py.FullName -eq (Join-Path $root $fileName)) { continue }
        $hit = Select-String -Path $py.FullName -Pattern $pattern -Quiet -ErrorAction SilentlyContinue
        if ($hit) { return $py.FullName }
    }
    return $null
}

# 4. Разделяем на "безопасно убрать" и "пропущено"
$toMove = @()
$skipped = @()
foreach ($c in $candidates) {
    if ($c.PSIsContainer) {
        # Папка FixAstro — не содержит .py, которые импортируются? Проверим по имени
        $toMove += $c
        continue
    }
    if ($c.Extension -eq ".py") {
        $importer = Test-IsImported -fileName $c.Name
        if ($importer) {
            $skipped += [pscustomobject]@{ File = $c.FullName; Importer = $importer }
        } else {
            $toMove += $c
        }
    } else {
        # Не .py (bak, txt) — не импортируются, двигаем
        $toMove += $c
    }
}

# 5. Вывод
Write-Host "`n=== КАНДИДАТЫ НА ПЕРЕМЕЩЕНИЕ ===" -ForegroundColor Cyan
$toMove | ForEach-Object {
    $rel = $_.FullName.Substring($root.Length).TrimStart('\')
    Write-Host ("  + {0}" -f $rel) -ForegroundColor Green
}
Write-Host "`nИтого к перемещению: $($toMove.Count)" -ForegroundColor Yellow

if ($skipped.Count -gt 0) {
    Write-Host "`n=== ПРОПУЩЕНО (импортируется где-то) ===" -ForegroundColor DarkYellow
    $skipped | ForEach-Object {
        $rel = $_.File.Substring($root.Length).TrimStart('\')
        $impRel = $_.Importer.Substring($root.Length).TrimStart('\')
        Write-Host ("  ! {0}  <-- импортируется из {1}" -f $rel, $impRel) -ForegroundColor DarkYellow
    }
}

if ($WhatIf) {
    Write-Host "`n[WhatIf] Перемещение НЕ выполнено. Запусти без -WhatIf, чтобы применить." -ForegroundColor Magenta
    return
}

if ($toMove.Count -eq 0) {
    Write-Host "`nНечего перемещать." -ForegroundColor Green
    return
}

# 6. Реальное перемещение
New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
Write-Host "`nПеремещаю в: $archiveDir" -ForegroundColor Cyan
$moved = 0
foreach ($item in $toMove) {
    $rel = $item.FullName.Substring($root.Length).TrimStart('\')
    $dest = Join-Path $archiveDir $rel
    $destDir = Split-Path $dest -Parent
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    try {
        Move-Item -Path $item.FullName -Destination $dest -Force
        $moved++
    } catch {
        Write-Host ("  ОШИБКА: {0} -- {1}" -f $rel, $_.Exception.Message) -ForegroundColor Red
    }
}
Write-Host "`nПеремещено: $moved из $($toMove.Count)" -ForegroundColor Green
Write-Host "Архив: $archiveDir" -ForegroundColor Cyan
Write-Host "`nВернуть обратно можно так:" -ForegroundColor Yellow
Write-Host ("  Move-Item '{0}\*' '{1}'" -f $archiveDir, $root) -ForegroundColor DarkGray
